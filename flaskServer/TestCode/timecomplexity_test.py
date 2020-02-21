import argparse
from pprint import pprint
import pandas as pd
import json, datetime, os, time, sys
from influxdb import DataFrameClient
import multiprocessing as mp
import numpy as np
import pymongo
import pymysql
from sqlalchemy import create_engine
from multiprocessing import Process, Pool, cpu_count

pymysql.install_as_MySQLdb()
engine = create_engine("mysql+mysqldb://user:" + "1234" + "@localhost/test2",pool_recycle=300, encoding='utf-8')
conn = engine.connect()


def main():
    filename = "Ysang"
    path = 'C:\\Users\\CheonYoungJo\\Downloads\\%s.log' % filename
    res = {}
    with open(path, 'r') as logData:
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
                    val = datetime.datetime.utcfromtimestamp(val.timestamp())
                    # val = datetime.datetime.timestamp(val)
                    # while str(val) in res:
                    #     val += datetime.timedelta(milliseconds=1)
                    # i = str(val)
                    data[key] = val
                else:
                    data[key] = val
            res[numerator - 1] = data

    df = pd.DataFrame.from_dict(res, orient='index')

    now = datetime.datetime.now()
    print(now)
    # df = pd.DataFrame(np.random.randn(100000, 100))
    # t1 = datetime.datetime.now()
    # print(df, t1-now)

    flag = False
    return df, now, flag


def process_zero(df, start):
    df.to_sql('testdb01', engine, if_exists='replace')
    print("Zero >>>>", datetime.datetime.now() - start)


def process_one(df, start):
    df.to_sql('testdb02', engine, if_exists='replace', chunksize=10)
    print("One >>>>", datetime.datetime.now() - start)


def process_second(df, start):
    df.to_sql('testdb03', engine, if_exists='replace', chunksize=1000)
    print("Sec >>>>", datetime.datetime.now() - start)


def timer(start):
    while True:
        print(datetime.datetime.now() - start, start)
        time.sleep(10)


def writeFunc():
    filename = "Ysang"
    path = 'C:\\Users\\CheonYoungJo\\Downloads\\%s.log' % filename
    res = {}
    with open(path, 'r') as logData:
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
                    break
                    print("현재 ", per, "% 진행 중 입니다. ")
                    perLimit += 5
                    time.sleep(0.1)
                key = c.split('=')[0]
                val = c.split('=')[1]
                if key == 'reqTime':
                    val = datetime.datetime.strptime(val, "%Y%m%d%H%M%S")
                    val = datetime.datetime.utcfromtimestamp(val.timestamp())
                    # val = datetime.datetime.timestamp(val)
                    # while str(val) in res:
                    #     val += datetime.timedelta(milliseconds=1)
                    # i = str(val)
                    data[key] = val
                else:
                    data[key] = val
            res[numerator - 1] = data

    df = pd.DataFrame.from_dict(res, orient='index')
    df_len = len(df)
    quotient = df_len // 10
    remainder = df_len % 10
    print(df_len, quotient, remainder)
    now = datetime.datetime.now()
    print(now)

    """ Basic Division Method (x/11)"""
    st = 0
    ed = quotient
    flag = True
    ct = 9
    while ct:
        now = datetime.datetime.now()
        while flag:
            df.to_sql('testdb01', engine, if_exists='replace', chunksize=10)
            # print(df[st:ed], datetime.datetime.now() - now)
            print(datetime.datetime.now() - now)
            if ed > len(df):
                ed += remainder
                flag = False
            else:
                st += quotient
                ed += quotient
            time.sleep(1.5)
        print(">>", datetime.datetime.now() - now)
        ct -= 1
        st = 0
        ed = quotient
        flag = True

    """ Using MultiProcessing Pool """
    # st = 0
    # ed = quotient
    # flag = True
    # ct = 9
    # while ct:
    #     df_list = []
    #     while flag:
    #         df_list.append(df[st:ed])
    #         if ed > len(df):
    #             ed += remainder
    #             flag = False
    #         else:
    #             st += quotient
    #             ed += quotient
    #
    #     now = datetime.datetime.now()
    #     coreNum = mp.cpu_count()
    #     pool = Pool(processes=coreNum)
    #     pool.map(process_func, df_list)
    #     pool.close()
    #     pool.join()
    #     print(">>", datetime.datetime.now() - now)
    #     ct -= 1
    #     st = 0
    #     ed = quotient
    #     flag = True

    """ Using MultiProcessing Process"""


    """ Length Test """
    # print(df, df.size, len(df))
    # print(df[0:10], df[0:10].size, len(df[0:10]))
    # print(df.values)
    # print(df.iloc[1])
    # print(df.iloc[[0,1]])
    # print(df.iloc[0:10])


def process_func(df):
    start = datetime.datetime.now()
    engine = create_engine("mysql+mysqldb://user:" + "1234" + "@localhost/test2",pool_recycle=300, encoding='utf-8')
    conn = engine.connect()
    df.to_sql('testdb01', conn, if_exists='append')
    """
    to_sql 대신 sql문으로 insert하는 걸로 변경해야지 dead lock을 피할 수 있을거 같음.
    """
    print("-", datetime.datetime.now() - start)


if __name__ == '__main__':
    writeFunc()
    # df, date, flag = main()
    # while flag:
    #     print("Flag를 기다려주세요")
    #     time.sleep(1)
    # p1 = Process(target=process_zero, args=(df, date))
    # p2 = Process(target=process_one, args=(df, date))
    # p3 = Process(target=process_second, args=(df, date))
    # # p4 = Process(target=timer, args=(date,))
    # p1.start()
    # p2.start()
    # p3.start()
    # # p4.start()
    # time.sleep(1)
    # # p4.join()
    # p3.join()
    # p2.join()
    # p1.join()
