import json
import os
import pickle
import psutil
import requests
import shutil
import sys
import spacy

from contextlib import contextmanager
from flask import Flask, request, jsonify
from flask_cors import CORS

from rasa.nlu.training_data import load_data
from rasa.nlu.components import ComponentBuilder
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.model import Interpreter, Trainer
from rasa.nlu import config

DEV_LIST_FILE = "devep_data/dev_list"
RASA_CONFIG_FILE = "config/config.yml"


class Manager:
    def __init__(self, dev_file):
        self.dev_file = dev_file
        self.devs = self.load_devs()
        self.models = {}  # Lazy load pre-existing models in get_model
        # Cache components between pipelines
        self.builder = ComponentBuilder(use_cache=True)

    def load_devs(self):
        try:
            with open(self.dev_file, 'rb') as f:
                return set(pickle.load(f))
        except FileNotFoundError:
            return set()

    def save_devs(self):
        with open(self.dev_file, 'wb') as f:
            pickle.dump(self.devs, f)

    def add_dev(self, dev_id):
        self.devs.add(dev_id)
        self.save_devs()

    def dev_exists(self, dev_id):
        return dev_id in self.devs

    # Returns stored model if it exists, else creates a new one
    def get_model(self, dev_id):
        if dev_id in self.models:
            print("Found model in memory")
            return self.models[dev_id]

        model = Model(dev_id)

        if not self.dev_exists(dev_id):
            print("Creating new model")
            if os.path.exists(model.dev_model_dir):
                shutil.rmtree(model.dev_model_dir)

            if not os.path.exists(model.dev_data_dir):
                os.makedirs(model.dev_data_dir)

            self.add_dev(dev_id)
        else:
            print("Found model on disk")
            model.interpreter = Interpreter.load(
                model.dev_model_dir, self.builder)

        self.models[dev_id] = model
        return model


class Model:
    def __init__(self, dev_id):
        self.dev_id = dev_id
        self.dev_data_dir = "devep_data/dev_{}".format(self.dev_id)
        self.dev_model_dir = "devep_model/dev_{}".format(self.dev_id)
        self.dev_train_file = "devep_data/dev_{}/nlu.json".format(self.dev_id)
        self.training_data = None
        self.interpreter = None

    def train(self, common_examples):
        # Store new training data into file
        self.update_data(common_examples)

        # Train Rasa model
        self.training_data = load_data(self.dev_data_dir)
        trainer = Trainer(config.load(RASA_CONFIG_FILE),
                          global_manager.builder)
        self.interpreter = trainer.train(self.training_data)
        model_directory = trainer.persist("devep_model", fixed_model_name=os.path.basename(self.dev_model_dir))

        return self.training_data.nlu_as_json()

    def parse(self, query):
        # Do entity Recognition using Spacy
        ner_doc = ner_spacy(query)
        ners = []
        for ent in ner_doc.ents:
            ent_dict = {
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'label': ent.label_
            }
            ners.append(ent_dict)

        if self.interpreter:
            res = self.interpreter.parse(query)
            res['entities'] = ners
            return res
        return {}

    @contextmanager
    def common_examples(self, default=[]):
        data = {}
        try:
            with open(self.dev_train_file, 'r+') as f:
                data = json.load(f)
                examples = data['rasa_nlu_data']['common_examples']
                yield examples

            data['rasa_nlu_data']['common_examples'] = examples
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "rasa_nlu_data": {
                    "common_examples": default,
                    "regex_features": [],
                    "lookup_tables": [],
                    "entity_synonyms": []
                }
            }
            yield default
        finally:
            with open(self.dev_train_file, 'w+') as f:
                json.dump(data, f)

    def update_data(self, new_examples):
        # FIXME: Searching for duplicates is inefficient
        with self.common_examples(new_examples) as examples:
            for ex in new_examples:
                if ex not in examples:
                    examples.append(ex)

            return examples

    def delete_intent(self, intent):
        with self.common_examples() as examples:
            examples[:] = [x for x in examples if x['intent'] != intent]
            self.train(examples) # Retrain model to remove intent
            return examples

    def update_query(self, intent, old_query, new_query):
        with self.common_examples() as examples:
            return_query = None
            for (i, example) in enumerate(examples):
                if example['intent'] == intent and example['text'] == old_query:
                    examples[i]['text'] = new_query
                    return_query = example
                    break

            # TODO: analyze query entities
            if return_query:
                return_query['entities'] = []

            return return_query 

    def delete_query(self, intent, query):
       with self.common_examples() as examples:
           examples[:] = [x for x in examples if x['intent'] != intent or x['text'] != query]
           return examples


class Entity:
    queries = []


class Data:
    def __init__(self, intent, queries):
        self.intent = intent
        self.queries = queries

        # Format intent and queries into Rasa training data
        self.training_data = [{"intent": intent, "text": query}
                              for query in queries]

#### Flask Server ####


app = Flask("Geno")
CORS(app)
global_manager = Manager(DEV_LIST_FILE)


@app.route('/intent/train', methods=['POST'])
def train():
    dev_id, intent, queries = int(
        request.json['dev_id']), request.json['intent'], request.json['queries']

    geno_data = Data(intent, queries)
    geno_model = global_manager.get_model(dev_id)
    return geno_model.train(geno_data.training_data)


@app.route('/intent/delete', methods=['POST'])
def delete_intent():
    dev_id, intent = int(request.json['dev_id']), request.json['intent']
    model = global_manager.get_model(dev_id)
    return jsonify(model.delete_intent(intent))


@app.route('/response', methods=['GET'])
def response():
    dev_id, query = int(request.args['dev_id']), request.args['query']
    model = global_manager.get_model(dev_id)
    return model.parse(query)


@app.route('/query/update', methods=['POST'])
def update_query():
    dev_id, intent, old_query, new_query = int(
        request.json['dev_id']), request.json['intent'], request.json['old_query'], request.json['new_query']
    model = global_manager.get_model(dev_id)
    return jsonify(model.update_query(intent, old_query, new_query))


@app.route('/query/delete', methods=['POST'])
def delete_query():
    dev_id, intent, query = int(
        request.json['dev_id']), request.json['intent'], request.json['query']
    model = global_manager.get_model(dev_id)
    return jsonify(model.delete_query(intent, query))


if __name__ == '__main__':
    ner_spacy = spacy.load("en")
    app.run(port=3001, debug=False, threaded=True)
