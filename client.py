import requests
import sys


def train(*data):
    res = []
    for json in data:
        res.append(requests.post("http://127.0.0.1:3001/train", json=json).text)
       
    return res

def response(dev_id, query):
    payload = {'dev_id': dev_id, 'query': query}
    res = requests.get("http://127.0.0.1:3001/response", params=payload)
    return res.text

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
                    'queries': ["what is the product of two and four", "multiply six and ten", "product of fourteen and twelve", "whats the product of thirty and eleven"]
                },
                {
                    'dev_id': 1,
                    'intent': "check_balance",
                    'queries': ["how much money is in my checking account", "what is the balance of my checking account", "how much money in my savings account", "what is the balance of my savings account"]
                }
            ))
        elif dev_id == 2:
            print(train({
                    'dev_id': 2,
                    'intent': "introduction",
                    'queries': ["hi my name is joe", "hello I'm bob", "hi i'm john", "hey my name is andrew"]
                },
                {
                    'dev_id': 2,
                    'intent': "check_weather",
                    'queries': ["what's the weather in sacramento", "what is the weather in los angeles", "what is the weather in tokyo", "whats the weather like in london"]
                }
            ))
    elif endpoint == "response":
        if dev_id == 1:
            print(response(1, "the product of twenty and sixteen"))
        elif dev_id == 2:
            print(response(2, "whats the weather in atlanta"))

