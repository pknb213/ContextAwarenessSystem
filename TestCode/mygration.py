# import argparse
# from influxdb import InfluxDBClient
#
#
# def main(host='localhost', port=8086):
#     """Instantiate a connection to the InfluxDB."""
#     user = 'root'
#     password = 'root'
#     dbname = 'example'
#     dbuser = 'smly'
#     dbuser_password = 'my_secret_password'
#     query = 'select Float_value from cpu_load_short;'
#     query_where = 'select Int_value from cpu_load_short where host=$host;'
#     bind_params = {'host': 'server01'}
#     json_body = [
#         {
#             "measurement": "cpu_load_short",
#             "tags": {
#                 "host": "server01",
#                 "region": "us-west"
#             },
#             "time": "2009-11-10T23:00:00Z",
#             "fields": {
#                 "Float_value": 0.64,
#                 "Int_value": 3,
#                 "String_value": "Text",
#                 "Bool_value": True
#             }
#         }
#     ]
#
#     client = InfluxDBClient(host, port, user, password, dbname)
#
#     print("Create database: " + dbname)
#     client.create_database(dbname)
#
#     print("Create a retention policy")
#     client.create_retention_policy('awesome_policy', '3d', 3, default=True)
#
#     print("Switch user: " + dbuser)
#     client.switch_user(dbuser, dbuser_password)
#
#     print("Write points: {0}".format(json_body))
#     client.write_points(json_body)
#
#     print("Querying data: " + query)
#     result = client.query(query)
#
#     print("Result: {0}".format(result))
#
#     print("Querying data: " + query_where)
#     result = client.query(query_where, bind_params=bind_params)
#
#     print("Result: {0}".format(result))
#
#     print("Switch user: " + user)
#     client.switch_user(user, password)
#
#     print("Drop database: " + dbname)
#     client.drop_database(dbname)
#
#
# def parse_args():
#     """Parse the args."""
#     parser = argparse.ArgumentParser(
#         description='example code to play with InfluxDB')
#     parser.add_argument('--host', type=str, required=False,
#                         default='localhost',
#                         help='hostname of InfluxDB http API')
#     parser.add_argument('--port', type=int, required=False, default=8086,
#                         help='port of InfluxDB http API')
#     return parser.parse_args()
#
#
# if __name__ == '__main__':
#     args = parse_args()
#     main(host=args.host, port=args.port)

import argparse
from pprint import pprint
import pandas as pd
import json, datetime, os, time
from influxdb import DataFrameClient
import multiprocessing as mp
import numpy as np
import pymongo
import pymysql
from sqlalchemy import create_engine

pymysql.install_as_MySQLdb()
engine = create_engine("mysql+mysqldb://user:"+"1234"+"@localhost/test", encoding='utf-8')
conn = engine.connect()

numCores = mp.cpu_count()

INTERNAL_DATABASE = True
DictCursor = pymysql.cursors.DictCursor


class MySQL:
    @staticmethod
    def connect():
        if INTERNAL_DATABASE:
            db = pymysql.connect(
                host='localhost',
                port=3306,
                user="user",
                password="1234",
                db="testdb",
                charset='utf8'
            )
        else:
            db = pymysql.connect(
                host='',
                port=0,
                user="",
                password="",
                db="",
                charset="utf8"
            )
        return db

    @classmethod
    def select(cls, __str, multi=True):
        if type(__str) is str:
            try:
                db = MySQL.connect()
                with db.cursor(DictCursor) as cursor:
                    sql = __str
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
                print("Select Error", e)
                raise e
            finally:
                cursor.close()
                db.close()
        else:
            raise Exception("Please, parameter must be String")

    @classmethod
    def insert(cls, __str):
        if type(__str) is str:
            try:
                db = MySQL.connect()
                with db.cursor(DictCursor) as cursor:
                    sql = __str
                    cursor.execute(sql)
                db.commit()
                return False if cursor.lastrowid == 0 else True
            except Exception as e:
                print("Insert Error", e)
                raise e
            finally:
                cursor.close()
                db.close()
        else:
            raise Exception("Please, parameter must be String !")


def parallel_dataframe(df, func):
    df_split = np.array_split(df, numCores)
    pool = mp.Pool(numCores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


def multiply_columns(data):
    print('PID :', os.getpid())
    data['length_of_word'] = data['species'].apply(lambda x : len(x))
    return data


def connect_mongo(host, port, user, pwd, db):
    if user and pwd:
        mongo_url = "mongodb://%s:%s@%s:%s/%s" % (user, pwd, host, port, db)
        conn = pymongo.MongoClient(mongo_url)
    else:
        conn = pymongo.MongoClient(host, port)

    return conn[db]


def read_mongo(db, collection, query={}, host='localhost', port='27017', user=None, pwd=None, no_id=True):
    """ Pymongo"""
    db = connect_mongo(host=host, port=port, user=user, pwd=pwd, db=db)
    # cursor = db[collection].find(query)


def main(host='localhost', port=8086):
    filename = "Ysang"
    path = 'C:\\Users\\CheonYoungJo\\Downloads\\%s.log' % filename
    res = {}
    with open(path, 'r') as logData:
        print(logData, " Core Num:", numCores)
        denominator = len(logData.readlines())
        numerator = 0
        i = ''
        perLimit = 5
        print(denominator, "rows")
        logData.seek(0)
        for line in logData:
            cols = line.split('|')
            numerator += 1
            data = {}
            # res = {}
            # print(">>>>>>", line)
            for c in cols:
                per = round((numerator / denominator), 2) * 100
                # print(numerator, denominator, numerator / denominator, round(numerator / denominator, 2), per)
                if per >= perLimit and per != 0:
                    print("현재 ", per, "% 진행 중 입니다. ")
                    perLimit += 5
                    time.sleep(0.1)
                key = c.split('=')[0]
                val = c.split('=')[1]
                if key == 'reqTime':
                    val = datetime.datetime.strptime(val, "%Y%m%d%H%M%S")
                    val = datetime.datetime.fromtimestamp(val.timestamp())
                    # while str(val) in res:
                    #     val += datetime.timedelta(milliseconds=1)
                    i = str(val)
                    data[key] = i
                else:
                    data[key] = val
            res[numerator-1] = data
            """Line by Line Test"""
            # print(data)
    df = pd.DataFrame.from_dict(res, orient='index')

    # dic = {"reqTime": "2019-01-01 00:00:00", "field": {"a":1,"b":2}}
    # print(dic, json.dumps(dic))
    # df = pd.DataFrame.from_dict(dic, orient='columns')

    df.to_sql(name="testdb", con=engine, if_exists='append')
    # pprint(res)
    # j = json.dumps(res)
    #
    # df = pd.DataFrame.from_dict(j, orient='index')
    # df = pd.read_json(j, orient='index')
    # print(df)
    #
    # df.to_sql(name="testdb", con=engine, if_exists='append')


    # """Instantiate the connection to the InfluxDB client."""
    # user = ''
    # password = ''
    # dbname = 'logTest'
    # protocol = 'json'
    # measurement = 'testTable'
    #
    # client = DataFrameClient(host, port, user, password, dbname)
    #
    # print("Create pandas DataFrame")
    # # df = pd.DataFrame(data=list(range(30)),
    # #                   index=pd.date_range(start='2014-11-16',
    # #                                       periods=30, freq='H'), columns=['0'])
    # # print(">>>", df)
    # print("Create database: " + dbname)
    # client.create_database(dbname)
    #
    # print("Write DataFrame")
    # writeLimit = 100000
    # writeInc = 100000
    # start = 0
    # while True:
    #     print(writeLimit, "/", len(df), "번째까지 쓰고 있습니다")
    #     if len(df) > writeLimit:
    #         tempDF = df[start:writeLimit]
    #         client.write_points(tempDF, measurement, protocol=protocol)
    #         writeLimit += writeInc
    #         start += writeInc
    #     else:
    #         tempDF = df[writeLimit:]
    #         client.write_points(tempDF, measurement, protocol=protocol)
    #         writeLimit += len(df)
    #         break

    # df = pd.DataFrame(data=list(range(500000)),
    #                   index=pd.date_range(start='2017-11-16',
    #                                       periods=30, freq='M'), columns=['0'])

    # client.write_points(df, measurement, protocol=protocol, batch_size=100000, time_precision='ms')

    # print("Write DataFrame with Tags")
    # client.write_points(df, measurement,
    #                     {'k1': 'v1', 'k2': 'v2'}, protocol=protocol)

    # print("Read DataFrame")
    # pprint(client.query("select * from testTable"))

    # print("Delete database: " + dbname)
    # client.drop_database(dbname)


def parse_args():
    """Parse the args from main."""
    parser = argparse.ArgumentParser(
        description='example code to play with InfluxDB')
    parser.add_argument('--host', type=str, required=False,
                        default='localhost',
                        help='hostname of InfluxDB http API')
    parser.add_argument('--port', type=int, required=False, default=8086,
                        help='port of InfluxDB http API')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(host=args.host, port=args.port)