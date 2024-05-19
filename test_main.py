import http.client
import json
import unittest
from datetime import datetime
import pytz


def send_request(address, path, method, query_string='', json_data={}):
    connection = http.client.HTTPConnection(address)
    headers = {'Content-type': 'application/json'}
    if query_string:
        path += '?' + query_string
    if json_data:
        json_data = json.dumps(json_data)
        connection.request(method, path, json_data, headers)
    else:
        connection.request(method, path, headers=headers)
    response = connection.getresponse()
    connection.close()
    return [response.status, response.read().decode('utf-8')]


class AppTest(unittest.TestCase):
    def test_get_time_from_tz_name(self):
        address = '127.0.0.1:8000'
        path = '/'
        method = 'GET'
        #Test with empty query string
        self.assertEqual(send_request(address, path, method),
                         [200, datetime.now(pytz.timezone('GMT')).strftime('%m.%d.%Y %H:%M:%S')])
        #Test with correct filled query string
        correct_query_string = 'tz_name=Europe/Moscow'
        self.assertEqual(send_request(address, path, method, correct_query_string),
                         [200, datetime.now(pytz.timezone('Europe/Moscow')).strftime('%m.%d.%Y %H:%M:%S')])
        #Test with incorrect variable in query string
        incorrect_query_string = 'invalid_variable=Europe/Moscow'
        self.assertEqual(send_request(address, path, method, incorrect_query_string),
                         [400, 'Something wrong with query string'])
        #Test with incorrect time zone in query string
        incorrect_tz_in_query_string = 'tz_name=Invalid/Tz'
        self.assertEqual(send_request(address, path, method, incorrect_tz_in_query_string),
                         [400, 'Timezone not found'])
        #Test with not allowed method
        self.assertEqual(send_request(address, path, 'POST'),
                         [405, 'Method not allowed'])

    def test_convert(self):
        address = '127.0.0.1:8000'
        path = '/api/v1/convert'
        method = 'POST'
        #Test with correct data
        correct_json_data = {"date": "12.20.2021 10:10:10", "tz": "Etc/GMT+2"}
        correct_query_string = 'target_tz=GMT'
        self.assertEqual(send_request(address, path, method, correct_query_string, correct_json_data),
                         [200, '12.20.2021 12:10:10'])
        #Test with incorrect variable in query string
        incorrect_query_string = 'invalid_variable=GMT'
        self.assertEqual(send_request(address, path, method, incorrect_query_string, correct_json_data),
                         [400, 'Something wrong with query string'])
        #Test with incorrect time zone in query string
        incorrect_tz_in_query_string = 'target_tz=Invalid/Tz'
        self.assertEqual(send_request(address, path, method, incorrect_tz_in_query_string, correct_json_data),
                         [400, 'Timezone not found'])
        #Test witn empty/incorrect(variables) json
        self.assertEqual(send_request(address, path, method, correct_query_string, {}),
                         [405, 'Invalid Input'])
        #Test with incorrect time zone in json
        incorrect_json_data_tz = {"date": "12.20.2021 10:10:10", "tz": "Invalid/Tz"}
        self.assertEqual(send_request(address, path, method, correct_query_string, incorrect_json_data_tz),
                         [400, 'Timezone not found'])
        #Test with incorrect data format in json
        incorrect_json_data_format = {"date": "12-20-2021 10!10!10", "tz": "Etc/GMT+2"}
        self.assertEqual(send_request(address, path, method, correct_query_string, incorrect_json_data_format),
                         [405, 'Invalid date format'])
        # Test with not allowed method
        self.assertEqual(send_request(address, path, 'GET', correct_query_string, correct_json_data),
                         [405, 'Method not allowed'])

    def test_datediff(self):
        address = '127.0.0.1:8000'
        path = '/api/v1/datediff'
        method = 'POST'
        #Test with correct data
        correct_json_data = {"first_date":"12.06.2024 12:30:00", "first_tz": "GMT", "second_date":"12:30pm 2024-12-06",
                             "second_tz": "Etc/GMT+2"}
        self.assertEqual(send_request(address, path, method, json_data=correct_json_data),
                         [200, '7200.0'])
        #Test witn empty/incorrect(variables) json
        self.assertEqual(send_request(address, path, method, json_data={}),
                         [405, 'Invalid Input'])
        #Test with incorrect time zone in json (first_tz, second_tz)
        incorrect_json_data_tz = {"first_date":"12.06.2024 12:30:00", "first_tz": "Invalid/Tz", "second_date":"12:30pm 2024-12-06",
                             "second_tz": "Etc/GMT+2"}
        self.assertEqual(send_request(address, path, method, json_data=incorrect_json_data_tz),
                         [400, 'Timezone not found'])
        incorrect_json_data_tz = {"first_date":"12.06.2024 12:30:00", "first_tz": "GMT", "second_date":"12:30pm 2024-12-06",
                             "second_tz": "Invalid/Tz"}
        self.assertEqual(send_request(address, path, method, json_data=incorrect_json_data_tz),
                         [400, 'Timezone not found'])
        #Test with incorrect data format in json (first_date, second_date)
        incorrect_json_data_format = {"first_date":"12!06!2024 12a30a00", "first_tz": "GMT", "second_date":"12:30pm 2024-12-06",
                             "second_tz": "Etc/GMT+2"}
        self.assertEqual(send_request(address, path, method, json_data=incorrect_json_data_format),
                         [405, 'Invalid date format'])
        incorrect_json_data_format = {"first_date":"12.06.2024 12:30:00", "first_tz": "GMT", "second_date":"121230 asfq",
                             "second_tz": "Etc/GMT+2"}
        self.assertEqual(send_request(address, path, method, json_data=incorrect_json_data_format),
                         [405, 'Invalid date format'])
        # Test with not allowed method
        self.assertEqual(send_request(address, path, 'GET', json_data=correct_json_data),
                         [405, 'Method not allowed'])



unittest.main()