import os, sys, json, time, datetime
import redis
from flask import Flask, request, render_template, Response
from flask_restplus import Api, Resource, fields, Namespace
from celery import Celery
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders

app = Flask(__name__)
api = Api(app,
          version='0.10',
          title='상황인지 시스템',
          description='<h2 style="background-color: #fde3c9e0">에브리봇 물걸레 청소기 기반 서비스 시나리오.</h1>'
                      '<div style="background-color: #eefdc9e0">case1 : 마지막 주기보고 시각을 기록한 뒤, 일정 시각 경과 후 작동하고 '
                      '내부 batch daemon이 분단위로 체크, 3분 경과시 와이파이 연결 상태 체크 관련 문구 notification 발생.\n'
                      'case2 : RSSI 값을 매회 체크하여 일정 수치 이하로 감소시 작동. 일시적인 하락으로 인한 오탐 방지 로직 검토 진행.\n</div>',
          validate=True,
          default=None)
cat_name_space = api.namespace("Cat", description='<div style="background-color: #caddff">Main APIs</div>')
dog_name_space = api.namespace("Dog", description='<div style="background-color: #e0fff9">Sub APIs</div>')
abnormal_ns = api.namespace("Abnormal", description='<div style="background-color: #dc17171a">이상 수치, 발생 시 전달 APIs</div>')
# api.default_namespace()


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
        print("Device ID :", key.decode(), "| Timestamp :", res[0].decode(), "| RSSI :", res[1].decode(),
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




