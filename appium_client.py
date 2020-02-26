import urllib3
import json
import os

from datetime import datetime, timedelta


class ElementNotFoundException(Exception):
    '''
    An exception thrown when the element can not be found.
    :arg details: A free form text message.
    '''

    def __init__(self, details):
        if isinstance(details, str):
            details = {'message': details}
        Exception.__init__(self, details)


class UnknownUiServerException(Exception):
    '''
    An exception thrown when in below situation:
    - The given Ui Selector can not be parsed
    - Requested attribute {0} not supported
    - Unknown internal server error
    :arg details: A free form text message.
    '''

    def __init__(self, details):
        if isinstance(details, str):
            details = {'message': details}
        Exception.__init__(self, details)


class InvalidCoordinatesException(Exception):
    '''
    An exception thrown when the coordinates provided to an interactions
    operation are invalid.
    :arg details: A free form text message.
    '''

    def __init__(self, details):
        if isinstance(details, str):
            details = {'message': details}
        Exception.__init__(self, details)


class JsonDecoderError(Exception):
    '''
    An exception thrown when could not decode action/params of command
    :arg details: A free form text message.
    '''

    def __init__(self, details):
        if isinstance(details, str):
            details = {'message': details}
        Exception.__init__(self, details)


class ByText(dict):

    def __init__(self, varg):
        self['strategy'] = '-android uiautomator'
        self['selector'] = 'new UiSelector().text(\"%s\");' % varg


class ById(dict):

    def __init__(self, varg):
        self['strategy'] = 'id'
        self['selector'] = varg


class ByDesc(dict):

    def __init__(self, varg):
        self['strategy'] = 'accessibility id'
        self['selector'] = varg


class ByClass(dict):

    def __init__(self, varg):
        self['strategy'] = 'class name'
        self['selector'] = varg


class ByXpath(dict):

    def __init__(self, varg):
        self['strategy'] = 'xpath'
        self['selector'] = varg


class ByUiautomator(dict):

    def __init__(self, varg):
        self['strategy'] = '-android uiautomator'
        self['selector'] = varg


class RequestHandler(object):
    base_url = 'http://localhost:'
    pool = None
    headers = {"Content-Type": "application/json"}

    def __init__(self, port):
        self.base_url = self.base_url + port
        self.pool = urllib3.PoolManager()

    def get(self, path):
        url = self.base_url + path
        return self.request_handler('GET', url)

    def post(self, path, body):
        url = self.base_url + path
        return self.request_handler('POST', url, body=body)

    def delete(self, path, body):
        url = self.base_url + path
        return self.request_handler('DELETE', url, body=body)

    def wait_for_netty(self):
        limit = datetime.now() + timedelta(seconds=30)
        unsuccessful = True
        while True:
            try:
                self.get('/wd/hub/status')
                unsuccessful = False
            except Exception:
                # Waiting for server ...
                pass
            if not unsuccessful or datetime.now() > limit:
                break

        if unsuccessful:
            raise Exception("Failed to contact io.appium.uiautomator2.server on " + self.base_url)

    def netty(self):
        try:
            self.get('/wd/hub/status')
            return True
        finally:
            return False

    def request_handler(self, method, url, body=None):
        try:
            if method == 'GET':
                r = self.pool.urlopen('GET', url, headers=self.headers)
            else:
                r = self.pool.urlopen(method, url, body=body, headers=self.headers)
        except Exception as e:
            raise Exception("Failed to connect Appium Server: %s" % e)

        if r.status == 200:
            return r.data.decode('utf8')
        elif r.status == 301:
            raise Exception('The request: %s %s moved Permanently') % (method, url)
        elif r.status == 404:
            raise Exception('The request: %s %s not found.') % (method, url)
        elif r.status == 500:
            data = json.loads(r.data.decode('utf8'))
            if data['status'] == 7:
                raise ElementNotFoundException('Could not locate the element: %s' % body)
            elif data['status'] in [9, 10, 13, 21, 23, 32]:
                msg = {'method': '%s "%s" ' % (method, url), 'body': body.decode('utf-8'), 'status': data['status'],
                       'error': data['value']}
                raise UnknownUiServerException(json.dumps(msg).encode('utf-8'))
            elif data['status'] == 29:
                msg = {'method': '%s "%s" ' % (method, url), 'body': body.decode('utf-8'), 'error': data['value']}
                raise InvalidCoordinatesException(json.dumps(msg).encode('utf-8'))
            elif data['status'] == 35:
                msg = {'method': '%s "%s" ' % (method, url), 'body': body.decode('utf-8'), 'error': data['value']}
                raise JsonDecoderError(json.dumps(msg).encode('utf-8'))


class AppiumClient(object):
    prefix_path = '/wd/hub/session'
    base_path = None
    rpc = None

    def __init__(self, port=6790):
        self.rpc = RequestHandler(port)
        self.base_path = os.path.join(self.prefix_path, self._create_session())

    def netty(self):
        return self.rpc.netty()

    def find_element(self, data):
        url = self.base_path + '/element'
        data['context'] = ''
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']['ELEMENT']

    def find_elements(self, data):
        url = self.base_path + '/elements'
        data['context'] = ''
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        element_ids = []
        for element in json.loads(response)['value']:
            element_ids.append(element['ELEMENT'])
        return element_ids

    def find_child_element(self, f_data, c_data):
        url = self.base_path + '/element'
        c_data['context'] = self.find_element(f_data)
        encoded_data = json.dumps(c_data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']['ELEMENT']

    def find_child_elements(self, f_data, c_data):
        url = self.base_path + '/elements'
        c_data['context'] = self.find_element(f_data)
        encoded_data = json.dumps(c_data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        element_ids = []
        for element in json.loads(response)['value']:
            element_ids.append(element['ELEMENT'])
        return element_ids

    def click_element(self, element_id):
        url = self.base_path + '/element/' + element_id + '/click'
        data = {'element': element_id}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_forward_on_element(self, element_id, is_vertical_list=True):
        url = self.base_path + '/element/' + element_id + '/scroll_forward_on_view'
        data = {'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_backward_on_element(self, element_id, is_vertical_list=True):
        url = self.base_path + '/element/' + element_id + '/scroll_backward_on_view'
        data = {'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_to_text_on_element(self, element_id, text, is_vertical_list=True):
        url = self.base_path + '/element/' + element_id + '/scroll_to_text_on_view'
        data = {'text': text, 'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_to_sub_text_on_element(self, element_id, text, is_vertical_list=True):
        url = self.base_path + '/element/' + element_id + '/scroll_to_sub_text_on_view'
        data = {'text': text, 'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_to_text_regex_on_element(self, element_id, regex, is_vertical_list=True):
        url = self.base_path + '/element/' + element_id + '/scroll_to_text_reg_on_view'
        data = {'regex': regex, 'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def wait_for_element(self, by, timeout):
        limit = datetime.now() + timedelta(seconds=timeout)
        found_status = False
        while True:
            try:
                self.find_element(by)
                found_status = True
            except ElementNotFoundException:
                pass
            finally:
                raise
            if found_status or datetime.now() > limit:
                break
        return found_status

    def wait_for_element_invisible(self, by, timeout):
        limit = datetime.now() + timedelta(seconds=timeout)
        exist = True
        while True:
            try:
                self.find_element(by)
            except ElementNotFoundException:
                exist = False
            finally:
                raise
            if not exist or datetime.now() > limit:
                break
        return not exist

    def delete_session(self):
        data = {}
        encoded_data = json.dumps(data).encode('utf-8')
        return self.rpc.delete(self.base_path, encoded_data)

    def _create_session(self):
        data = {'desiredCapabilities': {}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post('/wd/hub/session', encoded_data)
        return json.loads(response)['sessionId']

    def wait_for_netty(self):
        self.rpc.wait_for_netty()

    def get_size(self, element_id):
        url = self.base_path + '/element/' + element_id + '/size'
        response = self.rpc.get(url)
        return json.loads(response)['value']

    def get_text(self, element_id):
        url = self.base_path + '/element/' + element_id + '/text'
        response = self.rpc.get(url)
        return json.loads(response)['value']

    def long_click(self, element_id, duration=1):
        url = self.base_path + '/touch/longclick'
        data = {'params': {'element': element_id, 'duration': duration * 1000}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        if json.loads(response)['status'] == 0:
            return True
        else:
            return False

    def rotate_screen(self, orientation):
        if orientation.upper() not in ['LANDSCAPE', 'PORTRAIT']:
            raise Exception('the para is not right, it must be \'LANDSCAPE\' or \'PORTRAIT\'')
        url = self.base_path + '/orientation'
        data = {'orientation': orientation}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_to(self, scroll_to_text, index=0, is_vertical_list=True):
        url = self.base_path + '/touch/scroll'
        data = {'text': scroll_to_text, 'index': index, 'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def scroll_on_screen(self, direction, index=0, is_vertical_list=True):
        url = self.base_path + '/touch/scroll_on_screen'
        data = {'direction': direction, 'index': index, 'is_vertical_list': is_vertical_list}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        if json.loads(response)['status'] == 0:
            return True
        else:
            return False

    def set_text(self, element_id, text):
        url = self.base_path + '/element/' + element_id + '/value'
        data = {'element': element_id, 'text': text, 'replace': False}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        if json.loads(response)['status'] == 0:
            return True
        else:
            return False

    def set_rotation(self, z):
        if z not in [0, 90, 180, 270]:
            raise Exception('the para is not right, it must be in (0, 90, 180, 270)')
        url = self.base_path + '/rotation'
        data = {'x': 0, 'y': 0, 'z': z}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def tap(self, x, y):
        url = self.base_path + '/appium/tap'
        data = {'x': x, 'y': y}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def swipe(self, x1, y1, x2, y2, steps):
        url = self.base_path + '/touch/perform'
        data = {'startX': x1, 'startY': y1, 'endX': x2, 'endY': y2, 'steps': steps}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_down_element(self, element_id):
        url = self.base_path + '/touch/down'
        data = {'params': {'element': element_id}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_up_element(self, element_id):
        url = self.base_path + '/touch/up'
        data = {'params': {'element': element_id}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_move_element(self, element_id):
        url = self.base_path + '/touch/move'
        data = {'params': {'element': element_id}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_down(self, x, y):
        url = self.base_path + '/touch/down'
        data = {'params': {'x': x, 'y': y}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_up(self, x, y):
        url = self.base_path + '/touch/up'
        data = {'params': {'x': x, 'y': y}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def touch_move(self, x, y):
        url = self.base_path + '/touch/move'
        data = {'params': {'x': x, 'y': y}}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def dump_hierarchy(self):
        url = self.base_path + '/source'
        response = self.rpc.get(url)
        return json.loads(response)['value']

    def multi_pointer_gesture(self, body):
        url = self.base_path + '/touch/multi/perform'
        return self.rpc.post(url, body)

    def flick_on_element(self, element_id, xoffset, yoffset, speed):
        url = self.base_path + '/touch/flick'
        data = {'element': element_id, 'xoffset': xoffset, 'yoffset': yoffset, 'speed': speed}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def flick_on_position(self, xspeed, yspeed):
        url = self.base_path + '/touch/flick'
        data = {'xSpeed': xspeed, 'ySpeed': yspeed}
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']

    def get_attribute(self, element_id, attribute):
        response = self.rpc.get(self.base_path + "/element/" + element_id + "/attribute/" + attribute)
        return json.loads(response)['value']

    def get_device_size(self):
        response = self.rpc.get(self.base_path + "/window/current/size")
        return json.loads(response)['value']

    def get_location(self, element_id):
        response = self.rpc.get(self.base_path + "/element/" + element_id + "/location")
        value = json.loads(response)['value']
        return value['x'], value['y']

    def get_desc(self, element_id):
        response = self.rpc.get(self.base_path + "/element/" + element_id + "/name")
        return json.loads(response)['value']

    def get_rotation(self):
        response = self.rpc.get(self.base_path + "/rotation")
        value = json.loads(response)['value']
        return value['z']

    def get_screen_orientation(self):
        response = self.rpc.get(self.base_path + "/orientation")
        return json.loads(response)['value']

    def open_notification(self):
        url = self.base_path + '/appium/device/open_notifications'
        response = self.rpc.post(url, '{}')
        return json.loads(response)['value']

    def enable_logging(self, enabled):
        url = self.base_path + '/enable_logging'
        data = dict()
        data['enabled'] = enabled
        encoded_data = json.dumps(data).encode('utf-8')
        response = self.rpc.post(url, encoded_data)
        return json.loads(response)['value']


client = AppiumClient()
client.click_element(client.find_element(ByText("test")))
