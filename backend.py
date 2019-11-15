import sys
import os
import shutil
import psutil
from flask import Flask, request, jsonify
import json
from foo_IO import *
import requests



class Manager:
    dev_list = []
    pid_list = []
    port_list = []
    dev_dict = dict()

    def __init__(self, dev_file, port_file, pid_file):
        self.dev_dict, self.dev_list, self.port_list = load_dev_port(dev_file, port_file)
        self.pid_list = load_pidList(pid_file)

    def check_dev_id_is_exist(self, dev_id):
        for cur_id in self.dev_list:
            if int(cur_id) == dev_id:
                return True
        return False


class Model:
    cur_pid = -1
    dev_id = -1
    training_data = "\0"
    is_exist = False
    dev_data_dir = "\0"
    dev_model_dir = "\0"
    newport = -1

    def __init__(self):
        self.cur_pid = os.getpid()

    def load_dev_data(self, trans_id, trans_training_data):
        self.dev_id = trans_id
        self.training_data = trans_training_data

    def set_dev_dir(self):
        self.dev_data_dir = "devep_data/dev_" + self.dev_id
        self.dev_model_dir = "devep_model/dev_" + self.dev_id

    def create_update_model_data(self, manager):
        if not self.is_exist:
            if os.path.exists(self.dev_model_dir):
                shutil.rmtree(self.dev_model_dir)
            if not os.path.exists(self.dev_data_dir):
                os.mkdir(self.dev_data_dir)
                os.popen("cp data/stories.md " + self.dev_data_dir + "/stories.md")
                os.popen("cp data/nlu.md " + self.dev_data_dir + "/nlu.md")
            write_file(self.dev_id, "devep_data/dev_list.txt")
            if len(manager.port_list) == 0:
                self.newport = "5005"
            else:
                self.newport = str(int(max(manager.port_list)) + 1)
            write_port(self.newport, "devep_data/port_list.txt")
            write_pid(self.cur_pid, "devep_data/pid_list.txt")
        else:
            self.newport = manager.dev_dict[self.dev_id]
            pid_index = manager.dev_list.index(self.dev_id)
            old_pid = manager.pid_list[pid_index]
            os.popen("kill -9 " + str(old_pid))
            kill_port(self.newport)
            manager.pid_list[pid_index] = self.cur_pid
            update_pid(manager.pid_list, "devep_data/pid_list.txt")
        write_file(self.training_data, "devep_data/dev_" + self.dev_id + "/nlu.md")

    def train_run_model(self, trans_id, trans_training_data, manager):
        self.load_dev_data(trans_id, trans_training_data)
        self.set_dev_dir()
        self.create_update_model_data(manager)
        train_cmd = "cd ~/geno; /Library/Frameworks/Python.framework/Versions/3.6/bin/rasa train --data " + self.dev_data_dir + " --out " + self.dev_model_dir
        train_cmd_resp = os.popen(train_cmd)
        print(train_cmd)
        for tmp in train_cmd_resp.readlines():
            print(tmp)
        run_cmd = "cd ~/geno; /Library/Frameworks/Python.framework/Versions/3.6/bin/rasa run --enable-api -p " + self.newport + " -m " + self.dev_model_dir
        run_cmd_resp = os.popen(run_cmd)
        print(run_cmd)
        for tmp in run_cmd_resp.readlines():
            print(tmp)


class Entity:
    queries = []


class Data:
    intent = ""
    queries = ""
    training_data = ""

    def create_data(self):
        self.training_data = "## intent:" + self.intent
        # for query in self.queries:
        #     self.training_data = self.training_data + "\n - " + query
        self.training_data = self.training_data + "\n - " + self.queries

app = Flask("Geno")
global_manager = Manager("devep_data/dev_list.txt", "devep_data/port_list.txt", "devep_data/pid_list.txt")
geno_model = Model()
geno_data = Data()


@app.route('/train', methods=['POST'])
def train():
    geno_data.intent = request.json['intent']
    geno_data.queries = request.json['queries']
    geno_data.create_data()
    geno_model.is_exist = global_manager.check_dev_id_is_exist(geno_model.dev_id)
    geno_model.train_run_model(request.json['dev_id'], geno_data.training_data, global_manager)

    result = {'entities': geno_model.training_data}
    return jsonify(result)


@app.route('/response',  methods=['GET'])
def response():
    post_url = "http://localhost:" + "5016" + "/model/parse"
    data = json.dumps(dict(text="Hi"))
    resp = requests.post(post_url, data)
    # return "Hi Developer " + geno_model.dev_id
    return resp.content


if __name__ == '__main__':
    app.run(port=3000, debug=False)

