import os

from zabbix_utils import AsyncSender, ItemValue

server = os.getenv("ZABBIX_SERVER")
port = os.getenv("ZABBIX_PORT")
zabbix_host = os.getenv("ZABBIX_HOST")


async def send_data(data):

    items = [
        ItemValue(zabbix_host, key, value) for key, value in data.items()
        if value is not None
    ]

    sender = AsyncSender(zabbix_host, port)
    try:
        response = await sender.send(items)
        return response
    except Exception as e:
        raise e