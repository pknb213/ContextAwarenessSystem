from importlib.resources import Resource
from utils import *
import csv, datetime, itertools, collections

# DATA FIELD MACRO
SERVICE = 'service'
MESSAGE_FIELD = 'message'


@app.route('/ping', methods=["POST"])
def ping():
    print("Pong~")
    return Response("200")


@app.route('/', methods=["POST"])
def get_data():
    # print(">>", request.data.decode("utf-8"))
    st = datetime.datetime.now(timezone("Asia/Seoul"))
    data_field_dic = {"DEVICE_ID_FIELD": "", "MODEL_NAME_FIELD": "", "RSSI": "", "REQ_TIME": "",
                      "FRONT_COVER": "", "PM1DOT0": ""}
    service = ""
    dic = {}
    try:
        raw = request.data.decode("utf-8")
        """ Key Value Mapping """
        dic = json.loads(raw)
        if 'service' not in dic:
            dic['service'] = service
        else:
            service = dic['service']
        data_field_dic = change_field_name(service, data_field_dic)
        # todo : test code
        if "service" in dic:
            print("> [IN {0}] [{1} {2}]".format(st, dic[data_field_dic["MODEL_NAME_FIELD"]], dic[data_field_dic["DEVICE_ID_FIELD"]]))
        # todo : Grip Message 안에 resource=[{...}] 형태가 있기 때문에 제거 해야함. 그립을 상황인지하려면 여기에 매핑추가
        if service == G100SR:
            return Response('200')
        log("[{0}]{1}".format(request.method, request.url),
            "Model: {0} | Device: {1}".format(dic[data_field_dic["MODEL_NAME_FIELD"]],
                                              dic[data_field_dic["MODEL_NAME_FIELD"]]))
    except Exception as e:
        error_log(request.url, "501", "{0} | {1} | {2} | {3}".format(service,
                                                                     dic,
                                                                     data_field_dic["MODEL_NAME_FIELD"],
                                                                     e), st)
    """ Last Report Timestamp 저장 Device ID : { ts, rssi } """
    try:
        # print(r[SERVICE], r[DEVICE_ID_FIELD], r[MODEL_NAME_FIELD])
        if data_field_dic["DEVICE_ID_FIELD"] in dic:
            cache.sadd(DEVICE_LIST, dic[data_field_dic["DEVICE_ID_FIELD"]])
            cache.hmset(dic[data_field_dic["DEVICE_ID_FIELD"]],
                        {TIMESTAMP: str(datetime.datetime.now().timestamp()),
                         MODEL: dic[data_field_dic["MODEL_NAME_FIELD"]]})
        """ DB에서 Context Awareness Table 가져와서 감지 """
        if cache.exists(dic[data_field_dic["MODEL_NAME_FIELD"]]):
            for case in cache.smembers(dic[data_field_dic["MODEL_NAME_FIELD"]]):
                # print(cache.hgetall(case.decode()))
                config_data = cache.hgetall(case.decode())
                decoding_data = {}
                for key, value in config_data.items():
                    decoding_data[key.decode()] = value.decode()
                if decoding_data[PARAMETER] != 'report_delay':
                    cal_res = Operator.calculate(decoding_data[OPERATOR], dic[decoding_data[PARAMETER]],
                                                 decoding_data[THRESHOLD])
                    # print("[GET] >", datetime.datetime.now(), "[ Calculation ", r[MODEL_NAME_FIELD], r[DEVICE_ID_FIELD], "]: ", decoding_data[PARAMETER],
                    #       r[decoding_data[PARAMETER]], decoding_data[OPERATOR], decoding_data[THRESHOLD], " is ", cal_res)
                    """ Alert Post 전송 """
                    if cal_res is True:
                        et = datetime.datetime.now().timestamp()
                        post_alerts(dic[data_field_dic["DEVICE_ID_FIELD"]], decoding_data,
                                    "Model: {0} | Device: {1} | Keyword: {2}".format(
                                        dic[data_field_dic["MODEL_NAME_FIELD"]],
                                        dic[data_field_dic["DEVICE_ID_FIELD"]],
                                        decoding_data[PARAMETER]), st)
                else:
                    """ 주기보고 case는 여기서 안함 """
                    pass
        else:
            """ Device Model 에 해당하는 Case가 Cache에 없으면 DB에서 가져오기 """
            model = cache.hget(dic[data_field_dic["MODEL_NAME_FIELD"]], MODEL)
            """ 해당 모델의 정보가 없을 때, DB 에서 Cache 에 저장 """
            if model is None:
                pass
            elif cache.exists(model):
                if context_awareness_setting(model=model.decode()):
                    pass
                else:
                    pass
            else:
                pass
    except Exception as e:
        error_log("[{0}]{1}".format(request.method, request.url),
                  "502",
                  "{0} | {1} | {2} | {3}".format(service,
                                                 dic,
                                                 data_field_dic["MODEL_NAME_FIELD"],
                                                 e), st)
        # print("GET Cache Error", e)
    return Response("200")


@app.route("/posts/alerts", methods=["POST"])
def post_alerts(device, data, log_msg, st, batch=False):
    """ API G/W로 POST 전달. """
    """ Redis 저장된 설정 정보 읽음."""
    if batch is False:
        log("[{0}] {1}".format(request.method, request.url), log_msg, st)
    else:
        log("[{0}] {1}".format("POST", LOCAL_URL), log_msg, st)
    # Chungwu primary key not equal egg primary key.
    if device == "23065":
        device = "388"
    elif device == "23012":
        pass
    elif device == "22998":
        device = "389"
    post_data = {
        POST_DEVICE_ID: device,
        POST_TITLE: data[TITLE],
        POST_MESSAGE: data[DESCRIPTION],
        POST_URL_PATH: LOCAL_URL + "/manuals/" + data[PDF_NAME] + "?page=" + data[PAGE_NUM]
    }
    """ POST API G/W로 전송"""
    if device == "388" or device == "23012" or device == "389":
        # Todo : Test를 위해 잠시 꺼둠
        res = sent_api_gw(post_data)
        print(">>>", res, "[POST API G/W]")
    # res = sent_api_gw(post_data)
    # print("[POST] >>", post_data)
    return Response("200")


def sent_api_gw(_dict):
    # print("[POST] Sent Dict Test: ", _dict, type(_dict))
    response = requests.post(API_GATEWAY_URL, json=_dict)
    return response


# todo : Rendering Page APIs
@app.route("/manuals/<filename>")
def view_pdf(filename):
    page_num = request.args.get(PDF_PAGE_PARAMETER)
    if page_num is None:
        page_num = [1]
    else:
        page_num = list(map(lambda x: int(x), page_num.split("|")))
    # print("GET PDF : ", filename, page_num)
    return render_template("pdf_viewer.html",
                           file=LOCAL_URL + "/static/" + filename,
                           page_num=page_num,
                           title=filename)


# todo : Test Code 입니다.
@app.route("/pdfjs")
def get():
    print("GET PDF : TEST PAGE")
    page_num = request.args.get(PDF_PAGE_PARAMETER)
    if page_num is None:
        page_num = 1
    return render_template("pdf_viewer.html",
                           file="http://218.55.23.208:5000/static/3i_users_guide.pdf",
                           page_num=[2, 4, 7],
                           title="3i_users_guide.pdf")


# todo : Swagger API
@redis_swagger.route("/")
class Redis_swagger(Resource):
    @staticmethod
    def get():
        """ Redis 모든 Keys Dictionary 출력 """
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        print("[GET] Redis Keys")
        keys = cache.keys()
        print(keys)
        res = {"keys": keys}
        try:
            for key in keys:
                key_type = cache.type(key).decode()
                if key_type == 'set':
                    # print(">>", key.decode(), "|", cache.smembers(key))
                    res[key.decode()] = cache.smembers(key)
                elif key_type == 'hash':
                    args = cache.hgetall(key)
                    for arg in args:
                        # print(">>", key.decode(), "|", arg.decode(), ":", cache.hmget(key, arg.decode())[0].decode())
                        res[key.decode()] = {
                            arg.decode(): cache.hmget(key, arg.decode())[0].decode()
                        }
                else:
                    print("KeyType Error : {}".format(key_type))
                    pass
        except Exception as e:
            error_log("[{0}]{1}".format(request.method, request.url),
                      "503",
                      "{0} | {1}".format("Swagger Error", e), st)
        # print(res)
        swagger_log("[GET] : / ", res, st)
        return Response(json.dumps(res), status="200")

    @staticmethod
    def post():
        """ Server Close Api """
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        print("Server Closing... Please wait a pew second...")
        log("Closing Context Aware System", "No Error", st)
        swagger_log("[POST] : /", "Call Server Close Api", st)
        time.sleep(2)
        return sys.exit(0)


@redis_swagger.route('/device/list')
class Redis_All_Device_List(Resource):
    @staticmethod
    def get():
        """ 모든 Device List 출력 """
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        print("[GET] Redis Device list")
        res = {DEVICE_LIST: list(map(lambda x: x.decode(), cache.smembers(DEVICE_LIST)))}
        swagger_log("[GET] : /device/list", res, st)
        return Response(json.dumps(res), status="200")


@redis_swagger.route('/device/list/<int:index>')
class Redis_Model_Device_List(Resource):
    @staticmethod
    def get(index):
        """ 모든 Device List 출력 """
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        index_model = "HA-831" if index == 1 else "RS300"
        res = {}
        print("[GET] Redis Device list by model")
        for device in list(map(lambda x: x.decode(), cache.smembers(DEVICE_LIST))):
            if cache.hmget(device, MODEL)[0].decode() == index_model:
                ts = float(cache.hget(device, TIMESTAMP).decode())
                KST = datetime.timezone(datetime.timedelta(hours=9))
                ts_interval = datetime.datetime(datetime.datetime.now(timezone('Asia/Seoul')).year,
                                                datetime.datetime.now(timezone('Asia/Seoul')).month,
                                                datetime.datetime.now(timezone('Asia/Seoul')).day,
                                                0, 0, 0, tzinfo=KST) - datetime.datetime.fromtimestamp(ts, tz=KST)
                if ts_interval.days >= 1:
                    ts_interval = str(ts_interval.days) + " days ago"
                elif ts_interval.days <= 0:
                    ts_interval = str(ts_interval.min) + " minutes ago"
                else:
                    ts_interval = str(ts_interval.seconds) + " seconds ago"
                res[device] = [datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"), ts_interval]
        swagger_log("[GET] : /device/list/" + index_model + " | Device : [last date stamp]", res, st)
        return Response(json.dumps(res), status="200")


@redis_swagger.route('/device/list/<int:index>/yesterday')
@redis_swagger.response(200, 'Found')
@redis_swagger.param('index', 'Index ID')
class Redis_Yesterday_Model_Device_List(Resource):
    @staticmethod
    @redis_swagger.doc('get_todo')
    @redis_swagger.marshal_with(todo)
    def get(index):
        """ 모든 Device List 출력 """
        st = datetime.datetime.now(timezone("Asia/Seoul"))
        index_model = "HA-831" if index == 1 else "RS300"
        res = []
        print("[GET] Redis Device list by model")
        for device in list(map(lambda x: x.decode(), cache.smembers(DEVICE_LIST))):
            if cache.hmget(device, MODEL)[0].decode() == index_model:
                ts = float(cache.hget(device, TIMESTAMP).decode())
                KST = datetime.timezone(datetime.timedelta(hours=9))
                ts_interval = datetime.datetime(datetime.datetime.now(timezone('Asia/Seoul')).year,
                                                datetime.datetime.now(timezone('Asia/Seoul')).month,
                                                datetime.datetime.now(timezone('Asia/Seoul')).day,
                                                0, 0, 0, tzinfo=KST) - datetime.datetime.fromtimestamp(ts, tz=KST)
                # print(">>>>", device, datetime.datetime.fromtimestamp(ts, tz=KST), ts_interval, ts_interval.days)
                if ts_interval.days <= -1:
                    res.append(device)
        swagger_log("[GET] : /device/list/" + index_model + " | Device : [last date stamp]", res, st)
        return Response(json.dumps(res), status="200")


def change_field_name(service, data_dic):
    if service == RA1000:
        data_dic["DEVICE_ID_FIELD"] = 'deviceId'
        data_dic["MODEL_NAME_FIELD"] = 'modelName'
        data_dic["REQ_TIME"] = 'reqTime'
        data_dic["RSSI"] = 'rssi'
    elif service == RS900:
        data_dic["DEVICE_ID_FIELD"] = 'deviceId'
        data_dic["MODEL_NAME_FIELD"] = 'modelName'
        data_dic["REQ_TIME"] = 'reqTime'
        data_dic["RSSI"] = 'rssi'
    elif service == HA831 or service == HA830:
        data_dic["DEVICE_ID_FIELD"] = 'deviceId'
        data_dic["MODEL_NAME_FIELD"] = 'modelName'
        data_dic["RSSI"] = 'rssi'
        data_dic["REQ_TIME"] = 'reqTime'
        data_dic["FRONT_COVER"] = 'front'
        data_dic["PM1DOT0"] = 'pm1dot0'
    elif service == CAFU15:
        data_dic["DEVICE_ID_FIELD"] = 'DEVICE_ID'
        data_dic["MODEL_NAME_FIELD"] = 'MODEL_NAME'
        data_dic["RSSI"] = 'AP_RSSI'
        data_dic["REQ_TIME"] = 'REQ_TIME'
        data_dic["FRONT_COVER"] = 'COVER_FRONT'
        data_dic["PM1DOT0"] = 'PM1.0'
    elif service == G100SR:
        data_dic["DEVICE_ID_FIELD"] = 'deviceId'
        data_dic["MODEL_NAME_FIELD"] = 'modelName'
        data_dic["REQ_TIME"] = 'reqTime'
    elif service == RS300:
        data_dic["DEVICE_ID_FIELD"] = 'DEVICE_ID'
        data_dic["MODEL_NAME_FIELD"] = 'MODEL_NAME'
        data_dic["RSSI"] = 'AP_RSSI'
        data_dic["REQ_TIME"] = 'REQ_TIME'
    else:
        return data_dic
    return data_dic
