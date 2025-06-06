#TODO logging
import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from helpers.log import get_logger, setup_logs
from helpers.zabbix import send_data
from scraper import Scraper, SessionController

load_dotenv()

setup_logs()
logger = get_logger("main")


async def main():
    async with async_playwright() as pw:
        session_controller = SessionController(pw)

        try:
            data = await session_controller.run()
            #await send_data(scraped_data)
            logger.debug(data)

        except Exception as e:
            logger.error(e)
            

        finally:
            await session_controller.stop()


if __name__ == "__main__":


    #get timeout value based on cron 
    cron_interval = int(os.getenv("CRON_INTERVAL_MINUTES", 5))
    timeout_value = (cron_interval * 60) - 10

    
    try: 
        asyncio.run(asyncio.wait_for(main(), timeout=timeout_value))

    except asyncio.TimeoutError as e:
        logger.error(e)

    
