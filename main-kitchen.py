from machine import Pin
import time
from time import sleep
from umqtt.simple import MQTTClient

broker = "192.168.0.29"
port = 1883
username = "mqtt-bakedpi"
password = "bakedpi"
state_topic = 'home/room'

# Send messages in a loop
client = MQTTClient("ESP-Kitchen", broker, port=port, user=username, password=password)
client.connect()

pir = Pin(27, Pin.IN)

while True:
  if pir():
    print('Motion detected!')
    sleep(10)
    msg = "Kitchen is occupied."
    client.publish(state_topic, msg)
    if not pir():
        print('Motion stopped.')