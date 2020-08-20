import datetime
from utils import conn
from apscheduler.schedulers.background import BackgroundScheduler
from apis import *


def heartbeat():
    """ Heartbeat Test API """
    print("\n> Still alive!", datetime.datetime.now(), datetime.datetime.now().timestamp())
    """ Device Scan Start """
    init = 0  # cursor 값, scan 시작 값
    devices = []
    while True:
        scan_res = conn.scan(init)
        init = scan_res[0]  # 이어지는 scan 명령에 사용할 cursor 값
        for key in scan_res[1]:
            devices.append(key)
        if init == 0:  # 반환된 cursor 값이 0이면 스캔 종료
            break

    """ Device Scan Finish """
    for device in devices:
        res = conn.hmget(device.decode(), "ts", "rssi")
        # print("Device ID :", device.decode(), "| Timestamp :", res[0].decode(), "| RSSI :", res[1].decode(),
        #       "Recently Report Time Gap(s) :", datetime.datetime.now().timestamp() - float(res[0].decode()))
        print("Test : ", device, " | ", conn.hgetall(device), " | ", round(datetime.datetime.now().timestamp() - float(res[0].decode())))
        detected_report_time(device, res[0].decode())


def detected_report_time(device, ts):
    if ts is False:
        return False
    if datetime.datetime.now().timestamp() - float(ts) > 30:
        """ Alert to Server """
        # print("Report Interval is Very Long")
        pass


""" APSecheduler : https://apscheduler.readthedocs.io/en/latest/userguide.html 
    Bug : Flask Debug Mode is Twice execution. Because re-loader.
    'date' : once specific datetime execution 
    'interval' : static time range execution
    'cron' : Today specific time execution """
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(heartbeat, 'interval', seconds=10, id='heartbeat_job')
scheduler.start()
