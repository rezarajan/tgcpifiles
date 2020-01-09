import requests

# Request endpoints
url = 'http://192.168.2.46:5000/graphql'
json = {'query': '{ sensorvalues { temperature humidity } }'}

response = requests.post(url=url, json=json).json()
data = response['data']
print(data)
print(data['sensorvalues'][0]['humidity'])
