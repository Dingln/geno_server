import json
import os
import pickle
import psutil
import requests
import shutil
import sys

from contextlib import contextmanager
from flask import Flask, Response, request, abort, jsonify, g
from flask_cors import CORS

from rasa.nlu.training_data import load_data
from rasa.nlu.components import ComponentBuilder
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.model import Interpreter, Trainer
from rasa.nlu import config

DEV_LIST_FILE = "devep_data/dev_list"
RASA_CONFIG_FILE = "config/config.yml"

from functools import wraps

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
        # ners = pretrained_entities.run_spacy(query)

        if self.interpreter:
            res = self.interpreter.parse(query)
            # res['entities'] = ners
            for ent in res['entities']:
                if multiple_mode.check_words(ent['value']) == False:
                    res['entities'].remove(ent)
                if ent['value'] == 'None':
                    start = ent['start']
                    end = ent['end']
                    ent['value'] = query[start:end]
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

    def update_query(self, intent, old_text, new_query):
        with self.common_examples() as examples:
            return_query = None
            for (i, example) in enumerate(examples):
                if example['intent'] == intent and example['text'] == old_text:
                    examples[i]['text'] = new_query['text']
                    examples[i]['entities'] = pretrained_entities.self_choose_single(new_query)
                    return_query = example
                    break
            return return_query 

    def delete_query(self, intent, query):
       with self.common_examples() as examples:
           examples[:] = [x for x in examples if x['intent'] != intent or x['text'] != query]
           return examples


class EntityRecognition:
    ner_spacy = None

    def __init__(self, use_spacy=True):
        if use_spacy:
            self.ner_spacy = spacy.load("en")
        else:
            self.ner_spacy = None
        pass
    
    def run_spacy(self, query):
        if self.ner_spacy == None:
            print('Spacy should be set to USE')
            return
        ner_doc = self.ner_spacy(query)
        ners = []
        for ent in ner_doc.ents:
            ent_dict = {
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'entity': ent.label_
            }
            ners.append(ent_dict)
        return ners

    def self_choose(self, query, parameters):
        ners = []
        for para in parameters:
            ent_dict = {
                'text': query[para['start']:para['end']+1],
                'start': para['start'],
                'end': para['end'],
                'entity': para['label']
            }
            ners.append(ent_dict)
        return ners

    def self_choose_single(self, query):
        ners = []
        pre_entity = None
        for entity in query['entities'].values():
            if entity['label'] is not None:
                if pre_entity != None and entity['label'] == pre_entity['entity']:
                    print(pre_entity)
                    pre_entity['end'] = entity['end']
                    pre_entity['text'] = query['text'][pre_entity['start']:pre_entity['end']]
                else:
                    entity['entity'] = entity.pop('label')
                    ners.append(entity)
                    pre_entity = entity
        # for para in parameters:
        #     ent_dict = {
        #         'text': query[para['start']:para['end']],
        #         'start': para['start'],
        #         'end': para['end'],
        #         'entity': para['label']
        #     }
        #     ners.append(ent_dict)
        return ners


class Data:
    def __init__(self, intent, queries, parameters):
        self.intent = intent
        self.queries = queries
        self.parameters = parameters

        # Format intent and queries into Rasa training data
        self.queries = map(lambda q: q['text'], queries)
        self.training_data = [{"intent": intent, "text": queries[i]['text'], "entities": pretrained_entities.self_choose_single(queries[i])}
                              for i in range(len(queries))] 
        # self.training_data = [{"intent": intent, "text": query, "entities": pretrained_entities.run_spacy(query)}
                            #   for query in queries] 
        # self.training_data = [{"intent": intent, "text": query, "entities": []}
        #                       for query in queries] 
        # Assign parameters to label of entities
        # if self.parameters:
        #     for item in self.training_data:
        #         min_len = min(len(self.parameters), len(item['entities']))
        #         for idx in range(min_len):
        #             item['entities'][idx]['entity'] = self.parameters[idx]


class Multimodal:
    activation_words = None
    def __init__(self):
        self.activation_words = ['this', 'that', 'here', 'there']
    
    def check_words(self, entity):
        for word in self.activation_words:
            if word in entity:
                return False
        return True

            


#### Flask Server ####


app = Flask("Geno")
CORS(app)
global_manager = Manager(DEV_LIST_FILE)
pretrained_entities = EntityRecognition(use_spacy=False)
multiple_mode = Multimodal()


def validate_params(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'GET':
            params = request.args
        elif request.method == 'POST':
            params = request.json

        message = None
        status = 200

        # Validate dev_id
        dev_id = params['dev_id']
        if dev_id == "":
            message = "Please configure your unique developer ID in the settings."
            status = 400
        elif not dev_id.isnumeric():
            message = "Developer ID must be a number."
            status = 400
        else:
            g.dev_id = int(dev_id)
            g.model = global_manager.get_model(g.dev_id)
        
        # Abort if error was found
        if status != 200:
            print(message)
            abort(Response(message, status=status))
        else:
            return f(*args, **kwargs)
    
    return decorated


@app.route('/intent/train', methods=['POST'])
@validate_params
def train():
    intent, queries, parameters = request.json['intent'], request.json['queries'], request.json['parameters']
    geno_data = Data(intent, queries, parameters)
    return g.model.train(geno_data.training_data)


@app.route('/intent/delete', methods=['POST'])
@validate_params
def delete_intent():
    intent = request.json['intent']
    return jsonify(g.model.delete_intent(intent))


@app.route('/response', methods=['GET'])
@validate_params
def response():
    query = request.args['query']
    return g.model.parse(query)


@app.route('/query/update', methods=['POST'])
@validate_params
def update_query():
    intent, old_text, new_query = request.json['intent'], request.json['old_text'], request.json['new_query']
    return jsonify(g.model.update_query(intent, old_text, new_query))


@app.route('/query/delete', methods=['POST'])
@validate_params
def delete_query():
    intent, query = request.json['intent'], request.json['query']
    return jsonify(g.model.delete_query(intent, query))


if __name__ == '__main__':
    app.run(port=3313, debug=False, threaded=True)
