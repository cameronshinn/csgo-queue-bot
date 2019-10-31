#!/usr/bin/env python3
# dbl.py
# cameronshinn

import dbl
import asyncio
from discord.ext import commands, tasks

class DblCog(commands.Cog):
    """ Handles interactions with the top.gg API """

    def __init__(self, bot, dbl_token):
        """ Set attrivutes and get DBL client object """
        self.bot = bot
        self.dbl_token = dbl_token
        self.dbl_client = dbl.DBLClient(self.bot, self.dbl_token)
        self.update_stats.start()

    @tasks.loop(minutes=60)
    async def update_stats(self):
        """ Post server count to top.gg """
        print('Attempting to post server count to top.gg...')

        try:
            await self.dbl_client.post_guild_count()
            print(f'Posted server count ({self.dbl_client.guild_count()})\n')
        except Exception as e:
            raise Exception(f'Failed to post server count {type(e).__name__}\n')

    @update_stats.before_loop
    async def wait_bot_ready(self):
        """ Wait until the bot is ready before starting the update stats loop """
        await self.bot.wait_until_ready()
        await asyncio.sleep(1) # Give the bot time to run on_ready trigger first
