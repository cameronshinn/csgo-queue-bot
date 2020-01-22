#!/usr/bin/env python3
# donate.py
# cameronshinn

import discord
from discord.ext import commands


class DonateCog(commands.Cog):
    """ Cog to manage interactions with Donate Link """

    def __init__(self, bot, color, donate_url):
        """ Set attributes """
        self.bot = bot
        self.color = color
        self.donate_url = donate_url

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    @commands.command(brief='Link the server\'s designated Donation link')
    async def donate(self, ctx):
        description = f'[Link here]({self.donate_url})'
        embed = discord.Embed(title="Feel free to donate here: ", description=description, color=self.color)
        await ctx.send(embed=embed)
