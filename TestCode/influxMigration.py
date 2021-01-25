import unittest
import pandas as pd
from influxdb import DataFrameClient, InfluxDBClient
import argparse


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


def migration(host='localhost', port=8086):
    user = 'root'
    password = 'root'
    dbname = 'test'
    protocol = 'line'
    client = DataFrameClient(host, port, user, password, dbname)

    print("Create Pandas DataFrame")


if __name__ == '__main__':
    unittest.main()
