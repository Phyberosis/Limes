import json
from .testTools import Assert, BeforeAll, BeforeEach, PrintStats, Test

from limes_common.models.network import Model, SerializableTypes, provider as Provider

class TestModel(Model):
    def __init__(self, string = '', boolean = False, integer = 0) -> None:
        self.string = string
        self.boolean = boolean
        self.integer = integer

@BeforeAll
def all(env: dict):
    return env

@BeforeEach
def setup(env: dict):
    return env

class Inner(Model):
    def __init__(self, a: int = 0, b: str = '') -> None:
        self.a = a
        self.b = b

class Outer(Model):
    def __init__(self, x: str = '', inner: Inner = Inner()) -> None:
        self.x = x
        self.inner = inner

class TestTypesDict(SerializableTypes):
    INNER = Inner.Load, Inner()
    OUTER = Outer.Load, Outer()

@Test
def modelToDict(env: dict):
    string = 'asdf'
    boolean = False
    integer = 12565
    expected = """{"string": {"type": "<class 'str'>", "value": "%s"},
        "boolean": {"type": "<class 'bool'>", "value": %s},
        "integer": {"type": "<class 'int'>", "value": %s}}""" \
        % (string, str(boolean).lower(), integer)

    model = TestModel(string, boolean, integer)
    actual = json.dumps(model.ToDict())

    Assert.Equal(json.loads(actual), json.loads(expected))

@Test
def modelLoad(env: dict):
    string = 'le string'
    boolean = True
    integer = 9000
    serialized = '''{"string": {"type": "<class \'str\'>", "value": "%s"},
        "boolean": {"type": "<class \'bool\'>", "value": %s},
        "integer": {"type": "<class \'int\'>", "value": %s}}''' \
        % (string, str(boolean).lower(), integer)

    actual = TestModel.Load(json.loads(serialized))

    Assert.Equal(actual.string, string)
    Assert.Equal(actual.boolean, boolean)
    Assert.Equal(actual.integer, integer)

@Test
def nestedSerialize(env: dict):
    a = 25
    b = 'inside!'
    inner = Inner(a, b)
    x = 'le x string'
    outer = Outer(x, inner)
    actual = json.dumps(outer.ToDict())

    expected = '''{"x": {"type": "<class 'str'>", "value": "le x string"}, 
    "inner": {"type": "%s", "value": {
        "a": {"type": "<class 'int'>", "value": 25},
        "b": {"type": "<class 'str'>", "value": "inside!"}}}}''' % (Inner)

    Assert.Equal(json.loads(actual), json.loads(expected))

@Test
def nestedComplex(env: dict):
    class Complex(Model):
        def __init__(self, lst = [], dict = {}) -> None:
            self.List = lst
            self.Dict = dict

    com = Complex([
        1, 'lst', False,
        Inner(23, 'inner-lst')
    ], {
        'TF': True,
        'inner': Inner(2, 'inner-dict')
    })
    serialized = json.dumps(com.ToDict())

    back = Complex.Load(serialized, TestTypesDict)
    serialized2 = json.dumps(back.ToDict())
    Assert.Equal(serialized, serialized2)

@Test
def nestedLoad(env: dict):
    a = 25
    b = 'inside!'
    inner = Inner(a, b)
    x = 'le x string'
    expected = Outer(x, inner)

    serialized = '''{"x": {"type": "<class 'str'>", "value": "le x string"}, 
    "inner": {"type": "%s", "value": {
        "a": {"type": "<class 'int'>", "value": 25},
        "b": {"type": "<class 'str'>", "value": "inside!"}}}}''' % (Inner)
    
    actual_o = Outer.Load(serialized, TestTypesDict)
    Assert.Equal(actual_o.ToDict(), expected.ToDict())

PrintStats()