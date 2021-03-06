import os
import socket
from datetime import datetime
import time
import urllib2
import json
import threading
import redis
from graphqlclient import GraphQLClient
from gps3 import gps3
from logging import basicConfig, getLogger, DEBUG, handlers
import serial

# logging
basicConfig(level=DEBUG)
logger = getLogger(__name__)
handler = handlers.TimedRotatingFileHandler(
    filename='/home/pi/scripts/logs/loggingGPS.log',
    when='D'
)
logger.addHandler(handler)

# redis settings
r = redis.Redis(host='localhost', port=6379, db=0)

GRAPHQL_URL = os.environ['URL_PROD']
#GRAPHQL_URL = 'http://localhost:4000/graphql'
# default timeout is about 1 min.
socket.setdefaulttimeout(10)

# gps info
gps_info = {}


def getRaspiConfig():
    client = GraphQLClient(GRAPHQL_URL)
    result = None
    config = None
    try:
        result = client.execute(
            """query{
                ReadRasppiConfig(type: {id:9}){
                    id,
                    gpsInterval
                }
            }"""
        )
    except urllib2.URLError as err:
        if err.reason.strerror == 'nodename nor servname provided, or not known':
            config = json.loads(r.get('gpsconfig'))
            pass
        elif err.reason.message == 'timed out':
            config = json.loads(r.get('gpsconfig'))
            pass
        elif err.reason.errno == 51:
            config = json.loads(r.get('gpsconfig'))
            pass
        print(err.reason)
        logger.error(err.reason)
    if result is not None:
        config = json.loads(result)["data"]["ReadRasppiConfig"]
        if len(config) != 0:
            config = config[0]
            r.set('gpsconfig', json.dumps(config))
        else:
            config = r.get('gpsconfig')
    return config


def get_gps(data_stream, gps_socket, config):
    global lastLatLon
    global gps_info
    counter = 0
    for newdata in gps_socket:
        if counter <= 5:
            counter += 1
            continue
        if newdata:
            data_stream.unpack(newdata)

        if data_stream.TPV['time'] != 'n/a':
            #print 'time : ', data_stream.TPV['time']
            gps_info['time'] = data_stream.TPV['time']
        if data_stream.TPV['lat'] != 'n/a' or data_stream.TPV['lon'] != 'n/a':
            #print 'lat : ', data_stream.TPV['lat']
            gps_info['lat'] = data_stream.TPV['lat']
            #print 'lon : ', data_stream.TPV['lon']
            gps_info['lon'] = data_stream.TPV['lon']
            lastLatLon = (gps_info['lat'], gps_info['lon'])
        if data_stream.TPV['alt'] != 'n/a':
            #print 'alt : ', data_stream.TPV['alt']
            gps_info['alt'] = data_stream.TPV['alt']
        if data_stream.TPV['track'] != 'n/a':
            #print 'track : ', data_stream.TPV['track']
            gps_info['track'] = data_stream.TPV['track']
    return gps_info


def upload_server(timestr, gps_info, serial):
    if gps_info.viewkeys() >= {'lon', 'lat'}:
        try:
            client = GraphQLClient(GRAPHQL_URL)
            result = None
            query = "mutation{" + \
                "CamCreateGps(input: {" + \
                    "deviceSerial: \"" + serial + "\"," + \
                    "longitude:" + str(gps_info['lon']) + "," + \
                    "latitude:" + str(gps_info['lat']) + \
                "})}"
            result = client.execute(
                query
            )
        except urllib2.URLError as err:
            print err
            logger.error(err.reason)
        if result is not None:
            print result
            logger.info(result)


def seedData():
    f = open(
        "../futakotamagawa.json", 'r')
    json_data = json.load(f)["data"]["ReadGpsPoint"]

    for data in json_data:
        timestr = datetime.now().strftime('%Y_%m_%dT%H_%M_%S%f')
        print "starting upload photo"
        gps_info["lat"] = data["latitude"]
        gps_info["lon"] = data["longitude"]

        upload_server(timestr, gps_info, serialNo)
        print "finish upload gps data"


if __name__ == "__main__":
    # seeding data (usually comment out)
    # seedData()

    # gps_info = {
    #     'lon': 139.727873128,
    #     'lat': 35.658070908,
    #     'alt': 18.638
    # }

    # default interval
    interval = 1
    gps_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()

    config = getRaspiConfig()

    serialNo = serial.getserial()

    if config is not None and len(config) != 0:
        interval = 5
    else:
        interval = 5

    thread = threading.Thread(target=get_gps, args=(
        data_stream, gps_socket, config))
    thread.start()

    while True:
        timestr = datetime.now().strftime('%Y_%m_%dT%H_%M_%S%f')
        print "gps_infomation: " + str(gps_info)
        logger.info("gps_infomation: " + str(gps_info))
        print "starting upload photo"
        upload_server(timestr, gps_info, serialNo)
        print "finish upload gps data"
        time.sleep(interval)
