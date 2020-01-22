#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  appDhtWebServer.py
#  
#  Created by MJRoBot.org 
#  10Jan18
#  Edited by:
#  Gerben Bunt and Niek Schoemaker

'''
	RPi Web Server for DHT captured data  
'''

from flask import Flask, render_template, request
import json
import sqlite3
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates
import io
import base64
from datetime import datetime, timedelta 

#imports for mqtt-flask
from flask_mqtt import Mqtt
from flask_socketio import SocketIO

dbname='sensorsData.db'

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.178.80'  # brokerip dit moet raspberry zijn
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = 'gerben'
app.config['MQTT_PASSWORD'] = 'bunt' 

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
    print(jsonformat['id'])
    
    if jsonformat['id'] == 'esp32_gerben' or jsonformat['id'] == 'esp32_niek':
	    logData(jsonformat['id'],jsonformat['datetime'],jsonformat['temp'],jsonformat['hum'])
    else:
	    print("wrong message recieved BE CAREFULL!!!")


#functie om datum vanaf html om te zetten in fatsoenlijk format
def convertdateformat (date):
	date_in = date
	date_processing = date_in.replace('T', '-').replace(':', '-').split('-')
	date_processing = [int(v) for v in date_processing]
	date_out = datetime(*date_processing)
	
	return date_out

# Retrieve data from database
def getData():
	conn=sqlite3.connect('../sensorsData.db')
	curs=conn.cursor()
	
	#hier nog ID toevoegen
	for row in curs.execute("SELECT * FROM DHT_data Where ID = 'esp32_gerben' ORDER BY timestamp DESC LIMIT 1"):
		timevar = str(row[1])
		tempvar = row[2]
		humvar = row[3]
		print(curs.rowcount)
		
	timevar2 = '00:00:0000 00:00:00'
	tempvar2 = 0
	humvar2 = 0

	for row2 in curs.execute("SELECT * FROM DHT_data Where ID='esp32_niek' ORDER BY timestamp DESC LIMIT 1"):
		timevar2 = str(row2[1])
		tempvar2 = row2[2]
		humvar2 = row2[3]

	conn.close()
	return timevar, tempvar, humvar, timevar2, tempvar2, humvar2

def getHistData(date, date2):
	conn=sqlite3.connect('../sensorsData.db')
	curs=conn.cursor()

	curs.execute("SELECT * FROM DHT_data WHERE timestamp BETWEEN (?) AND (?)",(date, date2))
	data = curs.fetchall()
	dates1 = []
	temps1 = []
	hums1 = []

	dates2 = []
	temps2 = []
	hums2 = []
	no_data_warning = ""
	for row in reversed(data):
		
		if row[0] == 'esp32_gerben':
			dates1.insert(0,row[1])
			temps1.insert(0,row[2])
			hums1.insert(0,row[3])
		else:
			dates2.insert(0,row[1])
			temps2.insert(0,row[2])
			hums2.insert(0,row[3])
	conn.close()
	
	if len(dates1) and len(dates2) > 0:
		img1 = create_plots("esp32_gerben",dates1,temps1,hums1)
		img2 =create_plots("esp32_niek",dates2,temps2,hums2)	
		no_data_warning = " "
		return no_data_warning, img1, img2	
	elif len(dates1) > 0 and len(dates2) == 0:
		img1 = create_plots("esp32_gerben",dates1,temps1,hums1)
		img2 = ""
		no_data_warning = ""
		return no_data_warning, img1, img2
	elif len(dates1) == 0 and len(dates2) > 0: 
		img1 = ""
		img2 = create_plots("esp32_niek",dates2,temps2,hums2)	
		no_data_warning = ""
		return no_data_warning, img1, img2
	else:
		print("no data available")
		img1 = ""
		img2 = ""
		no_data_warning = "no data available!!!!!!!!!!!!!!!!!!!!!!"	
		return no_data_warning, img1, img2	
	
	
	
#function creates graph and returns as image.
def create_plots(espid,dates,temps,hums):
	fig,axs = plt.subplots(2,1)

	axs[0].set_ylabel('temperature in C')
	axs[1].set_ylabel('humidity in %')
	axs[0].set_title('esp32_gerben')
	axs[1].set_title('esp32_niek')

	every_nth = 2
	for n, label in enumerate(axs[0].xaxis.get_ticklabels()):
		label.set_rotation(90)
		label.set_horizontalalignment("right")
		if n % every_nth != 0:
			label.set_visible(False)
		
	for n, label in enumerate(axs[1].xaxis.get_ticklabels()):
		label.set_rotation(90)
		label.set_horizontalalignment("right")
		if n % every_nth != 0:
			label.set_visible(False)
		
	axs[0].plot(dates,temps)
	axs[1].plot(dates,hums)
	
	fig.suptitle(id)
	fig.set_figwidth(20)
	fig.set_figheight(10)
	fig.tight_layout()
	
	print("proccesing graphs")
	pngImage = io.BytesIO()
	FigureCanvas(fig).print_png(pngImage)
	pngImageB64String = "data:image/png;base64,"
	pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
	return pngImageB64String

# main route 
@app.route("/", methods=['POST','Get'])
def index():
	time2 = 0
	time, temp, hum, time2, temp2, hum2 = getData()
	templateData = {
	  'time'	: time,
      	  'temp'  : temp,
      	  'hum'	: hum,
	  'time2'	: time2,
      	  'temp2' : temp2,
      	  'hum2'	: hum2
	}
	#Als er een post is uitgevoerd voor de grafieken
	if request.method == 'POST':
		startdatetime = request.form['starttime']
		stopdatetime = request.form['endtime']
		date_out1 = convertdateformat(startdatetime) - timedelta(minutes=60)
		date_out2 = convertdateformat(stopdatetime) - timedelta(minutes=60)
	
		#functie om grafieken op te halen en warning message
		warning , image1, image2= getHistData(date_out1, date_out2)
		templateData["warning"] = warning
		templateData["image1"] = image1
		templateData["image2"] = image2
	
	return render_template('index.html', **templateData)

# log sensor data on database
def logData (espid,timestamp,temp, hum):
	print("loggin data for:" + espid)
	conn=sqlite3.connect('../' + dbname)
	curs=conn.cursor()
	curs.execute("INSERT INTO DHT_data values((?), (?), (?), (?))",(espid, timestamp, temp, hum))
	conn.commit()
	conn.close()



if __name__ == "__main__":
    conn=sqlite3.connect('../' + dbname)
    curs=conn.cursor()
    curs.execute("CREATE TABLE IF NOT EXISTS DHT_data (ID TEXT, timestamp DATETIME,  temp NUMERIC, hum NUMERIC);")
    conn.commit()
    conn.close()
    app.run(host='0.0.0.0', port=5000, debug=False)


