import argparse
import os
import sys
from pathlib import Path

from crontab import CronTab
from dotenv import load_dotenv
from log import get_logger

load_dotenv()
logger = get_logger("cron")

def create_cron_job():
    try:
        cron_interval = int(os.getenv("CRON_INTERVAL_MINUTES", 5))
        cron = CronTab(user=True)
        job = cron.new(
            command=f"/bin/bash {Path.cwd()}/run.sh",
            comment="dse855-scraper"
        )
        job.minute.every(cron_interval)
        cron.write()
        logger.debug("Cron job created")
    except Exception as e:
        logger.error(e)
        sys.exit(1)

def delete_cron_job():
    try:
        cron = CronTab(user=True)
        cron.remove_all(comment="dse855-scraper")
        cron.write()
        logger.debug("Cron job deleted")
    except Exception as e:
        logger.error(e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--create", action="store_true", help="Create cron job")
    group.add_argument("--delete", action="store_true", help="Delete cron job")

    args = parser.parse_args()

    if args.create:
        create_cron_job()
    elif args.delete:
        delete_cron_job()

    sys.exit(0)

if __name__ == "__main__":
    main()
