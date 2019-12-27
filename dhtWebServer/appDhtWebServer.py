#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  appDhtWebServer.py
#  
#  Created by MJRoBot.org 
#  10Jan18

'''
	RPi Web Server for DHT captured data  
'''

from flask import Flask, render_template, request
import json
import sqlite3
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io


#imports for mqtt-flask
from flask_mqtt import Mqtt
from flask_socketio import SocketIO



app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.178.109'  # brokerip dit moet raspberry zijn
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection

mqtt = Mqtt(app)
socketio = SocketIO(app)
#eventlet.monkey_patch()

# functies voor handelen connectie met mqtt en messages vanuit topic
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp32_gerben')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = message.payload.decode("utf-8")
    jsonformat = json.loads(data)
    #string = "INSERT INTO DHT_data values('esp32_gerben',{datetime}, {temp}, {hum})".format(**jsonformat)
    logData(jsonformat['id'],jsonformat['datetime'],jsonformat['temp'],jsonformat['hum'])


dbname='sensorsData.db'

# Retrieve data from database
def getData():
	conn=sqlite3.connect('../sensorsData.db')
	curs=conn.cursor()

	#hier nog ID toevoegen
	for row in curs.execute("SELECT * FROM DHT_data ORDER BY timestamp DESC LIMIT 1"):
		time = str(row[1])
		temp = row[2]
		hum = row[3]

	for row in curs.execute("SELECT * FROM DHT_data Where ID = 'esp32_gerben' ORDER BY timestamp DESC LIMIT 1"):
		time2 = str(row[1])
		temp2 = row[2]
		hum2 = row[3]
	conn.close()
	return time, temp, hum, time2, temp2, hum2

# main route 
@app.route("/")
def index():
	
	time, temp, hum, time2, temp2, hum2 = getData()
	templateData = {
	  'time'	: time,
      	  'temp'  : temp,
      	  'hum'	: hum,
	  'time2'	: time2,
      	  'temp2'  : temp2,
      	  'hum2'	: hum2
	}
	return render_template('index.html', **templateData)

# log sensor data on database
def logData (espid,datetime,temp, hum):
	print("loggin data for:" + espid)
	conn=sqlite3.connect('../' + dbname)
	curs=conn.cursor()
	curs.execute("INSERT INTO DHT_data values((?), (?), (?), (?))",(espid, datetime, temp, hum))
	conn.commit()
	conn.close()

if __name__ == "__main__":
    conn=sqlite3.connect('../' + dbname)
    curs=conn.cursor()
    #database heeft ID colom nodig / aangezien we data voor beide esps moeten laten zien
    curs.execute("CREATE TABLE IF NOT EXISTS DHT_data (ID TEXT, timestamp DATETIME,  temp NUMERIC, hum NUMERIC);")
    conn.commit()
    conn.close()
    #logData(26.5, 29)
    app.run(host='0.0.0.0', port=5000, debug=False)