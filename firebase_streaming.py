# adapted from firebase/EventSource-Examples/python/chat.py by Shariq Hashme

from sseclient import SSEClient
import requests

import json
import threading
import socket
import ast


def json_to_dict(response):
    return ast.literal_eval(json.dumps(response))


class ClosableSSEClient(SSEClient):

    def __init__(self, *args, **kwargs):
        self.should_connect = True
        super(ClosableSSEClient, self).__init__(*args, **kwargs)

    def _connect(self):
        if self.should_connect:
            super(ClosableSSEClient, self)._connect()
        else:
            raise StopIteration()

    def close(self):
        self.should_connect = False
        self.retry = 0
        try:
            self.resp.raw._fp.fp._sock.shutdown(socket.SHUT_RDWR)
            self.resp.raw._fp.fp._sock.close()
        except AttributeError:
            pass


class RemoteThread(threading.Thread):

    def __init__(self, parent, URL, function):
        self.function = function
        self.URL = URL
        self.parent = parent
        super(RemoteThread, self).__init__()

    def run(self):
        try:
            self.sse = ClosableSSEClient(self.URL)
            for msg in self.sse:
                msg_test = json.loads(msg.data)
                if msg_test is None:    # keep-alives
                    continue
                msg_data = json_to_dict(msg.data)
                msg_event = msg.event

                DEBUG = False
                if msg_event == 'put':
                    if msg_test['path'] == "/":
                        self.parent.admin_id = msg_test['data']['admin_id']
                        self.parent.notif = msg_test['data']['notif']
                        self.parent.timestamp = msg_test['data']['timestamp']
                    elif msg_test['path'] == "/admin_id":
                        self.parent.admin_id = msg_test['data']
                    elif msg_test['path'] == "/notif":
                        self.parent.notif = msg_test['data']
                    elif msg_test['path'] == "/timestamp":
                        self.parent.timestamp = msg_test['data']
                    else:
                        DEBUG = True
                else:
                    DEBUG = True

                if DEBUG:
                    print("DEBUG event: " + msg_event)
                    print("DEBUG data: " + msg_data)
                
                self.function(self.parent)

        except socket.error:
            pass    # this can happen when we close the stream
        except KeyboardInterrupt:
            self.close()

    def close(self):
        if hasattr(self, 'sse'):
            self.sse.close()


def firebaseURL(URL):
    if '.firebaseio.com' not in URL.lower():
        if '.json' == URL[-5:]:
            URL = URL[:-5]
        if '/' in URL:
            if '/' == URL[-1]:
                URL = URL[:-1]
            URL = 'https://' + \
                URL.split('/')[0] + '.firebaseio.com/' + URL.split('/', 1)[1] + '.json'
        else:
            URL = 'https://' + URL + '.firebaseio.com/.json'
        return URL

    if 'http://' in URL:
        URL = URL.replace('http://', 'https://')
    if 'https://' not in URL:
        URL = 'https://' + URL
    if '.json' not in URL.lower():
        if '/' != URL[-1]:
            URL = URL + '/.json'
        else:
            URL = URL + '.json'
    return URL


class EventListener:

    def __init__(self, URL, function):
        self.admin_id = {}
        self.notif = {}
        self.timestamp = {}
        
        self.cache = {}
        self.remote_thread = RemoteThread(self, firebaseURL(URL), function)

    def start(self):
        self.remote_thread.start()

    def stop(self):
        self.remote_thread.close()
        self.remote_thread.join()

    def wait(self):
        self.remote_thread.join()


class FirebaseException(Exception):
    pass

class Firebase():

    def __init__(self, name):
        self.name = name
        self.URL = firebaseURL(name)

    def child(self, child):
        return Firebase(self.name + child + "/")

    def put(self, msg):
        to_post = json.dumps(msg)
        response = requests.put(firebaseURL(self.URL), data=to_post)
        if response.status_code != 200:
            raise FirebaseException(response.text)

    def patch(self, msg):
        to_post = json.dumps(msg)
        response = requests.patch(firebaseURL(self.URL), data=to_post)
        if response.status_code != 200:
            raise FirebaseException(response.text)

    def get(self):
        response = requests.get(firebaseURL(self.URL))
        if response.status_code != 200:
            raise FirebaseException(response.text)
        return json_to_dict(response)

    def listener(self, callback=None):

        def handle(response):
            print(response)

        return EventListener(self.name, callback or handle)

    def __str__(self):
        return self.name
