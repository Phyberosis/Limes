from limes_common.models.network.server import Login
from ..basic import AdvancedEnum, AbbreviatedEnum

class Http(AbbreviatedEnum):
    GET = 1,
    POST = 2,
    PUT = 3

class Endpoint(AdvancedEnum, AbbreviatedEnum):
    def __init__(self, _:int, methods: list[Http], path: str) -> None:
        self.ValidMethods: list[Http] = methods
        self.path = path

class ServerEndpoint(Endpoint):
    LOGIN = 1, [Http.POST], 'login'
    AUTHENTICATE = 2, [Http.POST], 'authenticate'
    INIT = 3, [Http.GET], 'init'

class ELabEndpoint(Endpoint):
    Login = 1, [Http.POST], 'auth/user'