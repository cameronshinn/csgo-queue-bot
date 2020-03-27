# popflash.py

import discord
from discord.ext import commands

POPFLASH_BASE = 'https://popflash.site/scrim/'


class PopflashCog(commands.Cog):
    """ Cog to manage interactions with PopFlash. """

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.color = color
        self.popflash_base = POPFLASH_BASE

    def get_popflash_url(self, guild):
        """ Generate PopFlash URL based on guild name and ID. """
        sanitized_name = ''.join(char for char in str(guild) if char.isalpha() or char.isdigit())
        return self.popflash_base + sanitized_name + str(guild.id)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    @commands.command(brief='Link the server\'s designated PopFlash lobby')
    async def popflash(self, ctx):
        """ Send PopFlash link for the guild. """
        description = f'[Link here]({self.get_popflash_url(ctx.guild)})'
        embed = discord.Embed(title="PopFlash lobby is up!", description=description, color=self.color)
        await ctx.send(embed=embed)
