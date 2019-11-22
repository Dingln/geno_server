import requests
import sys

if len(sys.argv) < 2:
    print("Usage: python3 client.py [train/response]")
    exit()

if sys.argv[1] == "train":
    json_data = {
        'dev_id': 1,
        'intent': "multiply_numbers",
        'queries': ["what is the product of two and four", "multiply six and ten", "product of fourteen and twelve", "whats the product of thirty and eleven"]
    }
    res = requests.post("http://127.0.0.1:3001/train", json=json_data)
elif sys.argv[1] == "response":
    payload = {'query': "hello"}
    res = requests.get("http://127.0.0.1:3001/response", params=payload)

print(res.headers)
print(res.text)
exit()

