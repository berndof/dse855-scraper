import os

from zabbix_utils import AsyncSender, ItemValue

from schemas import CollectedData, flatten_dataclass

server = os.getenv("ZABBIX_SERVER")
port = int(os.getenv("ZABBIX_PORT"))
zabbix_host = os.getenv("ZABBIX_HOST")


async def send_data(data:CollectedData):

    flat_data = flatten_dataclass(data)
    items = [
        ItemValue(zabbix_host, key, value)
        for key, value in flat_data.items()
        if value is not None
    ]
    print(items)

    sender = AsyncSender(server, port)
    try:
        response = await sender.send(items)
        return response
    except Exception as e:
        raise e