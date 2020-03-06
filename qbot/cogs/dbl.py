#!/usr/bin/env python3
# dbl.py
# cameronshinn

import dbl
import asyncio
from discord.ext import commands, tasks


class DblCog(commands.Cog):
    """ Handles interactions with the Discord Bot Library API. """

    def __init__(self, bot, dbl_token):
        """ Set attrivutes and get DBL client object. """
        self.bot = bot
        self.dbl_token = dbl_token
        self.dbl_client = dbl.DBLClient(self.bot, self.dbl_token)
        self.topgg_url = 'https://top.gg/bot/{self.bot.user.id}'

    @tasks.loop(minutes=60)
    async def update_stats(self):
        """ Post server count to Discord Bot Library. """
        print('Attempting to post server count to top.gg...')

        try:
            await self.dbl_client.post_guild_count()
            print(f'Posted server count ({self.dbl_client.guild_count()})\n')
        except Exception as e:
            raise Exception(f'Failed to post server count {type(e).__name__}\n')

    @commands.Cog.listener()
    async def on_ready(self):
        """ Start periodic stat update. """
        self.update_stats.start()

    @commands.Cog.listener()
    async def on_disconnect(self):
        """ Stop periodic stat update. """
        self.update_stats.stop()
