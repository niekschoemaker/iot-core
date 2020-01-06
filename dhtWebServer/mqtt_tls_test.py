import paho.mqtt.client as paho
import time
broker='192.168.178.80'
port=8883
conn_flag = False

def on_connect(client, userdata, flags, rc):
          global conn_flag
          conn_flag = True
          print("connected")

def on_log(client, userdata, level, buf):
          print("buf")

def on_disconnect(client, userdata, rc):
          print("disconnect")

client1 = paho.Client("control1")
client1.on_log=on_log
client1.tls_set('/etc/mosquitto/ca_certificates/ca.crt')
client1.on_connect = on_connect
client1.on_disconnect=on_disconnect
client1.connect(broker,port)
while not conn_flag:
          time.sleep(1)
          print("waiting")
          client1.loop()
time.sleep(3)
print("publsinhing")
client1.publish("esp32", "wollolololo")
time.sleep(2)
client1.loop()
time.sleep(2)
client1.disconnect()


