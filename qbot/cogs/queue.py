#!/usr/bin/env python3
# queue.py
# cameronshinn

import asyncio
import discord
from discord.ext import commands, tasks

class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers """

    def __init__(self, bot, color):
        """ Set attributes """
        self.bot = bot
        self.spots = 10
        self.guild_queues = {} # Maps guild -> list of players in the queue for that guild
        self.popped_guild_queues = {} # MAps guild -> the most recent queue filled
        self.color = color

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each giuld the bot is in """
        for guild in self.bot.guilds:
            self.guild_queues[guild] = []
            self.popped_guild_queues[guild] = None

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added """
        self.guild_queues[guild] = []
        self.popped_guild_queues[guild] = None

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed """
        self.guild_queues.pop(guild, None)
        self.popped_guild_queues.pop(guild, None)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    @commands.command(brief='Join the queue')
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so """
        queue = self.guild_queues[ctx.guild]

        # if ctx.author in queue: # Author already in queue
        #     join_embed = discord.Embed(title=f'**{ctx.author.display_name}** is already in the queue', color=self.color)
        if len(queue) >= self.spots: # Queue full TODO: make elif
            join_embed = discord.Embed(title=f'Unable to add **{ctx.author.display_name}**\nQueue is full _({len(queue)}/{self.spots})_', color=self.color)
        else: # Open spot in queue
            queue.append(ctx.author)
            join_embed = discord.Embed(title=f'**{ctx.author.display_name}** has been added to the queue _({len(queue)}/{self.spots})_', color=self.color)

        # Check and pop queue if full
        if len(queue) == self.spots:
            self.popped_guild_queues[ctx.guild] = self.guild_queues.pop(ctx.guild, None) # Save who was in the queue for player draft
            self.guild_queues[ctx.guild] = [] # Reset the player queue to empty
            user_mentions = ''

            for user in queue:
                user_mentions += user.mention

            popflash_cog = self.bot.get_cog('PopflashCog') # NOTE: This is tied to the PopflashCog name so they need to be the same!

            if popflash_cog:
                popflash_url = popflash_cog.get_popflash_url(ctx.guild)
                description = f'[Join the PopFlash lobby here]({popflash_url})'
            else:
                description = ''

            pop_embed = discord.Embed(title='Queue has filled up!', description=description, color=self.color)
            await ctx.send(embed=join_embed)
            await ctx.trigger_typing()
            await ctx.send(user_mentions, embed=pop_embed)
        else:
            await ctx.send(embed=join_embed)

    @commands.command(brief='Leave the queue')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue:
            queue.remove(ctx.author)
            embed = discord.Embed(title=f'**{ctx.author.display_name}** has been removed from the queue _({len(queue)}/{self.spots})_', color=self.color)
        else:
            embed = discord.Embed(title=f'**{ctx.author.display_name}** was never in the queue', color=self.color)

        await ctx.channel.send(embed=embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """  Display the queue as an embed list of mentioned names """
        queue = self.guild_queues[ctx.guild]

        if queue != []: # If there are users in the queue
            enum_queue = enumerate(queue, start=1)
            queue_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enum_queue)
        else: # No users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title='__Players in queue for 10-mans__', description=queue_str, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue')
    async def empty(self, ctx):
        """ Reset the guild queue list to empty """
        queue = self.guild_queues[ctx.guild]
        queue.clear()
        embed = discord.Embed(title=f'The queue has been emptied _({len(queue)}/{self.spots})_', color=self.color)
        await ctx.send(embed=embed)
