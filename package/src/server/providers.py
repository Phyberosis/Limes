import json
from os import error
from typing import Any, Callable, Union
from threading import Thread, Condition

from flask import Flask, request

from limes_common import config, utils
from limes_common.models import Model, Primitive, server, provider
from limes_common.connections import Connection
from limes_common.connections.ssh import SshConnection
from limes_common.connections.statics.eLab import ELabConnection
from server.clientManager import Client, ClientManager
# from limes_common.models.provider import Result as Result

# _registeredProviders: dict[str, ProviderConnection] = {}
class ProviderReference:
    Con: Connection
    Schema: Union[provider.Schema, None]
    Lock: Condition
    LastUse: float

    def __init__(self, connection: Connection, schema: provider.Schema=None) -> None:
        self.Con = connection
        self.Schema = schema
        self.Lock = Condition()
        self.LastUse = 0.0

ProviderDictionary = dict[str, ProviderReference]

def _loadStatics() -> ProviderDictionary:
    print('## loading static providers')
    def GetSchema(ref: ProviderReference):
        s = ref.Con.GetSchema()
        # print(s.ToDict())
        if len(s.Services) > 0:
            ref.Lock.acquire()
            ref.Schema = s
            ref.LastUse = utils.current_time()
            ref.Lock.release

    try:
        with open(config.PROVIDER_STATICS_PATH, 'r') as raw:
            statics: list[dict] = json.loads("".join(raw.readlines()))
            loaded: ProviderDictionary = {}
            tasks: list[Thread] = []
            for p in statics:
                # todo add these strings to some config
                name = p.get('name', '')
                type = p.get('type', None)
                url = p.get('url', '')
                if type == 'ssh':
                    setup = p.get('setup', [])
                    command = p.get('command', '')
                    timeout = p.get('timeout', config.PROVIDER_DEFAULT_TRANSACTION_TIMEOUT)
                    keepAlive = p.get('keepAlive', config.PROVIDER_DEFAULT_CONNECTION_TIMEOUT)
                    idFile = p.get('identity', None)
                    con = SshConnection(url, setup, command, timeout, keepAlive, identityFile=idFile)
                    # con.AddOnResponseCallback(lambda s: print('>%s'%s))
                    loaded[name] = ProviderReference(
                        con,
                        con.GetSchema()
                    )
                    # print('s')
                    # tasks.append(Thread(target=GetSchema, args=[loaded[name]]))
                else:
                    print('unsupported provider type: [%s]' % (type))
            for t in tasks:
                t.daemon = True
                t.start()

        # if len(loaded) > 0:
        elabcon = ELabConnection()
        loaded['elab'] = ProviderReference(elabcon, elabcon.GetSchema())
        print('loaded %s' % len(loaded))
        return loaded
    except FileNotFoundError:
        print('!!! file [%s] required !!!' % config.PROVIDER_STATICS_PATH)
        return {}

import signal

class Handler:
    def __init__(self, views, clients: ClientManager) -> None:
        signal.signal(signal.SIGINT, self._shutdownConnections)
        self._clients = clients
        self._providers: ProviderDictionary = _loadStatics()
        for v in [self.List, self.ReloadProviders, self.ReloadCache, self.Search, self.Call]:
            views[v.__name__.lower()] = v

    def _shutdownConnections(self, x, y):
        for c in self._providers.values():
            try:
                c.Con.Close()
            except Exception:
                pass

    def _toRes(self, model: Model):
        return model.ToDict()

    def GetElabCon(self):
        def f() -> Any:
            return self._providers['elab'].Con
        con: ELabConnection = f()
        return con

    def List(self):
        res = server.List.Response()
        
        for k, info in self._providers.items():
            pi = server.ProviderInfo()
            pi.Name = k

            info.Lock.acquire()
            if info.Schema is not None:
                pi.Schema = info.Schema
            info.Lock.release()

            res.Providers.append(pi)
        return self._toRes(res)

    def ReloadProviders(self):
        for p in self._providers.values():
            p.Con.Close()
        self._providers: ProviderDictionary = _loadStatics()
        return self.List()

    def ReloadCache(self):
        con = self.GetElabCon()
        if con is not None:
            req = server.ReloadCache.Request.Parse(request.data)
            self._authProvider(con, req.ClientID)
            res = con.ReloadStorages()
            con.Logout()
            return self._toRes(server.ReloadCache.Response(res.Code))
        else:
            return self._toRes(server.ReloadCache.Response(500))


    def _authProvider(self, p: Connection, clientId: str):
        client = self._clients.Get(clientId)
        if client is not None: p.SetAuth(client.Token)

    def Search(self):
        req = server.Search.Request.Parse(request.data)
        res = server.Search.Response()
        res.Hits = {}
        def doSearch(name, p:Connection):
            self._authProvider(p, req.ClientID)
            r = p.Search(req.Query)
            p.Logout()
            if r.__dict__.get('Hits', None) is None: return
            for k, v in r.Hits.items():
                # todo: don't break the key
                k_withName = '%s_%s' % (name, k)
                res.Hits[k_withName] = v
        names = []
        for name, p in self._providers.items():
            doSearch(name, p.Con)
            names.append(name)
        res.Code = 200
        return self._toRes(res)

    def Call(self):
        req = server.CallProvider.Request.Parse(request.data)
        name = req.ProviderName
        p_req = req.RequestPayload

        theProvider = self._providers.get(name, None)
        res = server.CallProvider.Response()
        if theProvider is None:
            res.Code = 404
            res.Error = '[%s] is not a registered provider' % name
        else:
            self._authProvider(theProvider.Con, req.ClientID)
            p_res = theProvider.Con.MakeRequest(p_req)
            theProvider.Con.Logout()
            if isinstance(p_res, provider.GenericResponse):
                res.ResponsePayload = p_res
            else:
                g_res = provider.GenericResponse()
                g_res.Body = p_res.ToDict()
                res.ResponsePayload = g_res
        return self._toRes(res)