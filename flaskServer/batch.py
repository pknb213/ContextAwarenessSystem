import datetime, random
from utils import cache
from apscheduler.schedulers.background import BackgroundScheduler
from apis import *


def batch_daemon():
    print("\n> ", datetime.datetime.now(), "Batch Daemon")
    print("Models : ", cache.smembers("model_list"))
    print("Devices : ", cache.smembers("device_list"))
    devices = cache.smembers("device_list")
    devices = list(map(lambda x: x.decode(), devices))
    # todo : Delay Check


def detected_report_time(device, ts):
    if ts is False:
        return False
    if datetime.datetime.now().timestamp() - float(ts) > 30:
        """ Alert to Server """
        pass


# Todo : 나중에 삭제할 함수, 가짜 데이터 전송.
def fake_post():
    test = {
        "MOTOR_RPM": "1040",
        "AP_RSSI": str(random.randint(-70, -20)),
        "DEVICE_ACTION_STATUS": "00000000",
        "DEVICE_TYPE_NAME": "공기청정기",
        "tags": [
            "beats_input_codec_plain_applied"
        ],
        "DEVICE_GPS": "37.4858768,126.8931144",
        "INTERLOCK_TIME": "20200727130329",
        "MODEL_NAME": random.choice(["CT_MODEL_02", "CT_MODEL_01"]),
        "POWER": "1",
        "DEVICE_MENU_CODE": "1",
        "PROTOCOL_VERSION": "95",
        "PM2.5_2": "1",
        "SITE_ID": "547",
        "LOG_DATA_TYPE": "1",
        "DEVICE_ERROR_CODE": "[B@124002b9",
        "REQ_TIME": "20200821101623",
        "PM1.0_2": "1",
        "TVOC": "156",
        "DEVICE_TYPE_CODE": "6085",
        "AP_SSID": "TLG2G",
        "SERIAL_NUM": "010101",
        "LCD_STATUS": "0",
        "DEVICE_GPS_LONG": "126.8931144",
        "PM10": str(random.randint(20, 60)),
        "HUMIDITY": "70",
        "COVER_FRONT": "0",
        "RUN_TIME": "2687",
        "MAC_ADDRESS": "B0:F8:93:73:96:51",
        "TEMPERATURE": "25",
        "@version": "1",
        "SITE_NAME": "유비벨록스 모바일 TLG",
        "PRODUCTER_ID": "19",
        "offset": 1336796,
        "DEVICE_GPS_LAT": "37.4858768",
        "AUTO_MODE": "1",
        "source": "/svc/elesway/logs/bigData/iot/ct/cafu15/service.log",
        "TOTAL_RUN_TIME": "51436",
        "input": {
            "type": "log"
        },
        "DEVICE_ID": str(random.randint(285, 290)),
        "PM1.0": str(random.randint(20, 60)),
        "PM10_2": "1",
        "PM2.5": "21",
        "prospector": {
            "type": "log"
        },
        "MANUFACTURER_COUNTRY": "2",
        "beat": {
            "hostname": "research2",
            "name": "research2",
            "version": "6.3.2"
        },
        "USER_OWNER_DEVICE": "0",
        "@timestamp": str(datetime.datetime.now()),
        "CONTROL_TYPE": "0",
        "host": {
            "name": "research2"
        },
        "message": "PURCHASE_ROUTE=|USER_ID=|OWNER_AGE=|SITE_NAME=유비벨록스 모바일 TLG|TOTAL_RUN_TIME=51436|OWNER_ID=|MAC_ADDRESS=B0:F8:93:73:96:51|MODEL_COLOR=|DEVICE_CONTROL_GPS=|LCD_STATUS=0|DEVICE_GPS_LAT=37.4858768|PRODUCTER_ID=19|DEVICE_CONTROL_GPS_LAT=|USER_OWNER_DEVICE=0|PM1.0=19|PM2.5_2=1|MODEL_NAME=CT_MODEL_01|REQ_TIME=20200821101623|DEVICE_CONTROL_GPS_LONG=|AP_LQI=|DEVICE_GPS=\"37.4858768,126.8931144\"|INTERLOCK_TIME=20200727130329|RUN_TIME=2687|DEVICE_ACTION_STATUS=00000000|DEVICE_TYPE_NAME=공기청정기|USER_AGE=|DEVICE_ID=285|AP_RSSI=-61|DEVICE_TYPE_CODE=6085|USER_PHONE_MODEL=|LOG_DATA_TYPE=1|PRODUCTER_NAME=|AP_SSID=TLG2G|DEVICE_MENU_CODE=1|SERIAL_NUM=010101|TEMPERATURE=25|PROTOCOL_VERSION=95|PM1.0_2=1|PM2.5=21|PM10_2=1|CONTROL_TYPE=0|MANUFACTURER_COUNTRY=2|MANUFACTURER_FACTORY=|HUMIDITY=70|SITE_ID=547|POWER=1|OWNER_GENDER=|MANUFACTURER_DATE=|DEVICE_NICK_NAME=|AUTO_MODE=1|COVER_FRONT=0|USER_GENDER=|FIRMWAER_VERSION=31|PURCHAGE_TIME=|TVOC=156|DEVICE_GPS_LONG=126.8931144|DEVICE_ERROR_CODE=[B@124002b9|MODEL_NAME_SUB=|MOTOR_RPM=1040|PM10=26|DEVICE_LOCATION_NICK_NAME=",
        "service": "ct-cafu15",
        "FIRMWAER_VERSION": "31"
    }
    requests.post(LOCAL_URL, json=test)


""" APSecheduler : https://apscheduler.readthedocs.io/en/latest/userguide.html 
    Bug : Flask Debug Mode is Twice execution. Because re-loader.
    'date' : once specific datetime execution 
    'interval' : static time range execution
    'cron' : Today specific time execution """
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(batch_daemon, 'interval', seconds=20, id='batch_daemon_job')
scheduler.add_job(fake_post, 'interval', seconds=5, id='fake_post_job')
scheduler.start()
