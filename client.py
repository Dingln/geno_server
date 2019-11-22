import requests
import sys

if len(sys.argv) < 2:
    print("Usage: python3 client.py [train/response]")
    exit()

if sys.argv[1] == "train":
    json_data = {
        'dev_id': "1",
        'intent': "check_balance",
        'queries': "what is my balance"
    }
    res = requests.post("http://127.0.0.1:3001/train", json=json_data)
elif sys.argv[1] == "response":
    res = requests.get("http://127.0.0.1:3001/response")

print(res.headers)
print(res.text)
exit()

