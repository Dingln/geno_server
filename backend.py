import json
import os
import pickle
import psutil
import requests
import shutil
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS
from fileio import *

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
        self.models = {}  # Empty, lazy load pre-existing models in get_model
        
        # Cache components between pipelines (where possible)
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
            model.interpreter = Interpreter.load(model.dev_model_dir, self.builder)
        
        self.models[dev_id] = model
        return model


class Model:
    def __init__(self, dev_id):
        self.dev_id = dev_id
        self.dev_data_dir = "devep_data/dev_{}".format(self.dev_id)
        self.dev_model_dir = "devep_model/dev_{}".format(self.dev_id)
        self.training_data = None
        self.interpreter = None

    def train(self, training_data):
        # Store new training data into file (TODO: use rasa function?)
        write_file(training_data,
                   "devep_data/dev_{}/nlu.md".format(self.dev_id))

        # Train Rasa model
        self.training_data = load_data(self.dev_data_dir)
        trainer = Trainer(config.load(RASA_CONFIG_FILE), global_manager.builder)
        self.interpreter = trainer.train(self.training_data)
        model_directory = trainer.persist(self.dev_model_dir, fixed_model_name=os.path.basename(self.dev_model_dir))

        return self.training_data.nlu_as_json()
    
    def parse(self, query):
        if self.interpreter:
            return self.interpreter.parse(query)
        return {}


class Entity:
    queries = []


class Data:
    def __init__(self, intent, queries):
        self.intent = intent
        self.queries = queries

        # Format intent and queries into Rasa training data
        self.training_data = "## intent:{}\n".format(self.intent)
        self.training_data += '\n'.join(
            map(lambda q: " - {}".format(q), self.queries))

#### Flask Server ####

app = Flask("Geno")
CORS(app)
global_manager = Manager(DEV_LIST_FILE)


@app.route('/train', methods=['POST'])
def train():
    dev_id, intent, queries = int(request.json['dev_id']), request.json['intent'], request.json['queries']

    geno_data = Data(intent, queries)
    geno_model = global_manager.get_model(dev_id)
    return geno_model.train(geno_data.training_data)


@app.route('/response', methods=['GET'])
def response():
    dev_id, query = int(request.args['dev_id']), request.args['query']
    model = global_manager.get_model(dev_id)
    return model.parse(query)


if __name__ == '__main__':
    app.run(port=3001, debug=False)
