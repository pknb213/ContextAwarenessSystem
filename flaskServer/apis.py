from importlib.resources import Resource
from utils import *
import csv, datetime, itertools, collections

model_rawdata = api.model('raw_data', {
   'id': fields.Integer(readOnly=True, required=True, desciption='데이터 고유 값', help="필요합니다"),
})


@app.route('/pint', methods=["POST"])
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
    msg = dic['message']
    res = dict(item.split("=") for item in msg.split("|"))
    # print(dic.keys(), type(dic), len(dic), "\n", res.keys(), type(res), len(res))
    del dic["message"]
    """ message key value와 전체 key value 통합 """
    r = dict(res, **dic)
    """ Redis Hash 형태로 저장 """
    if "DEVICE_ID" in r:
        conn.hmset(r["DEVICE_ID"], {'ts': str(datetime.datetime.now().timestamp()), 'rssi': r['AP_RSSI']})
    elif "deviceId" in r:
        conn.hmset(r["deviceId"], {'ts': str(datetime.datetime.now().timestamp()), 'rssi': r['rssi']})

    """ DB에서 Context Awareness Table 가져와서 감지 """
    if conn.exists(r["MODEL_NAME"]):
        res = conn.hmget(r["MODEL_NAME"], "param", "operator", "threshold")
        params, comparison_operator, threshold = list(map(lambda x: x.decode(), res))
        res = Operator.calculate(comparison_operator, r[params], threshold)
        print("Calculation : ", r[params], comparison_operator, threshold, " is ", res)
        """ Alert Post 전송 """
        if res is True:
            # Alerts.post()
            pass
    else:
        # todo : 지금 들어온 Raw 데이터에 해당하는 상황인지 설정 값이 없음. 설정 값을 추가 해야함.
        pass

    if conn.exists(r["modelName"]):
        print("존재함")

    return Response("200")


# Test Route
@alerts.route("/")
class Alerts(Resource):
    @staticmethod
    def get():
        """ Redis 확인용 """
        print("[GET] Redis Keys")
        keys = conn.keys()
        # print(keys)
        for key in keys:
            args = list(conn.hgetall(key))
            # print(args, type(args))
            for arg in args:
                print(">>", key.decode(), "|", arg.decode(), ":", conn.hmget(key, arg.decode())[0].decode())

        return str(keys)

    @staticmethod
    def post():
        """ API G/W로 POST 전달. """
        test_data = {
            "siteProductSeq": "346",
            "keyword": "WiFi 이상 감지",
            "detailMassge": "WiFi 수신 감도가 너무 낮습니다.",
            "urlPath": "http://218.55.23.208:5000/pdfjs?page=3"
        }
        # DB 테이블 손수 넣어야됨.

        res = sent_api_gw(test_data)
        print(res)
        return Response("200")


def sent_api_gw(_dict):
    log(1, "Log Test")
    print("[POST] Sent Dict Test: ", _dict, type(_dict))
    response = requests.post(API_GATEWAY_URL, json=_dict)
    return response


@app.route("/get_test/lg")   # todo : Test 용도 삭제 예정
def get_test2():
    print("[GET] PDF Test")
    return send_from_directory(directory="./pdfs",
                               filename="LG-F700_UG_281.0_29_20161025.pdf",
                               mimetype="application/pdf",
                               as_attachment=False)


@app.route("/pdfjs")   # todo : /pdfjs -> /<file_name>&page=6 명명 변경   아래꺼 완성 전까지 냅두기
def get():
    page_num = request.args.get('page')
    if page_num is None:
        page_num = 1
    return render_template("index.html",
                           file="http://218.55.23.208:5000/static/pdf_manual_01.pdf",
                           page_num=page_num)


@app.route("/<filename>")   # todo : 혼모노 API
def get2(filename):
    filename = filename
    print("Test >>> ", filename)
    page_num = request.args.get('page')
    if page_num is None:
        page_num = 1
    return render_template("index.html",
                           file="http://218.55.23.208:5000/static/" + filename,
                           page_num=page_num)


abnormal_model = alerts.model('Model', {
    'url': fields.Url('todo_ep'),
    'key': fields.String,
    'value': fields.String,
    'device_id': fields.String,
    'timestamp': fields.Integer
})


@cat_name_space.route('/info')
class HelloRedis(Resource):
    @staticmethod
    def get():
        '''Redis Information 조회'''
        return info_redis()


@cat_name_space.route('/test/<string:todo_id>')
class TodoTest(Resource):
    @staticmethod
    def get(todo_id):
        '''Hello Get URL Parameter Test'''
        print("Hello~", todo_id)
        return Response("200")


@dog_name_space.route('/mail')
class Email(Resource):
    @staticmethod
    def get():
        '''Email 전송 테스트 API'''
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login('pknb321@gmail.com', "12281228a!")
        msg = MIMEMultipart()
        msg['Subject'] = 'Email Test Test Test'
        part = MIMEText('SMTP Email Body')
        msg.attach(part)
        msg['To'] = 'pknb213@naver.com'
        smtp.sendmail('pknb321@gmail.com', 'pknb213@naver.com', msg.as_string())

        return Response("200")
