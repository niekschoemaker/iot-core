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
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
import matplotlib.pyplot as plt
import matplotlib.dates
import io
import base64
from datetime import datetime, timedelta 

#imports for mqtt-flask
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import re
import sys

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
    #string = "INSERT INTO DHT_data values('esp32_gerben',{datetime}, {temp}, {hum})".format(**jsonformat)
    logData(jsonformat['id'],jsonformat['datetime'],jsonformat['temp'],jsonformat['hum'])

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

CONNECTION_STRING = sys.argv[1]
if not is_correct_connection_string():
    print ( "Device connection string is not correct." )

TWIN_CALLBACKS = 0
SEND_REPORTED_STATE_CALLBACKS = 0
METHOD_CALLBACKS = 0
MESSAGE_SWITCH = True
RECEIVE_CONTEXT = 0
TWIN_CONTEXT = 0
METHOD_CONTEXT = 0

# Set protocol to use for the Iot client to MQTT
PROTOCOL = IoTHubTransportProvider.MQTT

# HTTP options
# Note that for scalabilty, the default value of minimumPollingTime
# is 25 minutes. For more information, see:
# https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000


def is_correct_connection_string():
    m = re.search("HostName=.*;DeviceId=.*;", CONNECTION_STRING)
    if m:
        return True
    else:
        return False

def device_twin_callback(update_state, payload, user_context):
    global TWIN_CALLBACKS
    print ( "\nTwin callback called with:\nupdateStatus = %s\npayload = %s\ncontext = %s" % (update_state, payload, user_context) )
    TWIN_CALLBACKS += 1
    print ( "Total calls confirmed: %d\n" % TWIN_CALLBACKS )


def send_reported_state_callback(status_code, user_context):
    global SEND_REPORTED_STATE_CALLBACKS
    print ( "Confirmation for reported state received with:\nstatus_code = [%d]\ncontext = %s" % (status_code, user_context) )
    SEND_REPORTED_STATE_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_REPORTED_STATE_CALLBACKS )


def device_method_callback(method_name, payload, user_context):
    global METHOD_CALLBACKS,MESSAGE_SWITCH
    print ( "\nMethod callback called with:\nmethodName = %s\npayload = %s\ncontext = %s" % (method_name, payload, user_context) )
    METHOD_CALLBACKS += 1
    print ( "Total calls confirmed: %d\n" % METHOD_CALLBACKS )
    device_method_return_value = DeviceMethodReturnValue()
    device_method_return_value.response = "{ \"Response\": \"This is the response from the device\" }"
    device_method_return_value.status = 200
    if method_name == "start":
        MESSAGE_SWITCH = True
        print ( "Start sending message\n" )
        device_method_return_value.response = "{ \"Response\": \"Successfully started\" }"
        return device_method_return_value
    if method_name == "stop":
        MESSAGE_SWITCH = False
        print ( "Stop sending message\n" )
        device_method_return_value.response = "{ \"Response\": \"Successfully stopped\" }"
        return device_method_return_value
    return device_method_return_value

def iothub_client_init():
    # prepare iothub client
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    client.set_option("product_info", "HappyPath_RaspberryPi-Python")
    if client.protocol == IoTHubTransportProvider.HTTP:
        client.set_option("timeout", TIMEOUT)
        client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
    # set the time until a message times out
    client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    # to enable MQTT logging set to 1
    if client.protocol == IoTHubTransportProvider.MQTT:
        client.set_option("logtrace", 0)
    client.set_message_callback(
        receive_message_callback, RECEIVE_CONTEXT)
    if client.protocol == IoTHubTransportProvider.MQTT or client.protocol == IoTHubTransportProvider.MQTT_WS:
        client.set_device_twin_callback(
            device_twin_callback, TWIN_CONTEXT)
        client.set_device_method_callback(
            device_method_callback, METHOD_CONTEXT)
    return client

RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
def receive_message_callback(message, counter):
    global RECEIVE_CALLBACKS
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    print ( "Received Message [%d]:" % counter )
    print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode("utf-8"), size) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    counter += 1
    RECEIVE_CALLBACKS += 1
    print ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
    return IoTHubMessageDispositionResult.ACCEPTED

def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    print ( "    message_id: %s" % message.message_id )
    print ( "    correlation_id: %s" % message.correlation_id )
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )

IOT_HUB_MSG_TXT = "{\"deviceId\": %f,\"temperature\": %f,\"humidity\": %f',\"pressure\": %f, \"rasptimestamp\": %s}"
def send_message(espid, temperature, humidity, pressure, rasptimestamp, message_count):
    # send a few messages every minute
    global client
    print ("IoTHubClient sending %d messages" % message_count)
    msg_txt_formatted = IOT_HUB_MSG_TXT % (
        espid
        temperature,
        humidity,
        pressure,
        rasptimestamp)
    print (msg_txt_formatted)
    message = IoTHubMessage(msg_txt_formatted)
    # optional: assign ids
    message.message_id = "message_%d" % message_count
    message.correlation_id = "correlation_%d" % message_count

    client.send_event_async(message, send_confirmation_callback, message_count)
    print ( "IoTHubClient.send_event_async accepted message [%d] for transmission to IoT Hub." % message_count )

    status = client.get_send_status()
    print ( "Send status: %s" % status )

# log sensor data on database
def logData (espid,timestamp,temp, hum):
	print("loggin data for:" + espid)
	conn=sqlite3.connect('../' + dbname)
	curs=conn.cursor()
	curs.execute("INSERT INTO DHT_data values((?), (?), (?), (?))",(espid, timestamp, temp, hum))
	count = curs.fetchone("SELECT COUNT(*) FROM DHT_data WHERE ID = (?)", (espid))
	send_message(espid,temp, hum, None, timestamp, count)
	conn.commit()
	conn.close()

dbname='sensorsData.db'

if __name__ == "__main__":
    global client
    client = iothub_client_init()
    conn=sqlite3.connect('../' + dbname)
    curs=conn.cursor()
    #database heeft ID colom nodig / aangezien we data voor beide esps moeten laten zien
    curs.execute("CREATE TABLE IF NOT EXISTS DHT_data (ID TEXT, timestamp DATETIME,  temp NUMERIC, hum NUMERIC);")
    conn.commit()
    conn.close()
    #logData(26.5, 29)
    app.run(host='0.0.0.0', port=5000, debug=False)


