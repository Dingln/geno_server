import requests

res = requests.get("http://127.0.0.1:5000/response")

# print(res.headers)
print(res.text)