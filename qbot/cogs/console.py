#!/usr/bin/env python3
# console.py
# cameronshinn

import datetime
from discord.ext import commands

class ConsoleCog(commands.Cog):
    """ Does the console printing of the bot """

    def __init__(self, bot):
        """ Set bot attribute """
        self.bot = bot

    @property
    def startup_banner(self):
        """ Banner string to show basic bot info """
        user_name = self.bot.user.name
        user_id = self.bot.user.id
        line = '=' * max(len(user_name), len(str(user_id)))
        return f'{line}\nLogged in as...\n{user_name}\n{user_id}\n{line}'

    @staticmethod
    def timestamp():
        """ Easy timestamp generation """
        return datetime.datetime.now().strftime("%x - [%X]")

    @commands.Cog.listener()
    async def on_ready(self):
        """ Print basic bot info and server list and sets status on startup """
        print(self.startup_banner)
        print(f'\nBot is online in {len(self.bot.guilds)} servers:')

        for guild in self.bot.guilds:
            print(f'    {guild}')

        print('')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """ Print command calls to the console """
        print(f'{self.timestamp()}\n    Command: {ctx.command}\n    Sender:  {ctx.author}\n    Guild:   {ctx.guild}\n')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Print guild adds to the console """
        print(f'{self.timestamp()}\n    Bot has been added to guild: {guild}\n')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Print guild removes to the console """
        print(f'{self.timestamp()}\n    Bot has been removed from guild: {guild}\n')
