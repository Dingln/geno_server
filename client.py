import requests

json_data = {'dev_id': "1",
             'intent': "check_balance",
             'queries': "what is my balance"
             }

r = requests.post("http://127.0.0.1:5000/train", json=json_data)

print(r.headers)
print(r.text)

res = requests.get("http://127.0.0.1:5000/test", json=json_data)

print(res.headers)
print(res.text)