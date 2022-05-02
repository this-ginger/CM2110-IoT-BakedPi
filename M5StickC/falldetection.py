#Library based on project https://github.com/just4give/senior-aid/blob/master/ble-device/fall_detection.py
#and edited to suit.
import smbus
import math
from umqtt.simple import MQTTClient
import time
import json
from datetime import datetime
import threading
from machine import Pin

def on_connect(client, userdata, flags, rc):
    print("Connected.")
    client.connected_flag=True

def on_message(client, userdata, message):
    print("Received")

broker = "192.168.0.29"
port = 1883
username = "mqtt-bakedpi"
password = "bakedpi"
state_topic = 'home/fall'

client = MQTTClient("M5Stick", broker, port=port, user=username, password=password)
client.loop_start()
client.connect()
client.subscribe('home/fall')

pin = machine.Pin(37, machine.Pin.IN, machine.Pin.PULL_UP)
power_1 = 0x6b
power_2 = 0x6c
AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ = 0.0
ax, ay, az, gx, gy, gz = 0
fall = False
trigger1=False
trigger2=False
trigger3=False

trigger1count=0
trigger2count=0
trigger3count=0
angleChange=0

#def mpu_read():
    
def read_byte(reg):
    return bus.read_byte_data(address, reg)
 
def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value
 
def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val
 
def dist(a,b):
    return math.sqrt((a*a)+(b*b))
 
def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)
 
def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)
 
bus = smbus.SMBus(1)
address = 0x68
bus.write_byte_data(address, power_1, 0)

def check_panic_button():
    while True:
        button_state = pin.input(37)
        if button_state == False:
            print('Panic')
            data={'mac':device,'ts': int(time.time()*1000)}
            client.publish('home/fall/detected',json.dumps(data))
            time.sleep(5)
        else:
            time.sleep(0.1)

def check_online():
    while True:
        data={'mac':device,'ts': int(time.time()*1000)}
        client.publish('home/fall/device/online',json.dumps(data))
        time.sleep(5)

if __name__ == 'main':
    try:
        threading.Thread(target=check_panic_button,daemon=True).start()
        threading.Thread(target=check_online,daemon=True).start()
        while True:
            try:
                AcX=read_word_2c(0x3b)   
                AcY=read_word_2c(0x3d)
                AcZ=read_word_2c(0x3f)
                Tmp=read_word_2c(0x41)
                GyX=read_word_2c(0x43)
                GyY=read_word_2c(0x45)
                GyZ=read_word_2c(0x47)

                ax = (AcX-2050)/16384.00
                ay = (AcY-77)/16384.00
                az = (AcZ-1947)/16384.00

                gx = (GyX+270)/131.07
                gy = (GyY-351)/131.07
                gz = (GyZ+136)/131.07
                
                Raw_AM = math.sqrt((ax*ax)+(ay*ay)+(az*az))
                AM = Raw_AM * 10
                if trigger3==True:
                    trigger3count=trigger3count+1
                    if trigger3count>=10:
                        angleChange=math.sqrt((gx*gx)+(gy*gy)+(gz*gz))
                        print("angleChange=",angleChange)
                        if angleChange>=0 and angleChange<=10:
                            fall=True
                            trigger3=False
                            trigger3count=0
                        else: #user regained normal orientation
                            trigger3=False
                            trigger3count=0
                            print("TRIGGER 3 DEACTIVATED")
                
                if fall==True:
                    print("Fall detected")
                    fall=False
                    data={'mac':device,'ts': int(time.time()*1000)}
                    client.publish('senior-aid/fall/detected',json.dumps(data))
                
                if trigger2count>=6:
                    trigger2=False
                    trigger2count=0
                    print("TRIGGER 2 DECACTIVATED")
                
                if trigger1count>=6:
                    trigger1=False
                    trigger1count=0
                    print("TRIGGER 1 DECACTIVATED")

                if trigger2==True:
                    trigger2count=trigger2count+1
                    angleChange = math.sqrt((gx*gx)+(gy*gy)+(gz*gz))
                    if angleChange>=30 and angleChange<=400:
                        trigger3=True
                        trigger2=False
                        trigger2count=0
                        print("TRIGGER 3 ACTIVATED=",angleChange)
                
                if trigger1==True:
                    trigger1count=trigger1count+1
                    if AM>=12: #Upper Threshold
                        trigger2=True
                        print("TRIGGER 2 ACTIVATED")
                        trigger1=False
                        trigger1count=0
                
                if AM<=2 and trigger2==False: #Lower Threshold
                    trigger1=True
                    print("TRIGGER 1 ACTIVATED")
            except IOError as e:
                print("I/O error({}): {}".format(e.errno, e.strerror))
            except:
                print("Oop. Something's not right.")
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopped")
        