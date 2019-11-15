from flask import Flask, request, jsonify

app = Flask("Geno")


class ShareData:
    dev_id = -1
    training_data = "\0"

    def set_members(self, id, data):
        self.dev_id = id
        self.training_data = data

    def get_members(self):
        return self.dev_id, self.training_data


geno_data = ShareData()


@app.route('/train', methods=['POST'])
def train():
    dev_id = request.json['dev_id']
    training_data = request.json['training_data']
    geno_data.set_members(dev_id, training_data)
    result = {'entities': training_data}
    return jsonify(result)


@app.route('/')
def train():

    return ""


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)