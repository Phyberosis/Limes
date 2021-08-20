import os
from .testTools import Assert, BeforeAll, BeforeEach, PrintStats, Test

from limes_common.connections.server import ServerConnection
from limes_common.connections.eLab import ELabConnection
from limes_common import config

from limes_provider.passive import PassiveConnection

def getec(env) -> ELabConnection:
    return env['ec']
def getserv(env) -> ServerConnection:
    return env['serv']

@BeforeAll
def all(env: dict):
    env['ec'] = ELabConnection()
    env['serv'] = ServerConnection()
    return env

@BeforeEach
def setup(env: dict):
    return env

# @Test
# def elablogin(env: dict):
#     ec = getec(env)
#     ext = 'msl' if 'msl' in config.ELAB_URL else 'test' 
#     path = '../../credentials/elab.%s' % ext
#     u, p = list(line[:-1] for line in open(path, 'r').readlines()[:2])
    
#     res = ec.Login(u, p)
#     env['f'] = res.FirstName
#     env['l'] = res.LastName
#     Assert.Equal(res.Code, 200)
#     if res.Token is None or res.Token == '':
#         Assert.Fail()

# @Test
# def serverLogin(env: dict):
#     ext = 'msl' if 'msl' in config.ELAB_URL else 'test' 
#     path = '../../credentials/elab.%s' % ext
#     tok = list(line[:-1] for line in open(path, 'r').readlines())[2]
#     serv = getserv(env)
#     res = serv.Login(tok, 'test_FN', 'test_LN')

#     Assert.Equal(res.Success, True)
    

@Test
def providerPing(env: dict):
    #pinging local fosDB 
    url = 'local'
    setup = [
        'cd ~/workspace/Python/Limes/package/src',
        'conda activate limes'
    ]
    cmd = 'python -m fosDB'
    timeout = 3
    keepAlive = 10
    pc = PassiveConnection(url, setup, cmd, timeout, keepAlive)
    echo = 'test echo'
    stat = pc.CheckStatus(echo)
    Assert.Equal(stat.Online, True)
    Assert.Equal(stat.Echo, echo)
    pc.Dispose()

PrintStats()