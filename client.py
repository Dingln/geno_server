import pprint
import requests
import sys


def train(*data):
    res = []
    for json in data:
        res.append(requests.post("http://127.0.0.1:3001/intent/train", json=json).json())
       
    return res

def response(dev_id, query):
    payload = {'dev_id': dev_id, 'query': query}
    res = requests.get("http://127.0.0.1:3001/response", params=payload)
    return res.json()


def update(*data):
    res = []
    for json in data:
        res.append(requests.post("http://127.0.0.1:3001/query/update", json=json).json())
    return res

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 client.py [train/response]")
        exit()

    endpoint = sys.argv[1]
    dev_id = int(sys.argv[2])

    if endpoint == "train":
        if dev_id == 1:
            print(train({
                    'dev_id': 1,
                    'intent': "multiply_numbers",
                    'parameters': {},
                    'queries': ["what is the product of two and four", "multiply six and ten", "product of fourteen and twelve", "whats the product of thirty and eleven", "how much is six times ten"]
                },
                {
                    'dev_id': 1,
                    'intent': "check_balance",
                    'parameters': ["account"],
                    'queries': ["how much money is in my checking account", "what is the balance of my checking account", "how much money in my savings account", "what is the balance of my savings account"]
                }
            ))
        elif dev_id == 2:
            print(train(
                # {
                #     'dev_id': 2,
                #     'intent': "introduction",
                #     'parameters': [[], [], [], []],
                #     'queries': ["hi my name is Joe", "hello I'm Bob", "hi i'm John", "hey my name is Andrew"]
                # },
                # {
                #     'dev_id': 2,
                #     'intent': "check_weather",
                #     'parameters': [ 'location 1', 'location 2'
                #                 # [{'start': 23, 'end': 28, 'label': "location1"}, {'start': 33, 'end': 41, 'label': "location2"}],
                #                 # [{'label': "location1", 'start': 26, 'end': 32}]
                #                 ], 
                #     'queries': ["what is the weather in Tokyo and Shanghai", "whats the weather like in London"]
                # },
                {
                    'dev_id': 2,
                    'intent': "change_color",
                    'parameters': [ 'color'
                                # [{'start': 16, 'end': 19, 'label': "color"}],
                                # [{'label': "color", 'start': 21, 'end': 25}]
                                ], 
                    'queries': [
                        {   'text': "Change color to blue",
                            'entities': {
                                '0': { 'label': None, 'text': "Change", 'start': 0, 'end': 6 }, 
                                '7': { 'label': None, 'text': "color", 'start': 7, 'end': 12 }, 
                                '13': { 'label': "color", 'text': "to", 'start': 13, 'end': 15 }, 
                                '16': { 'label': "color", 'text': "blue", 'start': 16, 'end': 20 }, 
                            },
                            'id': 2
                        },
                        {   'text': "Change text color to red",
                            'entities': {
                                '0': { 'label': None, 'text': "Change", 'start': 0, 'end': 6 }, 
                                '7': { 'label': None, 'text': "text", 'start': 7, 'end': 11 }, 
                                '12': { 'label': None, 'text': "color", 'start': 7, 'end': 17 }, 
                                '18': { 'label': None, 'text': "to", 'start': 18, 'end': 20 }, 
                                '21': { 'label': "color", 'text': "red", 'start': 21, 'end': 24 }, 
                            },
                            'id': 2
                        }
                    ]
                },

            ))
    elif endpoint == "response":
        if dev_id == 1:
            print(response(1, "the product of twenty and sixteen"))
        elif dev_id == 2:
            print(response(2, "change the color to orange"))

    elif endpoint == "update":
        if dev_id == 2:
            print(update(
                {
                    'dev_id': 2,
                    'intent': "check_weather",
                    'parameters': [{'label': 'location1', 'start': 23, 'end': 27}, {'label': 'location2', 'start': 33, 'end': 41}],
                    'old_query': "what is the weather in Tokyo and Shanghai",
                    'new_query': "what is the weather in Tokyo and Shanghai"
                }
            ))


