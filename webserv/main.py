from flask import Flask, request
from graphene import ObjectType, Float, List, String, Schema
from flask_graphql import GraphQLView
import json
import os


class SensorValues(ObjectType):
    temperature=Float()
    humidity=Float()

class Query(ObjectType):
    # this defines a Field `hello` in our Schema with a single Argument `name`
    hello = String(name=String(default_value="stranger"))
    goodbye = String(temp=Float(default_value=27.0), humi=Float(default_value=54.0))
    temperature = Float(temperature=Float())
    humidity = Float(humidity=Float())

    sensorvalues = List(SensorValues)

    def _json_object_hook(d):
        return namedtuple('X', d.keys())(*d.values())

    def json2obj(data):
        return json.loads(data, object_hook=_json_object_hook)

    def resolve_sensorvalues(root, info):
        # sensorvalues = {"temperature": 28.0, "humidity": 56.0}
        sensorvalues = [SensorValues(temperature=25.9, humidity=56.4)]
        return sensorvalues

    # our Resolver method takes the GraphQL context (root, info) as well as
    # Argument (name) for the Field and returns data for the query Response
    def resolve_hello(root, info, name):
        return f'Hello {name}!'

    def resolve_goodbye(root, info, temp, humi):
        return f'Temp: {temp}    Humidity: {humi}'

    def resolve_temperature(root, info, temperature):
        return temperature

    def resolve_humidity(root, info, humidity):
        return humidity

view_func = GraphQLView.as_view(
    'graphql', schema = Schema(query=Query), graphiql=True)

app = Flask(__name__)
app.add_url_rule('/graphql', view_func=view_func)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
        
# schema = Schema(query=Query)

# @app.route("/graphql", methods=['POST'])
# def graphql():
#     data = json.loads(request.data)
#     result = schema.execute(data['query'])
#     # print(dir(result))
#     # print(dir(result.data))
#     # print(result.data['hello'])

#     if 'temperature' in result.data:
#         return {"temperature": result.data['temperature']}

#     if 'humidity' in result.data:
#         return {"humidity": result.data['humidity']}

    # print(dir(result.to_dict))
    # values = []
    # values.append({"temp": 1.0, "hum": 2.0})
    # print(values[0])
