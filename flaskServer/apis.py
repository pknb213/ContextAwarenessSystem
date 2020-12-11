from importlib.resources import Resource
from utils import *
import csv, datetime, itertools, collections


@app.route('/ping', methods=["POST"])
def ping():
    print("Pong~")
    return Response("200")


@app.route('/', methods=["POST"])
def hello_world():
    raw = request.data.decode("utf-8")
    """ Log 작성 """
    # with open('./http_test.txt', 'a') as fd:
    #     fd.write(str(raw) + "\n")
    """ Key Value Mapping """
    dic = json.loads(raw)
    msg = dic['message']  # Filebeat Format
    res = dict(item.split("=") for item in msg.split("|"))
    del dic["message"]
    """ message key value와 전체 key value 통합 """
    r = dict(res, **dic)

    """ Last Report Timestamp 저장 Device ID : { ts, rssi } """
    if "DEVICE_ID" in r:
        cache.sadd("device_list", r[DEVICE_ID_FIELD])
        cache.hmset(r[DEVICE_ID_FIELD], {'ts': str(datetime.datetime.now().timestamp())})
    """ DB에서 Context Awareness Table 가져와서 감지 """
    if cache.exists(r[MODEL_NAME_FIELD]):
        for case in cache.smembers(r[MODEL_NAME_FIELD]):
            # print(cache.hgetall(case.decode()))
            config_data = cache.hgetall(case.decode())
            decoding_data = {}
            for key, value in config_data.items():
                decoding_data[key.decode("utf-8")] = value.decode("utf-8")
            cal_res = Operator.calculate(decoding_data["operator"], r[decoding_data["param"]], decoding_data["threshold"])
            print("> [", datetime.datetime.now(), "] Calculation [", r[DEVICE_ID_FIELD], decoding_data["param"], "]: ",
                  r[decoding_data["param"]], decoding_data["operator"], decoding_data["threshold"], " is ", cal_res)
            """ Alert Post 전송 """
            if cal_res is True:
                post_alerts(r[DEVICE_ID_FIELD], decoding_data)
    else:
        # todo : 지금 들어온 Raw 데이터에 해당하는 상황인지 설정 값이 없음. 설정 값을 추가 해야함.
        pass

    return Response("200")


@alerts.route("/")
class Alerts(Resource):
    @staticmethod
    def get():
        """ Redis 확인용 """
        print("[GET] Redis Keys")
        keys = cache.keys()
        print(keys)
        for key in keys:
            args = cache.hgetall(key.decode())
            for arg in args:
                print(">>", key.decode(), "|", arg.decode(), ":", cache.hmget(key, arg.decode())[0].decode())
        return str(keys)

    @staticmethod
    def post(device, data):
        """ API G/W로 POST 전달. """
        """ Redis 저장된 설정 정보 읽음."""
        # print(data)
        post_data = {
            "siteProductSeq": device,
            "keyword": data["title"],
            "detailMassge": data["description"],
            "urlPath": LOCAL_URL + "/manual/" + data["pdf_id"] + "?page=" + data["page_num"]
        }
        """ POST API G/W로 전송"""
        # res = sent_api_gw(test_data)
        print(">>", post_data)
        return Response("200")


def sent_api_gw(_dict):
    log(1, "Log Test")
    print("[POST] Sent Dict Test: ", _dict, type(_dict))
    response = requests.post(API_GATEWAY_URL, json=_dict)
    return response


@app.route("/pdfjs")  # todo : /pdfjs -> /<file_name>?page=6 명명 변경   아래꺼 완성 전까지 냅두기
def get():
    page_num = request.args.get('page')
    if page_num is None:
        page_num = 1
    return render_template("index.html",
                           file="http://218.55.23.208:5000/static/pdf_manual_01.pdf",
                           page_num=page_num)


@app.route("/manual/<filename>")  # todo :  API
def get2(filename):
    page_num = request.args.get('page')
    if page_num is None:
        page_num = 1
    return render_template("index.html",
                           file=LOCAL_URL + "/static/" + filename,
                           page_num=page_num)
