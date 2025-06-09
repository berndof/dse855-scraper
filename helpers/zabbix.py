import os

from zabbix_utils import AsyncSender, ItemValue

from helpers.log import get_logger
from schemas import CollectedData, flatten_dataclass

server = os.getenv("ZABBIX_SERVER")
port = int(os.getenv("ZABBIX_PORT"))
zabbix_host = os.getenv("ZABBIX_HOST")

logger = get_logger("zabbix")

async def send_data(data:CollectedData):

    flat_data = flatten_dataclass(data)
    items = [
        ItemValue(zabbix_host, key, value)
        for key, value in flat_data.items()
        if value is not None
    ]
    sender = AsyncSender(server, port)
    try:
        response = await sender.send(items)
        return response
    except Exception as e:
        raise e