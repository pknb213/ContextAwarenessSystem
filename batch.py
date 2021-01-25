from utils import *
from apis import *
from apscheduler.schedulers.background import BackgroundScheduler


def batch_daemon():
    # print("\n", datetime.datetime.now(), "[ Batch Daemon ]")
    # print("Models : ", cache.smembers(MODEL_LIST))
    # print("Devices : ", cache.smembers(DEVICE_LIST))
    st = datetime.datetime.now(timezone("Asia/Seoul"))
    models = cache.smembers(MODEL_LIST)
    devices = cache.smembers(DEVICE_LIST)
    log("[{0}]".format("Batch"), "Detecting_Models: {0} | Connected_Devices: {1}".format(models, devices), st)
    device_report_time_log_dic = {}
    if len(devices):
        devices = list(map(lambda x: x.decode(), devices))
        for device in devices:
            model = "None"
            try:
                """ Report Delay Calculation """
                ts_interval = datetime.datetime.now().timestamp() - float(cache.hget(device, TIMESTAMP).decode())
                # print(">>", device, cache.hget(device, 'ts').decode(), ts_interval)
                ts_and_interval = [str(round(ts_interval)) + " seconds ago"]
                """ Device Model에 해당하는 Case가 Cache에 없으면 DB에서 가져오기 """
                model = cache.hget(device, MODEL).decode()
                """ 해당 모델의 정보가 없을 때, DB 에서 Cache 에 저장 """
                if not cache.exists(model):
                    context_awareness_setting(model=model)
                """ Alert Transmission """
                cases = list(map(lambda x: x.decode(), cache.smembers(model)))
                config_data = {}
                for case in cases:
                    keyword = cache.hget(case, PARAMETER).decode()
                    if keyword == REPORT_DELAY:
                        for key, value in cache.hgetall(case).items():
                            config_data[key.decode()] = value.decode()
                    else:
                        # Except Report delay, context awareness cases.
                        pass
                if REPORT_INTERVAL in config_data:
                    ts_and_interval.append(config_data[REPORT_INTERVAL])
                    # print(">", model, device, ts_and_interval)
                    # todo : 주기보고 딜레이 전송.
                    # if 뒤에 600s 이상안오면 안보내는 로직을 변경해야 함. Flag etc . . .
                    if int(config_data[REPORT_INTERVAL]) <= ts_interval:  # <= 600 계속 안보내게 하려면 추가
                        # todo : Alert 전송 및 Redis 전송 Count 증가. (Count = Dynamic Value)
                        post_alerts(device, {
                            TITLE: config_data[TITLE],
                            DESCRIPTION: config_data[DESCRIPTION] + "- {}s 지연".format(str(round(ts_interval))),
                            PDF_NAME: config_data[PDF_NAME],
                            PAGE_NUM: config_data[PAGE_NUM]
                        }, "Model: {0} | Device: {1} | Keyword: {2}".format(model, device, "Report Delay"), st, batch=True)
                        # Delete Device Information 
                        # Todo : 계속 안보내는 용도
                        cache.delete(device)
                        cache.srem(DEVICE_LIST, device)
                    else:
                        # Empty the Delay Report.
                        pass
                else:
                    # REPORT_INTERVAL column is not existed.
                    ts_and_interval.append("Config None")
                    pass
                device_report_time_log_dic[model + "|" + device] = ts_and_interval
            except Exception as e:
                error_log("[{0}]{1}".format(request.method, request.url),
                          "504",
                          "{0} | {1} | {2}".format(device, model, e), st)
    else:
        # Empty the Device.
        pass
    log("[Batch']", "Device: [Recently Report Time, Delay Config Value]" +
        str(device_report_time_log_dic), st)


""" APSecheduler : https://apscheduler.readthedocs.io/en/latest/userguide.html 
    Bug : Flask Debug Mode is Twice execution. Because re-loader.
    'date' : once specific datetime execution 
    'interval' : static time range execution
    'cron' : Today specific time execution """
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(batch_daemon, 'interval', seconds=10, id='batch_daemon_job')
# scheduler.add_job(fake_post, 'interval', seconds=5, id='fake_post_job')
scheduler.start()
