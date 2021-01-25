import os, sys, json, time, datetime, requests, operator, random, signal, math
import redis
from flask import Flask, request, render_template, Response, send_from_directory, make_response, send_file, redirect, \
    jsonify, url_for
from flask_restplus import Api, Resource, fields, Namespace
from celery import Celery
from flask_apscheduler import APScheduler
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
import logging
from logging.handlers import TimedRotatingFileHandler
import operator
import time

import pymysql
import redis
from flask import Flask
from flask_restplus import Api
from pytz import timezone

# MACRO
DictCursor = pymysql.cursors.DictCursor
PDF_PAGE_PARAMETER = 'page'
SERVICE_LOG_PATH = './logs/service'
ERROR_LOG_PATH = './logs/error'
SWAGGER_LOG_PATH = './logs/swagger'
DIRECTORY_PATHS = [SERVICE_LOG_PATH, ERROR_LOG_PATH, SWAGGER_LOG_PATH]

# SERVICE NAME
RA1000 = 'everybot-ra1000'
RS900 = 'everybot-rs900'
HA831 = 'daeyoung-ha-831'
HA830 = 'daeyoung-ha-830'
G100SR = 'grib-g100sr'
CAFU15 = 'ct-cafu15'
RS300 = "everybot-rs300_v2"

# URL MACRO
API_GATEWAY_URL = "http://218.55.23.200:10400/v2/report/push/state"
LOCAL_URL = "http://218.55.23.208:5000"
TEST_URL = "http://localhost:5000"

# RDB MACRO
RDB_ID = 'ca_id'
MODEL = 'model_name'
KEYWORD = 'ca_error_case'
TITLE = 'noti_title'
DESCRIPTION = 'noti_description'
REPORT_INTERVAL = 'interval_sec'
MODEL_ID = 'model_id'  # Not use
PDF_ID = 'pdf_id'
PDF_NAME = 'pdf_url'
PAGE_NUM = 'pdf_page_list'
PARAMETER = 'check_sensor'
THRESHOLD = 'check_threshold'
OPERATOR = 'check_operator'
REPORT_DELAY = 'report_delay'

# REDIS MACRO
DEVICE_LIST = "device_list"
MODEL_LIST = 'model_list'
TIMESTAMP = 'ts'

# API GATEWAY FIELD
POST_DEVICE_ID = 'siteProductSeq'
POST_TITLE = 'keyword'
POST_MESSAGE = 'detailMessage'
POST_URL_PATH = 'urlPath'

# SQL
SELECT_QUERY_ALL_CONTEXT_AWARENESS_CASE = '''
SELECT a.ca_id, a.model_name, a.interval_sec, a.ca_error_case, a.check_sensor, 
a.check_operator, a.check_threshold, a.noti_title, a.noti_description, b.pdf_id, b.pdf_url, a.pdf_page_list 
FROM elesway_dev.t_ca_case a,elesway_dev.t_ca_pdf_info b WHERE a.model_name = b.model_name ORDER BY b.model_name'''

SELECT_QUERY_SPECIFIC_MODEL_CONTEXT_AWARENESS_CASE = '''
SELECT a.ca_id, a.model_name, a.interval_sec, a.ca_error_case, a.check_sensor, 
a.check_operator, a.check_threshold, a.noti_title, a.noti_description, b.pdf_id, b.pdf_url, a.pdf_page_list 
FROM elesway_dev.t_ca_case a,elesway_dev.t_ca_pdf_info b WHERE a.model_name = '{model}' AND a.model_name = b.model_name ORDER BY b.model_name'''


# Logging APIs
def log(req, msg, st):
    log_date = get_log_date()
    log_message = "Info: {0} | {1} | {2} | {3}".format(log_date,
                                                       datetime.datetime.now(timezone("Asia/Seoul")) - st,
                                                       str(req), msg)
    logger_1.info(log_message)


def error_log(req, err_code, msg, st):
    log_date = get_log_date()
    log_message = "Error: {0} | {1} | {2} | {3} | {4}".format(log_date,
                                                              datetime.datetime.now(timezone("Asia/Seoul")) - st,
                                                              str(req), err_code, msg)
    logger_2.error(log_message)


def swagger_log(msg1, msg2, st):
    log_date = get_log_date()
    log_message = "DEBUG: {0} | {1} | {2} | {3}".format(log_date,
                                                        datetime.datetime.now(timezone("Asia/Seoul")) - st,
                                                        msg1, msg2)
    logger_3.debug(log_message)


def get_log_date():
    dt = datetime.datetime.now(timezone("Asia/Seoul"))
    log_date = dt.strftime("%Y-%m-%d %H:%M:%S%f")[:-3]
    return log_date


# Redis APIs
def connect_redis():
    st = datetime.datetime.now(timezone("Asia/Seoul"))
    _host = 'localhost'
    _port = 6379
    _db = 0
    try:
        conn = redis.Redis(host=_host, port=_port, db=_db)
    except Exception as e:
        # print("DB Connection Error : ", e)
        error_log("[{0}]{1}".format("Redis Connect Error", _host + str(_port)),
                  "505",
                  "{0} | {1}".format(_db, e), st)
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
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        try:
            db_conn = pymysql.connect(**CONFIG)
        except Exception as e:
            # print("DB Connect Exception >> ", e)
            error_log("[{0}]{1}".format("MariaDB Connect Error", CONFIG['host'] + str(CONFIG['port'])),
                      "506",
                      "{0}".format(e), st)
            raise e
        return db_conn

    @classmethod
    def select(cls, sql, multi=True):
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        if type(sql) is str:
            try:
                db = MariaDB.connect()
            except Exception as e:
                error_log("[{0}]{1}".format("DB select() Error", sql),
                          "507",
                          "{0}".format(e), st)
            try:
                with db.cursor(DictCursor) as cursor:
                    if cursor.execute(sql):
                        if multi:
                            res = cursor.fetchall()
                            return res
                        elif not multi:
                            res = cursor.fetchone()
                            return res
                    else:
                        return None
            except Exception as e:
                db.rollback()
                error_log("[{0}]{1}".format("DB Select Error", sql),
                          "508",
                          "{0}".format(e), st)
            finally:
                cursor.close()
                db.close()

    @classmethod
    def insert(cls, sql):
        # todo : read 함수의 스키마와 같이 새로운 Raw를 저장할 수 있는 함수.
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        if type(sql) is str:
            try:
                db = MariaDB.connect()
            except Exception as e:
                error_log("[{0}]{1}".format("DB inset() Error", sql),
                          "509",
                          "{0}".format(e), st)
            try:
                with db.cursor(DictCursor) as cursor:
                    cursor.execute(sql)
                db.commit()
            except Exception as e:
                db.rollback()
                error_log("[{0}]{1}".format("DB Insert Error", sql),
                          "510",
                          "{0}".format(e), st)
            finally:
                cursor.close()
                db.close()
        else:
            error_log("[{0}]{1}".format("DB Query Error", sql),
                      "511",
                      "{0}".format("Please, parameter must be String !"), st)


def context_awareness_setting(model=None):
    st = datetime.datetime.now(timezone("Asia/Seoul"))
    try:
        if model is None:
            print("Context Awareness Setting...")
            case = MariaDB.select(SELECT_QUERY_ALL_CONTEXT_AWARENESS_CASE)
        else:
            case = MariaDB.select(SELECT_QUERY_SPECIFIC_MODEL_CONTEXT_AWARENESS_CASE.format(model=model))
        # case = MariaDB.read_test()
    except Exception as e:
        # print("Context Awareness Setting DB Error >> ", e)
        error_log("[{0}]".format("Context Awareness DB Setting Error"),
                  "512",
                  "{0} | {1}".format(model, e), st)
        return False
    if case is not None:
        for _case in case:
            # todo : Fix Please, Table1, Table2 in MariaDB have a equal model_name.
            try:
                """ Hash 형태로 model_list : Model 저장 """
                cache.sadd(MODEL_LIST, _case[MODEL])
                cache.sadd(_case[MODEL], _case[RDB_ID])
                """ Hash 형태로 Model : Config 값 저장 """
                cache.hmset(_case[RDB_ID], _case)
            except Exception as e:
                error_log("[{0}]".format("Context Awareness Cache Setting Error"),
                          "513",
                          "{0} | {1}".format(_case, e), st)
                return False
    else:
        pass
    if model is None:
        print("Setting Finish.")
    return True


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


_st = datetime.datetime.now(timezone("Asia/Seoul"))
# Created Directory
for dir_path in DIRECTORY_PATHS:
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    except OSError:
        error_log("[{0}]".format(dir_path), "514", "Create Error", _st)
time.sleep(1)
# todo : Handler Setting
# log_formatter = logging.Formatter("[%(asctime)s] %(message)s")
time_rotating_file_handler = TimedRotatingFileHandler(SERVICE_LOG_PATH + "/service.log", when="midnight", interval=1)
error_file_handler = logging.FileHandler(ERROR_LOG_PATH + "/error.log")
swagger_file_handler = logging.FileHandler(SWAGGER_LOG_PATH + "/swagger.log")
# time_rotating_file_handler.setFormatter(log_formatter)
# todo : logger Setting
logger_1 = logging.getLogger('1')
logger_1.setLevel(logging.INFO)
logger_1.addHandler(time_rotating_file_handler)
logger_2 = logging.getLogger('2')
logger_2.setLevel(logging.ERROR)
logger_2.addHandler(error_file_handler)
logger_3 = logging.getLogger('3')
logger_3.setLevel(logging.DEBUG)
logger_3.addHandler(swagger_file_handler)
# logging.basicConfig(filename="./flask.log", level=logging.INFO)
time.sleep(1)
# todo : Cache FlushAll !!!
cache = connect_redis()
cache.flushall()
log("Starting Context Aware System", "No Message", _st)
time.sleep(1)
context_awareness_setting()
app = Flask(__name__, template_folder='templates', static_folder='static')
api = Api(app,
          version='0.10',
          title='상황인지 시스템',
          description='<h2 style="background-color: #fde3c9e0">에브리봇 물걸레 청소기 기반 서비스 시나리오.</h1>'
                      '<div style="background-color: #eefdc9e0">case1 : 마지막 주기보고 시각을 기록한 뒤, 일정 시각 경과 후 작동하고 '
                      '내부 batch daemon이 분단위로 체크, 3분 경과시 와이파이 연결 상태 체크 관련 문구 notification 발생.\n'
                      'case2 : RSSI 값을 매회 체크하여 일정 수치 이하로 감소시 작동. 일시적인 하락으로 인한 오탐 방지 로직 검토 진행.\n</div>',
          validate=True,
          default=None)
redis_swagger = api.namespace("Redis",
                       description='<div style="background-color: #dc17171a; text-align: right">저장된 Redis 확인용 APIs 입니다.</div>')
todo = api.model('Todo', {
    'index': fields.Integer(readonly=True, description='HHHHH')
})
app.static_folder = 'static'
# cat_name_space = api.namespace("cats", description='<div style="background-color: #caddff; text-align: right">테스트 API 카테고리 01 입니다.</div>')
# dog_name_space = api.namespace("dogs", description='<div style="background-color: #e0fff9; text-align: right">테스트 API 카테고리 02 입니다.</div>')
# api.default_namespace()
