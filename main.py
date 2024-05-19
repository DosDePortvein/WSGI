from json import JSONDecodeError
from wsgiref.simple_server import make_server
import json
import pytz
from datetime import datetime
from pytz.exceptions import UnknownTimeZoneError


def get_time_from_tz_name(environ, response, headers):
    if environ['REQUEST_METHOD'] != 'GET':
        response('405 Method Not Allowed', headers)
        return b"Method not allowed"
    query = environ['QUERY_STRING'].split("=")
    if query[0] == 'tz_name':
        try:
            current_time = datetime.now(pytz.timezone(query[1])).strftime('%m.%d.%Y %H:%M:%S')
            response("200 OK", headers)
            return current_time.encode('utf-8')
        except UnknownTimeZoneError:
            response("400 Bad request", headers)
            return b"Timezone not found"
    if query[0] == "":
        current_time = datetime.now(pytz.timezone('GMT')).strftime('%m.%d.%Y %H:%M:%S')
        response("200 OK", headers)
        return current_time.encode('utf-8')
    response("400 Bad request", headers)
    return b"Something wrong with query string"


def convert(environ, response, headers):
    if environ['REQUEST_METHOD'] != 'POST':
        response('405 Method Not Allowed', headers)
        return b"Method not allowed"
    query = environ['QUERY_STRING'].split("=")
    try:
        target_tz = pytz.timezone(query[1])
        if query[0] != 'target_tz':
            raise KeyError
    except UnknownTimeZoneError:
        response("400 Bad request", headers)
        return b"Timezone not found"
    except KeyError:
        response("400 Bad request", headers)
        return b"Something wrong with query string"
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    try:
        json_from_body = json.loads(request_body)
        input_tz = pytz.timezone(json_from_body['tz'])
        input_time = datetime.strptime(json_from_body['date'], '%m.%d.%Y %H:%M:%S').replace(tzinfo=input_tz)
        result = target_tz.normalize(input_time.astimezone(target_tz))
        response("200 OK", headers)
        return result.strftime('%m.%d.%Y %H:%M:%S').encode('utf-8')
    except UnknownTimeZoneError:
        response("400 Bad request", headers)
        return b"Timezone not found"
    except (KeyError, JSONDecodeError):
        response("405 Invalid Input", headers)
        return b"Invalid Input"
    except ValueError:
        response("405 Invalid Input", headers)
        return b"Invalid date format"


def datediff(environ, response, headers):
    if environ['REQUEST_METHOD'] != 'POST':
        response('405 Method Not Allowed', headers)
        return b"Method not allowed"
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    try:
        json_from_body = json.loads(request_body)
        first_tz = pytz.timezone(json_from_body['first_tz'])
        second_tz = pytz.timezone(json_from_body['second_tz'])
        first_date = datetime.strptime(json_from_body['first_date'], '%m.%d.%Y %H:%M:%S').replace(tzinfo=first_tz)
        second_date = datetime.strptime(json_from_body['second_date'], '%H:%M%p %Y-%m-%d').replace(tzinfo=second_tz)
        if first_date > second_date:
            result = str((first_date - second_date).total_seconds())
            response("200 OK", headers)
            return result.encode('utf-8')
        else:
            result = str((second_date - first_date).total_seconds())
            response("200 OK", headers)
            return result.encode('utf-8')
    except UnknownTimeZoneError:
        response("400 Bad request", headers)
        return b"Timezone not found"
    except (KeyError, JSONDecodeError):
        response("405 Invalid Input", headers)
        return b"Invalid Input"
    except ValueError:
        response("405 Invalid Input", headers)
        return b"Invalid date format"



PATH_DICT = {'/': get_time_from_tz_name, '/api/v1/convert': convert, '/api/v1/datediff': datediff} #Словарь с доступными URL


def time_app(environ, response):
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    try:
        result = PATH_DICT[environ["PATH_INFO"]](environ, response, headers)
    except KeyError:
        response("404 Not Found", headers)
        return [b"Not found"]
    return [result]


with make_server('127.0.0.1', 8000, time_app) as httpd:
    try:
        print("Server start")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        print("Server shutdown")
