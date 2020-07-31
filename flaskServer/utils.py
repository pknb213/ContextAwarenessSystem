import os, sys, json, time, datetime
import redis
from flask import Flask, request, render_template, Response
from flask_restplus import Api, Resource
from celery import Celery
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
api = Api(app)


def connect_redis():
    try:
        conn = redis.Redis(host='localhost', port=6379, db=0)
    except Exception as e:
        print("DB Connection Error : ", e)
        return False
    return conn


def info_redis():
    res = conn.info(section="memory")
    print(res)


conn = connect_redis()
conn.flushall()


def heartbeat():
    """ Heartbeat Test API """
    print("> Still alive!", datetime.datetime.now(), datetime.datetime.now().timestamp())
    for key in conn.keys():
        res = conn.hmget(key.decode(), "ts", "rssi")
        print("Device ID :", key.decode(), "Timestamp :", res[0].decode(), "RSSI :", res[1].decode(),
              "Recently Report Time Gap(s) :", datetime.datetime.now().timestamp() - float(res[0].decode()))


""" APSecheduler : https://apscheduler.readthedocs.io/en/latest/userguide.html 
    Bug : Flask Debug Mode is Twice execution. Because re-loader.
    'date' : once specific datetime execution 
    'interval' : static time range execution
    'cron' : Today specific time execution 
"""
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(heartbeat, 'interval', seconds=10, id='heartbeat_job')
scheduler.start()



