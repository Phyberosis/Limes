
from limes_provider import ProviderConnection
from limes_provider.passive import PassiveConnection
from limes_common import config

def GetList(passiveRecieveAddress: str, passiveRecievePort: int) -> list[ProviderConnection]:
    return []
    # return [
    #     PassiveConnection('FosDB', passiveRecieveAddress, passiveRecievePort)
    # ]