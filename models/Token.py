# -*- coding: utf-8 -*-
#
import time
import hmac
import hashlib
import pprint
import requests
import json


class Token(object):

    def __init__(self, user):
        self.user = user

    def getToken(self, method, function, timestamp):
        data = "{0}{1}{2}".format(method, function, timestamp)
        p = hashlib.sha1()
        p.update(data)
        token = hmac.new(self._toSha256(self.user),
                         msg=p.hexdigest(),
                         digestmod=hashlib.sha256).hexdigest()
        return token

    def _toSha256(self, target):
        hash_object = hashlib.sha256(target)
        hex_dig = hash_object.hexdigest()
        return hex_dig

if __name__ == '__main__':
    token = Token('bobcarr')
    print time.time()
    print token.getToken('POST', 'notify', time.time())