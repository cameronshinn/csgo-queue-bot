# qbot.py

from discord.ext import commands
import cogs

BOT_COLOR = 0x0D61B7
DATA_PATH = 'guild_data.json'


def run(discord_token, dbl_token=None, donate_url=None, generic=False):
    """ Create the bot, add the cogs and run it. """
    bot = commands.Bot(command_prefix=('q!', 'Q!'), case_insensitive=True)
    bot.add_cog(cogs.CacherCog(bot, DATA_PATH))
    bot.add_cog(cogs.ConsoleCog(bot))
    bot.add_cog(cogs.HelpCog(bot, BOT_COLOR))
    bot.add_cog(cogs.QueueCog(bot, BOT_COLOR))
    bot.add_cog(cogs.TeamDraftCog(bot, BOT_COLOR))

    if not generic:
        bot.add_cog(cogs.MapDraftCog(bot, BOT_COLOR))
        bot.add_cog(cogs.PopflashCog(bot, BOT_COLOR))

    if dbl_token:
        bot.add_cog(cogs.DblCog(bot, dbl_token))

    if donate_url:
        bot.add_cog(cogs.DonateCog(bot, BOT_COLOR, donate_url))

    bot.run(discord_token)
