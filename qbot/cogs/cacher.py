#!/usr/bin/env python3
# cacher.py
# cameronshinn

import discord
from discord.ext import commands, tasks
import json
import os

from .queue import QQueue


class CacherCog(commands.Cog):
    """ Cog to handle the caching of guild data. """
    def __init__(self, bot, guild_data_file):
        self.bot = bot
        self.guild_data_file = guild_data_file

    def encode(self, obj):
        """ JSON encoding for queue bot objects. """
        enc = {'type': type(obj).__name__}

        if type(obj) is discord.User or type(obj) is discord.Member:
            enc['id'] = obj.id
        elif type(obj) is QQueue:
            enc['active'] = [self.encode(user) for user in obj.active]
            enc['capacity'] = obj.capacity
            enc['bursted'] = [self.encode(user) for user in obj.bursted]
        else:
            raise TypeError(f'Cannot encode {type(obj)} into a JSON format')

        return enc

    def save(self):
        """ Save guild data to JSON. """
        # Find bot's cogs with 'cache_data' property
        cache_cogs = (cog for cog in self.bot.cogs.values() if hasattr(cog, 'cache_data'))

        data = {} # Return combined guild dictionary with data from all cogs

        # Construct save dictionary
        for guild in self.bot.guilds:
            data[guild.id] = {}

            for cog in cache_cogs:
                if not cog.cache_data[guild].is_default:  # Check if data is non-default
                    data[guild.id][type(cog).__name__] = cog.cache_data[guild]

            # Check for guilds with no data to save and remove them
            if not data[guild.id]:  # Dict is empty
                data.pop(guild.id)

        # Dump JSON with custom default encoding
        json.dump(data, open(self.guild_data_file, 'w+'), default=self.encode)

    def load(self):
        """ Load guild data from JSON. """
        if not os.path.exists(self.guild_data_file):  # Check for guild data file first
            return

        undec = json.load(open(self.guild_data_file, 'r'))  # Read JSON into dictionary
        get_users = lambda users: [self.bot.get_user(u['id']) for u in users]  # Gets list of users from IDs

        for guild_id, guild_data in undec.items():
            guild = self.bot.get_guild(int(guild_id))  # Get guild from ID

            for cog_name, cog_data in guild_data.items():
                cog = self.bot.get_cog(cog_name)
                data_type = cog_data['type']  # Every encoding has 'type' field
                dec = {}  # Initial dict for decoded data

                if data_type == 'QQueue':
                    dec[guild] = QQueue(active=get_users(cog_data['active']),
                                        capacity=cog_data['capacity'],
                                        bursted=get_users(cog_data['bursted']))
                else:
                    raise TypeError(f'Cannot decode {data_type} from a JSON format.')

                cog.cache_data = dec

    @tasks.loop(minutes=10)
    async def periodic_save(self):
        """ Save guild data periodically. """
        self.save()
        print('Saved guild data')

    @commands.Cog.listener()
    async def on_ready(self):
        """ Load guild data and start periodic saving. """
        self.load()
        self.periodic_save.start()

    @commands.Cog.listener()
    async def on_disconenct(self):
        """ Save guild data on disconnect to be reloaded when ready. """
        self.save()
