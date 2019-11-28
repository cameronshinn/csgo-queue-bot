#!/usr/bin/env python3
# popflash.py
# cameronshinn

import discord
from discord.ext import commands

POPFLASH_URL = 'https://popflash.site/scrim/'

class PopflashCog(commands.Cog):
    """ Cog to manage interactions with PopFlash """

    def __init__(self, bot, color):
        """ Set attributes """
        self.bot = bot
        self.color = color
        self.popflash_url = POPFLASH_URL

    def get_popflash_url(self, guild):
        """ Generate PopFlash URL based on guild name and ID """
        return self.popflash_url + ''.join(char for char in str(guild) if char.isalpha() or char.isdigit()) + str(guild.id)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    @commands.command(brief='Link the server\'s designated PopFlash lobby')
    async def popflash(self, ctx):
        description = f'[Link here]({self.get_popflash_url(ctx.guild)})'
        embed = discord.Embed(title="PopFlash lobby is up!", description=description, color=self.color)
        await ctx.send(embed=embed)
