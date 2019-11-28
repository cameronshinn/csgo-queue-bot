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

    def pop_queue(self, ctx):
        self.popped_guild_queues[ctx.guild] = self.guild_queues.pop(ctx.guild, None) # Save who was in the queue for player draft
        self.guild_queues[ctx.guild] = [] # Reset the player queue to empty
        user_mentions = ''

        for user in self.popped_guild_queues[ctx.guild]:
            user_mentions += user.mention

        popflash_cog = self.bot.get_cog('PopflashCog') # NOTE: This is tied to the PopflashCog name so they need to be the same!

        if popflash_cog:
            popflash_url = popflash_cog.get_popflash_url(ctx.guild)
            description = f'[Join the PopFlash lobby here]({popflash_url})'
        else:
            description = ''

        pop_embed = discord.Embed(title='Queue has filled up!', description=description, color=self.color)
        return user_mentions, pop_embed

    @commands.command(brief='Join the queue')
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue: # Author already in queue
            join_embed = discord.Embed(title=f'**{ctx.author.display_name}** is already in the queue', color=self.color)
        elif len(queue) >= self.spots: # Queue full
            join_embed = discord.Embed(title=f'Unable to add **{ctx.author.display_name}**\nQueue is full _({len(queue)}/{self.spots})_', color=self.color)
        else: # Open spot in queue
            queue.append(ctx.author)
            join_embed = discord.Embed(title=f'**{ctx.author.display_name}** has been added to the queue _({len(queue)}/{self.spots})_', color=self.color)

        # Check and pop queue if full
        if len(queue) == self.spots:
            user_mentions, pop_embed = self.pop_queue(ctx)
            await ctx.send(embed=join_embed)
            await ctx.trigger_typing() # Need to retrigger typing for second send
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
            embed = discord.Embed(title=f'**{ctx.author.display_name}** isn\'t in the queue', color=self.color)

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

    @commands.command(usage='q!remove \{user mention\}', brief='Remove the mentioned user from the queue (Must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        try:
            removee = ctx.message.mentions[0]
        except IndexError as e:
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.color)
        else:
            queue = self.guild_queues[ctx.guild]
            last_popped_queue = self.popped_guild_queues[ctx.guild]

            if removee in queue:
                queue.remove(removee)
                embed = discord.Embed(title=f'**{removee}** has been removed from the queue _({len(queue)}/{self.spots})_', color=self.color)
            elif removee in last_popped_queue:
                last_popped_queue.remove(removee)
                embed = discord.Embed(title=f'**{removee}** has been removed from the popped queue', color=self.color)
                await ctx.send(embed=embed)

                if len(queue) >= 1:
                    await ctx.trigger_typing() # Need to retrigger typing for second send
                    save_queue = queue[:]
                    first_in_queue = save_queue[0]
                    self.guild_queues[ctx.guild] = last_popped_queue + [first_in_queue]
                    last_popped_queue = None
                    user_mentions, pop_embed = self.pop_queue(ctx)
                    await ctx.send(user_mentions, embed=pop_embed)

                    if len(queue) > 1:
                        self.guild_queues[ctx.guild] = save_queue[1:]
                else:
                    self.guild_queues[ctx.guild] = last_popped_queue
                    last_popped_queue = None

                return
            else:
                embed = discord.Embed(title=f'**{removee}** is not in the queue or the most recent popped queue', color=self.color)

        await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue (Must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty """
        queue = self.guild_queues[ctx.guild]
        queue.clear()
        embed = discord.Embed(title=f'The queue has been emptied _({len(queue)}/{self.spots})_', color=self.color)
        await ctx.send(embed=embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            embed = discord.Embed(title=f'Cannot remove players without permission to {missing_perm}!', color=self.color)
            await ctx.send(embed=embed)
