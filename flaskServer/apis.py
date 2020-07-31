from utils import *
import csv, datetime, itertools, collections


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

    conn.hmset(r["DEVICE_ID"], {'ts': str(datetime.datetime.now().timestamp()),
               'rssi': r['AP_RSSI']})

    return Response("200")


@api.route('/info')
class HelloRedis(Resource):
    @staticmethod
    def get():
        """Redis Information 조회"""
        return info_redis()


@api.route('/test/<string:todo_id>')
class TodoTest(Resource):
    @staticmethod
    def get(todo_id):

        return Response("200")

