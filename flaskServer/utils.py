import os, sys, json, time, datetime, requests, operator
import redis
from flask import Flask, request, render_template, Response, send_from_directory, make_response, send_file, redirect, \
    jsonify
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

# MACRO
DEVICE_ID = "DEVICE_ID"
MODEL_NAME = "MODEL_NAME"


# Logging APIs
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


# Redis APIs
def connect_redis():
    try:
        conn = redis.Redis(host='localhost', port=6379, db=0)
    except Exception as e:
        print("DB Connection Error : ", e)
        return False
    return conn


def info_redis():
    res = cache.info(section="memory")
    print(res)


# Maria DB, Read the Context_Awareness_Case
class MariaDB:
    def __init__(self):
        pass

    @staticmethod
    def connect():
        # todo : Maria DB 커넥트 부분
        return 1

    @staticmethod
    def read():
        # todo : Read 결과가 List 자료형으로 [row1, row2 . . .] 이여야 함.
        row1 = {
            "_seq": 1,
            "model": "CT_MODEL_01",
            "keyword": "RSSI",
            "title": "WiFi 감도 이상",
            "description": "WiFi 수신 세기가 너무 약합니다.",
            "report_interval": 10,
            "model_id": 1,
            "pdf_id": "RS500N_users_guide.pdf",
            "page_num": 4,
            "param": "AP_RSSI",
            "threshold": -60,
            "operator": "lt"
        }
        row2 = {
            "_seq": 2,
            "model": "CT_MODEL_02",
            "keyword": "PM1.0",
            "title": "초 미세 먼지가 심각",
            "description": "공기 정화기가 필요합니다.",
            "report_interval": 30,
            "model_id": 2,
            "pdf_id": "RS500N_users_guide.pdf",
            "page_num": 3,
            "param": "PM1.0",
            "threshold": 50,
            "operator": "gt"
        }
        row3 = {
            "_seq": 3,
            "model": "CT_MODEL_02",
            "keyword": "PM10",
            "title": "미세 먼지가 심각",
            "description": "환기가 필요합니다.",
            "report_interval": 30,
            "model_id": 2,
            "pdf_id": "RS500N_users_guide.pdf",
            "page_num": 6,
            "param": "PM10",
            "threshold": 50,
            "operator": "gt"
        }
        return [row1, row2, row3]

    @staticmethod
    def write():
        # todo : read 함수의 스키마와 같이 새로운 Raw를 저장할 수 있는 함수.
        return 1

    @classmethod
    def select(cls, sql):
        pass


def context_awareness_setting():
    # todo : DB에서 Config 가져오기
    print("Context Awareness Setting...")
    case = MariaDB.read()
    for _case in case:
        """ Hash 형태로 model_list : Model 저장 """
        cache.sadd("model_list", _case["model"])
        cache.sadd(_case["model"], _case["_seq"])
        """ Hash 형태로 Model : Config 값 저장 """
        cache.hmset(_case["_seq"], _case)


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


cache = connect_redis()
cache.flushall()
context_awareness_setting()
time.sleep(2)
API_GATEWAY_URL = "http://218.55.23.200:10400/v2/report/push/state"
LOCAL_URL = "http://218.55.23.208:5000"
logging.basicConfig(filename="./flask.log", level=logging.INFO)
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
alerts = api.namespace("alerts",
                       description='<div style="background-color: #dc17171a; text-align: right">이상 수치, 발생 시 전달 APIs</div>')
# cat_name_space = api.namespace("cats", description='<div style="background-color: #caddff; text-align: right">테스트 API 카테고리 01 입니다.</div>')
# dog_name_space = api.namespace("dogs", description='<div style="background-color: #e0fff9; text-align: right">테스트 API 카테고리 02 입니다.</div>')
# api.default_namespace()
