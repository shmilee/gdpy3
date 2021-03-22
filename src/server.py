# -*- coding: utf-8 -*-

# Copyright (c) 2021 shmilee

'''
Contains gdpy3 server class.
'''

import asyncio
import websockets
import json
import random
import string
import hmac

from .glogger import getGLogger
from .processors import Processor_Names, get_processor, is_processor
from .__about__ import __gversion__

__all__ = ['cli_script']

log = getGLogger('G')

class GdpServer(object):
    '''
    A TCP server to export gdp data.
    '''

    def __init__(self, ip, port, secret):
        self.ip = ip
        self.port = port
        self.__secret = secret
        self.processors = []
        self.processors_lib = {}
        self.clients = {}

    def add_processor(self, path, **kwargs):
        '''processor get by :func:`processors.get_processor`, rm visplter'''
        kwargs['add_visplter'] = None
        gdp = get_processor(path, **kwargs)
        if gdp.pckloader is None:
            log.error("Failed to add %s!" % path)
        else:
            key = (gdp.name, gdp.pckloader.path)
            if key in self.processors_lib:
                self.processors_lib[key] = None
            log.info("Add %s in server!" % path)
            self.processors_lib[key] = gdp
        self.processors = sorted(self.processors_lib.keys())

    def del_processor(self, path, name='all'):
        '''*name*: 'all' or Processor_Names'''
        if name == 'all':
            for key in self.processors_lib:
                if key[1] == path:
                    log.info("Delete %s in server!" % (key,))
                    self.processors_lib.pop(key)
        else:
            key = (name, path)
            if key in self.processors_lib:
                log.info("Delete %s in server!" % (key,))
                self.processors_lib.pop(key)
        self.processors = sorted(self.processors_lib.keys())

    def start(self, **kwargs):
        log.info("Bind to %s:%s" % (self.ip, self.port))
        runserver = websockets.serve(self.serve, self.ip, self.port, **kwargs)
        asyncio.get_event_loop().run_until_complete(runserver)
        asyncio.get_event_loop().run_forever()

    async def serve(self, ws, path):
        if await self.register(ws):
            log.info("Serve connection from %s:%s" % ws.remote_address)
            try:
                data = json.dumps({'processors': self.processors})
                await ws.send(data)
                async for msg in ws:
                    request = json.loads(msg)
                    if request['action'] == 'get_figlabels':
                        key = (request['name'], request['path'])
                        if key in self.processors_lib:
                            gdp = self.processors_lib[key]
                            data = json.dumps({'status': 200, 'figlabels': gdp.availablelabels})
                            await ws.send(data)
                        else:
                            await ws.send(json.dumps({'status': 404, 'reason': 'processor not found'}))
                    elif request['action'] == 'get_results':
                        key = (request['name'], request['path'])
                        figlabel = request['figlabel']
                        if key in self.processors_lib:
                            gdp = self.processors_lib[key]
                            data = gdp.export(figlabel, fmt='json')
                            await ws.send(data)
                        else:
                            await ws.send(json.dumps({'status': 404, 'reason': 'processor not found'}))
                    else:
                        log.error("unsupported action: {}", request['action'])
            finally:
                await self.unregister(ws)
        else:
            await ws.close()

    async def register(self, ws):
        log.info("Auth connection from %s:%s" % ws.remote_address)
        chars = string.ascii_letters + string.digits
        msg = ''.join(random.choices(chars, k=32))
        data = json.dumps({'msg': msg})
        await ws.send(data)
        h = hmac.new(self.__secret, bytes(msg, encoding='utf-8'), 'sha256')
        digest = h.hexdigest()
        response = await ws.recv()
        data = json.loads(response)
        if data['action'] == 'auth':
            if hmac.compare_digest(digest, data['digest']):
                log.info("Add client from %s:%s" % ws.remote_address)
                self.clients[ws] = digest
                await ws.send(json.dumps({'msg': 'OK'}))
                return True
            else:
                log.info("Wrong secret words from %s:%s" % ws.remote_address)
                fail = json.dumps({'msg': 'Wrong Secret'})
        else:
            log.info("Wrong action from %s:%s" % ws.remote_address)
            fail = json.dumps({'msg': 'Bad Request'})
        await ws.send(fail)
        return False

    async def unregister(self, ws):
        if not ws.closed:
            await ws.close()
        self.clients.pop(ws)

    # test client register
    async def auth(ip, secret):
        uri = "ws://%s:3601" % ip
        async with websockets.connect(uri) as ws:
            data = json.loads(await ws.recv())
            msg = bytes(data['msg'], encoding='utf-8')
            digest = hmac.new(secret, msg, 'sha256').hexdigest()
            data = json.dumps({'action': 'auth', 'digest': digest})
            await ws.send(data)
            response = await ws.recv()
            data = json.loads(response)
            log.info("Auth response: %s" % data['msg'])
            if data['msg'] == 'OK':
                response = await ws.recv()
                data = json.loads(response)
                print(data['processors'])
                name, path = data['processors'][0]
                request = json.dumps({'action': 'get_figlabels', 'name': name, 'path': path})
                await ws.send(request)
                response = await ws.recv()
                data = json.loads(response)
                print(data)
                request = json.dumps(
                    {'action': 'get_results', 'name': name, 'path': path, 'figlabel': data['figlabels'][0]})
                await ws.send(request)
                response = await ws.recv()
                data = json.loads(response)
                print(data)
                #async for response in ws:
    #asyncio.get_event_loop().run_until_complete(auth('', b''))
