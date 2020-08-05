from importlib.resources import Resource

from utils import *
import csv, datetime, itertools, collections

model_rawdata = api.model('raw_data', {
   'id': fields.Integer(readOnly=True, required=True, desciption='데이터 고유 값', help="필요합니다"),
})


@app.route('/', methods=["POST"])
def hello_world():
    raw = request.data.decode("utf-8")
    # 파일 쓰기
    with open('./http_test.txt', 'a') as fd:
        fd.write(str(raw) + "\n")
    dic = json.loads(raw)

    msg = dic['message']
    res = dict(item.split("=") for item in msg.split("|"))
    # print(dic.keys(), type(dic), len(dic), "\n", res.keys(), type(res), len(res))
    del dic["message"]
    # # 키 값 유지
    # r = collections.defaultdict(list)
    # for k, v in itertools.chain(dic.items(), res.items()):
    #     r[k].append(v)
    # del r["message"]
    # print(r, type(r), len(r))

    # res.update(dic)
    r = dict(res, **dic)

    conn.hmset(r["DEVICE_ID"], {'ts': str(datetime.datetime.now().timestamp()),'rssi': r['AP_RSSI']})

    return Response("200")


abnormal_model = abnormal_ns.model('Model', {
    'url': fields.Url('todo_ep'),
    'key': fields.String,
    'value': fields.String,
    'device_id': fields.String,
    'timestamp': fields.Integer
})


@abnormal_ns.route('/')
class Abnormal(Resource):
    @staticmethod
    def get():
        """ 없음 """
        return Response("200")

    @staticmethod
    @abnormal_ns.marshal_with(abnormal_model)
    def post():
        """ 없음 """
        return Response("200")

    @staticmethod
    def put():
        """ 없음 """
        return Response("200")

    @staticmethod
    def delete():
        """ 없음 """
        return Response("200")


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
