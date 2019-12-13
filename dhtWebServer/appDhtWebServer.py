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

# #imports for mqtt-flask
# from flask_mqtt import Mqtt
# from flask_socketio import SocketIO

# app.config['MQTT_BROKER_URL'] = '192.168.178.80'  # brokerip dit moet raspberry pi zijn
# app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection

# mqtt = Mqtt(app)
# socketio = SocketIO(app)

app = Flask(__name__)

#eventlet.monkey_patch()

#  # functies voor handelen connectie met mqtt en messages vanuit topic
# @mqtt.on_connect()
# def handle_connect(client, userdata, flags, rc):
#     mqtt.subscribe('esp32_gerben')

# @mqtt.on_message()
# def handle_mqtt_message(client, userdata, message):
#     data = dict( topic=message.topic,payload=message.payload.decode())
#     print(message.payload)

import sqlite3

dbname='sensorsData.db'

# Retrieve data from database
def getData():
	conn=sqlite3.connect('../sensorsData.db')
	curs=conn.cursor()

	for row in curs.execute("SELECT * FROM DHT_data ORDER BY timestamp DESC LIMIT 1"):
		time = str(row[0])
		temp = row[1]
		hum = row[2]
	conn.close()
	return time, temp, hum

# main route 
@app.route("/")
def index():
	
	time, temp, hum = getData()
	templateData = {
	  'time'	: time,
      	  'temp'  : temp,
      	  'hum'	: hum
	}
	return render_template('index.html', **templateData)

# log sensor data on database
def logData (temp, hum):
	conn=sqlite3.connect('../' + dbname)
	curs=conn.cursor()
	curs.execute("INSERT INTO DHT_data values(datetime('now'), (?), (?))", (temp, hum))
	conn.commit()
	conn.close()

if __name__ == "__main__":
    conn=sqlite3.connect('../' + dbname)
    curs=conn.cursor()
    #database heeft ID colom nodig / aangezien we data voor beide esps moeten laten zien
    curs.execute("CREATE TABLE IF NOT EXISTS DHT_data (ID TEXT, timestamp DATETIME,  temp NUMERIC, hum NUMERIC);")
    conn.commit()
    conn.close()
    logData(26.5, 29)
    app.run(host='0.0.0.0', port=5000, debug=False)