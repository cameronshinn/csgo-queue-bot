# cacher.py

from . import mapdraft
import discord
from discord.ext import commands, tasks
import asyncio
import json
import os


class CacherCog(commands.Cog):
    """ Cog to handle the caching of guild data. """
    def __init__(self, bot, guild_data_file):
        self.bot = bot
        self.guild_data_file = guild_data_file

    @commands.Cog.listener()
    async def on_ready(self):
        """ Load guild data and start saving task. """
        # Wait for all other discord on_ready event handlers to finish
        tasks = [t for t in asyncio.Task.all_tasks() if type(t) is discord.client._ClientEventTask]
        tasks.remove(asyncio.Task.current_task())
        await asyncio.wait(tasks)

        # Load guild data
        print('Loading guild data...')
        self.load()
        print('Loaded guild data')

        # Start periodic save if it hasn't already begun
        if self.periodic_save.current_loop == 0:
            self.periodic_save.start()

    def save(self):
        """ Save guild data to JSON. """
        data = {}
        queue_cog = self.bot.get_cog('QueueCog')
        mapdraft_cog = self.bot.get_cog('MapDraftCog')

        # Save guild data for each guild
        for guild in self.bot.guilds:
            guild_queue = queue_cog.guild_queues.get(guild)
            guild_mdraft = mapdraft_cog.guild_mdraft_data.get(guild)
            guild_data = {}
            guild_data['queue'] = {}
            guild_data['queue']['active'] = [user.id for user in guild_queue.active]
            guild_data['queue']['bursted'] = [user.id for user in guild_queue.bursted]
            guild_data['queue']['capacity'] = guild_queue.capacity

            if mapdraft_cog:
                guild_data['mdraft'] = {}
                guild_data['mdraft']['map_pool'] = [m.dev_name for m in guild_mdraft.map_pool]

            data[str(guild.id)] = guild_data

        with open(self.guild_data_file, 'w+') as f:
            json.dump(data, f)  # Dump dict to JSON

    def load(self):
        """ Load guild data from JSON. """
        if not os.path.exists(self.guild_data_file):  # Check for guild data file first
            return

        queue_cog = self.bot.get_cog('QueueCog')
        mapdraft_cog = self.bot.get_cog('MapDraftCog')
        data = json.load(open(self.guild_data_file, 'r'))

        for guild_id, guild_data in data.items():
            guild = self.bot.get_guild(int(guild_id))

            if guild is None:
                continue

            guild_queue = queue_cog.guild_queues.get(guild)

            if guild_queue and 'queue' in guild_data:
                guild_queue.capacity = guild_data['queue']['capacity']
                active = guild_data['queue']['active']
                bursted = guild_data['queue']['bursted']
                guild_queue.active = [self.bot.get_user(id) for id in active if self.bot.get_user(id)]
                guild_queue.bursted = [self.bot.get_user(id) for id in bursted if self.bot.get_user(id)]

            if mapdraft_cog:  # Generic bot version doesn't have MapDraft cog
                guild_mdraft = mapdraft_cog.guild_mdraft_data.get(guild)
            else:
                continue

            if guild_mdraft and 'mdraft' in guild_data:
                all_maps = mapdraft.ALL_MAPS
                guild_mdraft.map_pool = [m for m in all_maps if m.dev_name in guild_data['mdraft']['map_pool']]

    @tasks.loop(minutes=10)
    async def periodic_save(self):
        """ Save guild data periodically. """
        self.save()
        print('Saved guild data')

    @commands.Cog.listener()
    async def on_disconenct(self):
        """ Save guild data on disconnect to be reloaded when ready. """
        self.save()
        print('Saved guild data')
