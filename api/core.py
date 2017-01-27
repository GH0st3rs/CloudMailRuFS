#!/usr/bin/python3
import requests
import re
import json
import os
from time import time


class CloudMailAPI():
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
                                     'X-Requested-With': 'XMLHttpRequest'})
        self.MAIN_HEADERS = {}
        self.api_url = 'https://cloud.mail.ru/api/v2/'
        self.public_url = 'https://cloud.mail.ru/public/'
        self.API_V = 2

    def debug(self, txt):
        print(txt)

    def is_error(self, req):
        if req['status'] != 200:
            print('Error: %d => %s' % (req['status'], req['body']))
            return True
        else:
            return False

    def auth(self, email, passwd):
        self.email = email
        login = self.email.split('@')[0]
        url = 'https://auth.mail.ru/cgi-bin/auth?lang=ru_RU&from=authpopup'
        data = {'page': 'https://cloud.mail.ru/?from=promo',
                'Domain': 'mail.ru',
                'FailPage': '',
                'Login': self.email,
                'Password': passwd,
                'Username': login,
                'saveauth': 1,
                'new_auth_form': 1}

        req = self.session.post(url, data)
        try:
            json_txt = re.findall('<script>window\[[a-zA-Z0-9\"\_]+\]\ *\=([^<]+)</script>', req.text)[0]
            json_txt = json.loads(re.sub('"ITEM_NAME_INVALID_CHARACTERS":"[^,]+",', '', json_txt)[:-1])
            csrf_token = json_txt['tokens']['csrf']
            BUILD = json_txt['params']['BUILD']
            x_page_id = json_txt['params']['x-page-id']
        except:
            csrf_token = re.findall('"csrf":"([a-zA-Z0-9]+)"', req.text)[0]
            x_page_id = re.findall('"x-page-id":"([a-zA-Z0-9]+)"', req.text)[0]
            BUILD = re.findall('"BUILD":"([a-zA-Z0-9]+)"', req.text)[0]

        self.MAIN_HEADERS['_'] = round(time() * 1000)
        self.MAIN_HEADERS['x-email'] = self.MAIN_HEADERS['email'] = self.email
        self.MAIN_HEADERS['x-page-id'] = x_page_id
        self.MAIN_HEADERS['build'] = BUILD
        self.MAIN_HEADERS['api'] = self.API_V
        self.MAIN_HEADERS['token'] = csrf_token

    def connect(self, method, action, data={}):
        data.update(self.MAIN_HEADERS)
        if method == 'POST':
            req = self.session.post(self.api_url + action, data)
        elif method == 'GET':
            req = self.session.get(self.api_url + action, params=data)
        else:
            print('Error')
            return {}
        return json.loads(req.text)

    def check_share(self, file):
        req = self.file(file)
        if req['body'].get('weblink'):
            return self.unshare(file, req['body'].get('weblink'))

    def id(self, batch=False):
        '''Receive info about current account
        Return: {
            'time': 1485520422691,
            'body': {
                'domain': 'mail.ru',
                'account_type': 'regular',
                'ui': {
                    'expand_loader': True,
                    'sort': {'order': 'asc', 'type': 'name'},
                    'sidebar': False,
                    'kind': 'all',
                    'thumbs': False
                },
                'newbie': False,
                'login': 'user',
                'cloud': {
                    'billing': {
                        'prolong': False,
                        'active_cost_id': '',
                        'expires': 0,
                        'auto_prolong': False,
                        'active_rate_id': 'ZERO',
                        'enabled': True,
                        'subscription': []
                    },
                    'beta': {'allowed': True, 'asked': True},
                    'enable': {'sharing': True},
                    'file_size_limit': 2147483648,
                    'bonuses': {
                        'desktop': False,
                        'registration': False,
                        'feedback': False,
                        'mobile': False,
                        'camera_upload': False,
                        'links': False,
                        'complete': False
                    },
                    'metad': 2, 
                    'space': {'total': 102400, 'overquota': False, 'used': 74435}
                }
            }, 
            'email': self.email,
            'status': 200
        }'''
        return self.connect('GET', 'user')

    def dispatcher(self, batch=False):
        '''Receive temporary links
        Return: {
            'time': 1485520787262,
            'body': {
                'thumbnails': [{'count': '250', 'url': 'https://cloclo28.cloud.mail.ru/thumb/'}],
                'weblink_view': [{'count': '50', 'url': 'https://cloclo28.datacloudmail.ru/weblink/view/'}],
                'auth': [{'count': '500', 'url': 'https://swa.mail.ru/cgi-bin/auth'}],
                'weblink_get': [{'count': 1, 'url': 'https://cloclo28.cldmail.ru/jfBWE35z3yH8mvkNMwb/G'}],
                'upload': [{'count': '25', 'url': 'https://cloclo28-upload.cloud.mail.ru/upload/'}],
                'view_direct': [{'count': '250', 'url': 'http://cloclo28.cloud.mail.ru/docdl/'}],
                'weblink_video': [{'count': '3', 'url': 'https://cloclo28.cloud.mail.ru/videowl/'}],
                'weblink_thumbnails': [{'count': '50', 'url': 'https://cloclo28.datacloudmail.ru/weblink/thumb/'}],
                'get': [{'count': '100', 'url': 'https://cloclo21.datacloudmail.ru/get/'}],
                'video': [{'count': '3', 'url': 'https://cloclo28.cloud.mail.ru/video/'}],
                'view': [{'count': '250', 'url': 'https://cloclo28.datacloudmail.ru/view/'}]
            },
            'email': self.email,
            'status': 200
        }'''
        return self.connect('GET', 'dispatcher')

    def ls(self, folder, batch=False):
        '''[{"count": {"folders":4,"files":0},
            "tree": "343030336563623030303030",
            "name": "FOLDER_NAME",
            "grev": 10419,
            "size": 5561085784,
            "kind": "folder",
            "rev": 10413,
            "type": "folder",
            "home":"FOLDER_PATH"},...]'''
        req = self.file(folder)
        count = req['body']['count']['files'] + req['body']['count']['folders']
        offset = 0
        listing = []
        while offset <= count:
            data = {'home': folder, 'sort': '{"type":"name","order":"asc"}', 'offset': offset, 'limit': 500}
            listing += self.connect('GET', 'folder', data)['body']['list']
            offset += 500
        return listing

    def rm(self, file, batch=False):
        self.check_share()
        return self.connect('POST', 'file/remove', {'home': file})

    def mkdir(self, file, batch=False):
        '''Create directory
        Return: {
            'time': 1485520960531,
            'body': file,
            'email': self.email,
            'status': 200
        }'''
        return self.connect('POST', 'folder/add', {'conflict': 'rename', 'home': file})

    def share(self, file, batch=False):
        '''Create share link for file.
        Use https://cloud.mail.ru/public/ + body
        Return: {
            'time': 1485521095263,
            'body': 'DDDD/DkvRDDuXd',
            'email': self.email,
            'status': 200
        }'''
        return self.connect('POST', 'file/publish', {'home': file})

    def unshare(self, file, weblink=None, batch=False):
        '''Delete weblink from file
        Return: {
            'time': 1485521095263,
            'body': file,
            'email': self.email,
            'status': 200
        }'''
        if weblink is None:
            req = self.file(file)
            weblink = req['body'].get('weblink')
        return self.connect('POST', 'file/unpublish', {'weblink': weblink})

    def rename(self, file, new_name):
        '''Rename file to new_name
        file - must have fuul path to target file
        new_name - just new name for targer file
        Return: {
            'time': 1485521523534,
            'body': new_name,
            'email': self.email,
            'status': 200
        }'''
        self.check_share(file)
        return self.connect('POST', 'file/rename', {'home': file, 'name': new_name, 'conflict': 'rename'})

    def download(self, file):
        '''Use: https://cloud.mail.ru/ + body
        Return: {
            'status': 200,
            'email': self.email,
            'time': 1485523741349,
            'body': '/zip/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/file.zip'
        }'''
        body = self.file(file)
        if not self.is_error(body):
            body = body['body']
            req = self.connect('POST', 'zip', {'name': body['name'], 'cp866': 'false', 'home_list': '["%s"]' % body['home']})
            return req
        else:
            return body

    def upload(self, file, path):
        upload_folder = self.dispatcher()['body']['upload'][0]['url']
        self.debug('Upload folder is: %s' % upload_folder)
        url_param = '?cloud_domain=2&fileapi%s&x-email=%s' % (round(time() * 1000), self.email.replace('@', '%40'))
        if os.path.exists(file):
            fName = os.path.basename(file)
            files = {'file': (fName, open(file, 'rb'), 'application/octet-stream')}
        else:
            print('File %s not found' % file)
            return
        req = self.session.post('%s%s' % (upload_folder, url_param), files=files)
        if req.status_code == 200:
            req = req.text.strip().split(';')
            return self.add_file(os.path.join(path, fName), req[1], req[0])
        else:
            print('Error %s => %s' % (req.status_code, req.text.strip()))
            return

    def mv(self, file, folder, batch=False):
        '''Move file to folder
        file - must have fuul path to target file
        Return: {
            "email": self.email,
            "body": NEW_FILE_PATH,
            "time": 1485452161339,
            "status":
            200
        }'''
        return self.connect('POST', 'file/move', {'home': file, 'conflict': 'rename', 'folder': folder})

    def cp(self, file, folder, batch=False):
        '''Copy file to folder
        file - must have fuul path to target file
        Return: {
            "email": self.email,
            "body": NEW_FILE_PATH,
            "time": 1485452161339,
            "status": 200
        }'''
        return self.connect('POST', 'file/copy', {'home': file, 'conflict': 'rename', 'folder': folder})

    def file(self, file, batch=False):
        '''Return: {
            'time': 1485521913642,
            'body': {
                'count': {'files': 0, 'folders': 0},
                'tree': '343030336563623030303030',
                'type': 'folder',
                'home': file,
                'grev': 10445,
                'kind': 'folder',
                'name': 'tmp2',
                'rev': 10445
            },
            'email': self.email,
            'status': 200
        }
        If error: {
            'time': 1485521999307,
            'body': {
                'home': {'error': 'not_exists', 'value': file}
            },
            'email': self.email,
            'status': 404
        }
        '''
        method = 'file'
        params = {'home': file}
        if batch:
            return {'method': method, 'params': params}
        return self.connect('GET', method, params)

    def links(self):
        '''Receive all weblinks
        Return: [{
            "tree": "343030336563623030303030",
            "name": "",
            "grev": 4836,
            "size": 126276078,
            "kind": "folder",
            "weblink": "",
            "rev": 4833,
            "type": "folder",
            "home": ""
        },...]
        for weblink need https://cloud.mail.ru/public/weblink'''
        req = self.connect('GET', 'folder/shared/links')
        return req['body']['links']

    def add_file(self, file, size, file_hash, batch=False):
        method = 'file/add'
        params = {'home': file, 'conflict': 'rename', 'size': size, 'hash': file_hash}
        if batch:
            return {'method': method, 'params': params}
        return self.connect('POST', method, params)

    def batch(self, method, params):
        '''Apply one method for any objects
        method: Full method name
        params: {param_name: [values], ...}'''
        data = [{"method": method, "params": ''}]
        # [{"method":"file/remove","params":{"home":"/Новая+папка"}},{"method":"file/remove","params":{"home":"/test"}}]
        self.connect('POST', 'batch', data)
