import asyncio
import logging
import os

SLEEP_TIME = 24*60*60 # 24 hours
PREFIX = "backup : "

BACKUP_DIR = "./backup"

async def start_backup(logger: logging.Logger, msgQueue: asyncio.Queue):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    while True:
        try:
            exit_code = os.system(f'sudo /bin/bash ./backup.sh')
            if exit_code != 0:
                logger.error(PREFIX + "Error in creating backup, trying again...")
                await asyncio.sleep(10)
            else:
                logger.info(PREFIX + "New Backup created")
                msgQueue.put_nowait(True)
                await asyncio.sleep(SLEEP_TIME)
        except:
            logger.error(PREFIX + "Error in creating backup, trying again...")
            await asyncio.sleep(10)

def last_backup_time():
    if not os.path.exists(BACKUP_DIR):
        return ""
    
    files = os.listdir(BACKUP_DIR)
    if len(files) == 0:
        return ""
    
    files.sort()
    return files[-1][7:] # remove first 7 chars from backup_<time>