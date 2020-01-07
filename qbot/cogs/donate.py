#!/usr/bin/env python3
# popflash.py
# cameronshinn

import discord
from discord.ext import commands


class DonateCog(commands.Cog):
    """ Cog to manage interactions with Donate Link """

    def __init__(self, bot, color, donate_url):
        """ Set attributes """
        self.bot = bot
        self.color = color
        self.donate_token = donate_token

    def get_donation_url(self, guild):
        """ Generate Donation link based on specific bot instance """
        return self.donate_url

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    @commands.command(brief='Link the server\'s designated Donation link')
    async def donate(self, ctx):
        description = f'[Link here]({self.get_donation_url(ctx.guild)})'
        embed = discord.Embed(title="Feel free to donate here: ", description=description, color=self.color)
        await ctx.send(embed=embed)
