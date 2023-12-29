import datetime
import json
import logging
from typing import Optional

import discord
from discord import app_commands
from aiohttp import ClientSession
import asyncio
import os
import socket
import backup
import docker_cmds

PREFIX = "bot : "

backend_socket_path = "/tmp/ras-backend.sock"

FRONTEND_CONTAINER_NAME = os.getenv("FRONTEND_CONTAINER_NAME","")
BACKEND_CONTAINER_NAME = os.getenv("BACKEND_CONTAINER_NAME","")
WEBSITE_CONTAINER_NAME = os.getenv("WEBSITE_CONTAINER_NAME","")

class Bot(discord.Client):
    def __init__(
        self,
	    *args,
        logger: logging.Logger,
        msgQueue: asyncio.Queue,
        web_client: ClientSession,
        guild_id: str = None,
        channel_id: str = None,
        intents: Optional[discord.Intents] = None,
    ):
        """Client initialization."""
        if intents is None:
            intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.logger = logger
        self.msgQueue = msgQueue
        self.web_client = web_client
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.tree = app_commands.CommandTree(self)
        self.guild = None
        self.channel = None

    async def on_ready(self):
        await self.wait_until_ready()

        self.guild = self.get_guild(int(self.guild_id))
        self.channel = self.guild.get_channel(int(self.channel_id))

        self.loop.create_task(self.sendBackupMsg())
        self.loop.create_task(self.listenForPanic())
        self.logger.info(PREFIX + f'Bot logged on as {self.user}!')

    async def sendBackupMsg(self):
        while not self.is_closed():
            await self.msgQueue.get()

            current_time = datetime.datetime.now()
            await self.channel.send(f"> New backup created at **{current_time}**")

    async def listenForPanic(self):
        try:
            if os.path.isdir(backend_socket_path):
                os.rmdir(backend_socket_path)
            else:
                os.unlink(backend_socket_path)
        except OSError:
            if os.path.exists(backend_socket_path):
                raise
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(backend_socket_path)
        sock.setblocking(False)

        sock.listen(1)
        self.logger.info(PREFIX+"listening for backend connection...")

        while not self.is_closed():
            conn,client_addr = await self.loop.sock_accept(sock)

            self.logger.info(PREFIX+"connection from "+str(client_addr))
            try:
                while not self.is_closed():
                    data = await self.loop.sock_recv(conn,4096)
                    if data:
                        try:
                            decoded_data = json.loads(data.decode("utf-8"))
                        except json.decoder.JSONDecodeError:
                            self.logger.error(PREFIX+"Error in decoding data")
                            continue
                        self.logger.info(PREFIX+f"received panic alert: {decoded_data}")
                        reply = f"Endpoint: {decoded_data['endpoint']} \n Error: {decoded_data['error']}"
                        embed = discord.Embed(title="PANIC", description=reply, color=0xff0000)
                        await self.channel.send(embed=embed)
                    else:
                        break
            except ConnectionResetError:
                self.logger.info(PREFIX+"connection reset by peer")
            self.logger.info(PREFIX+"closing connection")
            conn.close()
        sock.close()
        os.unlink(backend_socket_path)

    async def setup_hook(self) -> None:
        """Setup Hook."""
        self.tree.add_command(last_backup_time)
        self.tree.add_command(container_status)
        self.tree.add_command(restart_backend)
        self.tree.add_command(restart_frontend)
        self.tree.add_command(restart_website)
        await self.tree.sync()

@app_commands.command(name="last_backup_time", description="Last Backup Time")
async def last_backup_time(interaction: discord.Interaction):
    last_backup_time = backup.last_backup_time()
    if last_backup_time == "":
        reply = "No backup created yet"
    else:
        reply = f"{last_backup_time}"
    embed = discord.Embed(title="Last Backup Time", description=reply, color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@app_commands.command(name="restart_backend", description="Restart Backend Container")
async def restart_backend(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting Backend Container...")
    channel = interaction.channel
    ok,reply = docker_cmds.restart_container(BACKEND_CONTAINER_NAME)
    embed = discord.Embed(title="Restart Backend", description=reply, color=0x00ff00 if ok else 0xff0000)
    await channel.send(embed=embed)

@app_commands.command(name="restart_frontend", description="Restart Frontend Container")
async def restart_frontend(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting Frontend Container...")
    channel = interaction.channel
    ok,reply = docker_cmds.restart_container(FRONTEND_CONTAINER_NAME)
    embed = discord.Embed(title="Restart Frontend", description=reply, color=0x00ff00 if ok else 0xff0000)
    await channel.send(embed=embed)

@app_commands.command(name="restart_website", description="Restart Website Container")
async def restart_website(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting Website Container...")
    channel = interaction.channel
    ok,reply = docker_cmds.restart_container(WEBSITE_CONTAINER_NAME)
    embed = discord.Embed(title="Restart Website", description=reply, color=0x00ff00 if ok else 0xff0000)
    await channel.send(embed=embed)

@app_commands.command(name="container_status", description="Containers Status")
async def container_status(interaction: discord.Interaction):
    all_container_status = docker_cmds.get_running_containers_status()
    reply = ""
    for container_status in all_container_status:
        reply += f"{container_status} \n"
    if len(all_container_status) == 0:
        reply = "No containers created"
    embed = discord.Embed(title="Containers Status", description=reply, color=0x00ff00 if len(all_container_status) > 0 else 0xff0000)
    await interaction.response.send_message(embed=embed)