# dbl.py

import dbl
from discord.ext import commands, tasks


class DblCog(commands.Cog):
    """ Handles interactions with the Discord Bot Library API. """

    def __init__(self, bot, dbl_token):
        """ Set attributes and get DBL client object. """
        self.bot = bot
        self.dbl_token = dbl_token
        self.dbl_client = dbl.DBLClient(self.bot, self.dbl_token)
        self.topgg_url = 'https://top.gg/bot/{self.bot.user.id}'
        self.update_stats.start()

    @tasks.loop(minutes=60)
    async def update_stats(self):
        """ Post server count to Discord Bot Library. """
        print('Attempting to post server count to top.gg...')

        try:
            await self.dbl_client.post_guild_count()
            print(f'Posted server count ({self.dbl_client.guild_count()})\n')
        except Exception as e:
            raise Exception(f'Failed to post server count {type(e).__name__}\n')

    @update_stats.before_loop
    async def before_update_stats(self):
        """ Wait until bot is ready before posting server count. """
        await self.bot.wait_until_ready()
