import asyncio
import logging
import logging.handlers
import os
from aiohttp import ClientSession
from dotenv import load_dotenv
import bot
import backup
from discord.ext import commands

async def Bot(logger: logging.Logger,msgQueue: asyncio.Queue):
    async with ClientSession() as web_client:
        async with bot.Bot(
            commands.when_mentioned,
            logger=logger,
            msgQueue=msgQueue,
            web_client=web_client,
            guild_id=os.getenv("GUILD_ID"),
            channel_id=os.getenv("CHANNEL_ID"),
        ) as client:
            await client.start(os.getenv("DISCORD_TOKEN"))

async def main():
    logger = logging.getLogger("logs")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename=f"./logs.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  #32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}]: {message}", date_format, style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    msgQueue = asyncio.Queue()

    await asyncio.gather(Bot(logger,msgQueue),backup.start_backup(logger,msgQueue))

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
    print("exiting")