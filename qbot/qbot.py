#!/usr/bin/env python3
# qbot.py
# cameronshinn

from discord.ext import commands

from cogs.cacher import CacherCog
from cogs.console import ConsoleCog
from cogs.dbl import DblCog
from cogs.help import HelpCog
from cogs.mapdraft import MapDraftCog
from cogs.popflash import PopflashCog
from cogs.queue import QueueCog
from cogs.teamdraft import TeamDraftCog
from cogs.donate import DonateCog

BOT_COLOR = 0x0D61B7
DATA_PATH = 'guild_data.json'


def run(discord_token, dbl_token=None, donate_url=None, generic=False):
    """ Create the bot, add the cogs and run it. """
    bot = commands.Bot(command_prefix=('q!', 'Q!'), case_insensitive=True)
    bot.add_cog(CacherCog(bot, DATA_PATH))
    bot.add_cog(ConsoleCog(bot))
    bot.add_cog(HelpCog(bot, BOT_COLOR))
    bot.add_cog(QueueCog(bot, BOT_COLOR))
    bot.add_cog(TeamDraftCog(bot, BOT_COLOR))

    if not generic:
        bot.add_cog(MapDraftCog(bot, BOT_COLOR))
        bot.add_cog(PopflashCog(bot, BOT_COLOR))
        bot.remove_command('cap')

    if dbl_token:
        bot.add_cog(DblCog(bot, dbl_token))

    if donate_url:
        bot.add_cog(DonateCog(bot, BOT_COLOR, donate_url))

    bot.run(discord_token)
