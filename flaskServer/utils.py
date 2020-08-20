import os, sys, json, time, datetime, requests, operator
import redis
from flask import Flask, request, render_template, Response, send_from_directory, make_response, send_file, redirect, jsonify
from flask_restplus import Api, Resource, fields, Namespace
from celery import Celery
from flask_apscheduler import APScheduler
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
import logging
from pytz import timezone

logging.basicConfig(filename="./flask.log", level=logging.INFO)


def get_log_date():
    dt = datetime.datetime.now(timezone("Asia/Seoul"))
    log_date = dt.strftime("%Y%m%d_%H:%M:%S")
    return log_date


def log(req, mes):
    log_date = get_log_date()
    log_message = "{0}/{1}/{2}".format(log_date, str(req), mes)
    logging.info(log_message)


def error_log(req, err_code, mes):
    log_date = get_log_date()
    mes = "{0}/{1}/{2}/{3}".format(log_date, str(req), err_code, mes)
    logging.info(mes)


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
alerts = api.namespace("alerts", description='<div style="background-color: #dc17171a; text-align: right">이상 수치, 발생 시 전달 APIs</div>')
cat_name_space = api.namespace("cats", description='<div style="background-color: #caddff; text-align: right">테스트 API 카테고리 01 입니다.</div>')
dog_name_space = api.namespace("dogs", description='<div style="background-color: #e0fff9; text-align: right">테스트 API 카테고리 02 입니다.</div>')
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

API_GATEWAY_URL = "http://218.55.23.200:10400/v2/report/push/state"


""" Maria DB, Read the Context_Awareness_Case """
class MariaDB:
    @staticmethod
    def connect():
        return 1
    @staticmethod
    def read():
        test = {
            "model": "CT_MODEL_01",
            "keyword": "RSSI",
            "title": "WiFi",
            "description": "ABCDEFFFF",
            "report_interval": 10,
            "model_id": 1,
            "pdf_id": 2,
            "page_num": 4,
            "param": "AP_RSSI",
            "threshold": -62,
            "operator": "lt"
        }
        test2 = {
            "model": "CT_MODEL_01",
            "keyword": "PM1.0",
            "title": "미세먼지",
            "description": "두둥ㄹ으등ㄹㅇ느",
            "report_interval": 30,
            "model_id": 2,
            "pdf_id": 3,
            "page_num": 2,
            "param": "PM1.0",
            "threshold": 50,
            "operator": "gt"
        }
        return [test,test2]
    @staticmethod
    def write():
        return 1


def context_awareness_setting():
    # todo : DB에서 Config 가져오기
    case = MariaDB.read()
    for _case in case:
        key = _case["model"]
        del _case["model"]
        val = _case
        conn.hmset(key, val)


print("Context Awareness Setting...")
context_awareness_setting()


def detected_rssi(device, rssi):
    if rssi is False:
        return False
    if int(rssi) < -80:
        """ Alert to Server """
        # print("Wireless Power is Very Week")
        pass


class Operator:
    @staticmethod
    def calculate(_oper, _p1, _p2):
        _p1 = int(_p1)
        _p2 = int(_p2)
        if _oper == "lt":
            return operator.lt(_p1, _p2)
        elif _oper == "le":
            return operator.le(_p1, _p2)
        elif _oper == "gt":
            return operator.gt(_p1, _p2)
        elif _oper == "ge":
            return operator.ge(_p1, _p2)
        elif _oper == "eq":
            return operator.eq(_p1, _p2)
        elif _oper == "ne":
            return operator.ne(_p1, _p2)

