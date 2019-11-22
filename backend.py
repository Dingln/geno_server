import json
import os
import psutil
import requests
import shutil
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS
from fileio import *

from rasa.nlu.training_data import load_data
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.model import Trainer
from rasa.nlu import config

DEV_LIST_FILE = "devep_data/dev_list.txt"
PORT_LIST_FILE = "devep_data/port_list.txt"
PID_LIST_FILE = "devep_data/pid_list.txt"


class Manager:
    def __init__(self, dev_file, port_file, pid_file):
        self.dev_dict, self.dev_list, self.port_list = load_dev_port(dev_file, port_file)
        self.pid_list = load_list(pid_file)

    def dev_id_exists(self, dev_id):
        return dev_id in self.dev_list


class Model:
    cur_pid = -1
    dev_id = -1
    training_data = "\0"
    is_exist = False
    dev_data_dir = "\0"
    dev_model_dir = "\0"
    new_port = -1

    def __init__(self):
        self.cur_pid = os.getpid()

    def load_dev_data(self, trans_id, trans_training_data):
        self.dev_id = trans_id
        self.training_data = trans_training_data

    def set_dev_dir(self):
        self.dev_data_dir = "devep_data/dev_{}".format(self.dev_id)
        self.dev_model_dir = "devep_model/dev_{}".format(self.dev_id)

    def create_update_model_data(self, manager):
        if not self.is_exist:
            if os.path.exists(self.dev_model_dir):
                shutil.rmtree(self.dev_model_dir)

            if not os.path.exists(self.dev_data_dir):
                os.makedirs(self.dev_data_dir)

            write_file(self.dev_id, DEV_LIST_FILE)

            if len(manager.port_list) == 0:
                self.new_port = 5005
            else:
                self.new_port = max(manager.port_list) + 1

            write_file(self.new_port, PORT_LIST_FILE)
            write_file(self.cur_pid, PID_LIST_FILE)
        else:
            self.new_port = manager.dev_dict[self.dev_id]
            pid_index = manager.dev_list.index(self.dev_id)
            old_pid = manager.pid_list[pid_index]
            psutil.Process(old_pid).kill()
            kill_port(self.new_port)
            manager.pid_list[pid_index] = self.cur_pid
            update_pid(manager.pid_list, PID_LIST_FILE)

        write_file(self.training_data,
                   "devep_data/dev_{}/nlu.md".format(self.dev_id))

    def train_run_model(self, trans_id, trans_training_data, manager):
        self.load_dev_data(trans_id, trans_training_data)
        self.set_dev_dir()
        self.create_update_model_data(manager)

        # Train Rasa Model
        training_data = load_data(self.dev_data_dir)
        trainer = Trainer(config.load("config.yml"))
        self.interpreter = trainer.train(training_data)
        model_directory = trainer.persist("./models/nlu", fixed_model_name=self.dev_model_dir)
        # TODO: catch error: "Can not train a classifier. Need at least 2 different classes. Skipping training of classifier.""


class Entity:
    queries = []


class Data:
    def __init__(self, intent, queries):
        self.intent = intent
        self.queries = queries
        self.create_data()

    def create_data(self):
        self.training_data = "## intent:{}\n".format(self.intent)
        print(self.queries)
        self.training_data += '\n'.join(map(lambda q: " - {}".format(q), self.queries))


app = Flask("Geno")
CORS(app)
global_manager = Manager("devep_data/dev_list.txt", "devep_data/port_list.txt", "devep_data/pid_list.txt")
geno_model = Model()


@app.route('/train', methods=['POST'])
def train():
    geno_data = Data(request.json['intent'], request.json['queries'])
    geno_model.is_exist = global_manager.dev_id_exists(geno_model.dev_id)
    geno_model.train_run_model(request.json['dev_id'], geno_data.training_data, global_manager)

    result = {'entities': geno_model.training_data}
    return jsonify(result)


@app.route('/response',  methods=['GET'])
def response():
    return geno_model.interpreter.parse(request.args['query'])


if __name__ == '__main__':
    app.run(port=3001, debug=False)

