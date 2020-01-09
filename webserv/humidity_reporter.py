# while True:
#         humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
#         if humidity is not None and temperature is not None:
#            print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humi$
#         else:
#            print("Failed to retrieve data from the sensor")


from flask import Flask, request
from graphene import ObjectType, Float, List, String, Schema
from flask_graphql import GraphQLView
import Adafruit_DHT
import json
import os

# Setup
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4


class SensorValues(ObjectType):
    temperature=Float()
    humidity=Float()

class Query(ObjectType):
    # temperature = Float(temperature=Float())
    # humidity = Float(humidity=Float())

    sensorvalues = List(SensorValues)       

    def resolve_sensorvalues(root, info):
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        # if humidity is not None and temperature is not None:
        #    return  temperature, humidity
        # else:
        #    return -1.0, -1.0
        sensorvalues = [SensorValues(temperature=temperature, humidity=humidity)]

        return sensorvalues

    # def resolve_temperature(root, info, temperature):
    #     return temperature

    # def resolve_humidity(root, info, humidity):
    #     return humidity

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
