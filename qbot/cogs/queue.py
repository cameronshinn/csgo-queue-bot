#!/usr/bin/env python3
# queue.py
# cameronshinn

import discord
from discord.ext import commands

class QQueue:
    """ Queue class for the bot. """

    def __init__(self, active=[], capacity=10, bursted=None, timeout=None):
        """ Set attributes. """
        self.active = active  # List of players in the queue
        self.capacity = capacity  # Max queue size
        self.bursted = bursted  # Cached lst filled queue
        # self.timeout = timeout  # Number of minutes of inactivity after which to empty the queue


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.guild_queues = {}  # Maps Guild -> QQueue
        self.color = color

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each giuld the bot is in. """
        for guild in self.bot.guilds:
            self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added. """
        self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed. """
        self.guild_queues.pop(guild, None)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    def cap_str(self, guild):
        """ Generate string showing how full queue is. """
        queue = self.guild_queues[guild]
        return f'({len(queue.active)}/{queue.capacity})'

    def burst_queue(self, guild):
        queue = self.guild_queues[guild]
        queue.bursted = queue.active  # Save bursted queue for player draft
        queue.active = []  # Reset the player queue to empty
        user_mentions = ''.join(user.mention for user in queue.bursted)
        popflash_cog = self.bot.get_cog('PopflashCog')

        if popflash_cog:
            popflash_url = popflash_cog.get_popflash_url(guild)
            description = f'[Join the PopFlash lobby here]({popflash_url})'
        else:
            description = ''

        pop_embed = discord.Embed(title='Queue has filled up!', description=description, color=self.color)
        return pop_embed, user_mentions

    @commands.command(brief='Join the queue')
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:  # Author already in queue
            join_embed = discord.Embed(title=f'**{ctx.author.display_name}** is already in the queue', color=self.color)
        elif len(queue.active) >= queue.capacity:  # Queue full
            title = f'Unable to add **{ctx.author.display_name}**\nQueue is full ({len(queue.active)}/{queue.capacity})'
            join_embed = discord.Embed(title=title, color=self.color)
        else:  # Open spot in queue
            queue.active.append(ctx.author)
            title = f'**{ctx.author.display_name}** has been added to the queue {self.cap_str(ctx.guild)}'
            join_embed = discord.Embed(title=title, color=self.color)

        # Check and burst queue if full
        if len(queue.active) == queue.capacity:
            pop_embed, user_mentions = self.burst_queue(ctx.guild)
            await ctx.send(embed=join_embed)
            await ctx.trigger_typing()  # Need to retrigger typing for second send
            await ctx.send(user_mentions, embed=pop_embed)
        else:
            await ctx.send(embed=join_embed)

    @commands.command(brief='Leave the queue')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:
            queue.active.remove(ctx.author)
            title = f'**{ctx.author.display_name}** has been removed from the queue {self.cap_str(ctx.guild)}'
            embed = discord.Embed(title=title, color=self.color)
        else:
            embed = discord.Embed(title=f'**{ctx.author.display_name}** isn\'t in the queue', color=self.color)

        await ctx.channel.send(embed=embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """  Display the queue as an embed list of mentioned names. """
        queue = self.guild_queues[ctx.guild]

        if queue.active != []:  # If there are users in the queue
            queue_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.active, start=1))
        else:  # No users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title='__Players in queue for 10-mans__', description=queue_str, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        await ctx.send(embed=embed)

    @commands.command(usage='q!remove <user mention>',
                      brief='Remove the mentioned user from the queue (Must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.color)
        else:
            queue = self.guild_queues[ctx.guild]

            if removee in queue.active:
                queue.active.remove(removee)
                title = f'**{removee.display_name}** has been removed from the queue {self.cap_str(ctx.guild)}'
                embed = discord.Embed(title=title, color=self.color)
            elif queue.bursted and removee in queue.bursted:
                queue.bursted.remove(removee)
                embed = discord.Embed(title=f'**{removee.display_name}** has been removed from the filled queue',
                                      color=self.color)
                await ctx.send(embed=embed)

                if len(queue.active) >= 1:
                    await ctx.trigger_typing()  # Need to retrigger typing for second send
                    saved_queue = queue.active.copy()
                    first_in_queue = saved_queue[0]
                    queue.active = queue.bursted + [first_in_queue]
                    queue.bursted = None
                    pop_embed, user_mentions = self.burst_queue(ctx.guild)
                    await ctx.send(user_mentions, embed=pop_embed)

                    if len(queue.active) > 1:
                        queue.active = saved_queue[1:]
                else:
                    queue.active = queue.bursted
                    queue.bursted = None

                return
            else:
                title = f'**{removee.display_name}** is not in the queue or the most recent filled queue'
                embed = discord.Embed(title=title, color=self.color)

        await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue (Must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        queue = self.guild_queues[ctx.guild]
        queue.active.clear()
        embed = discord.Embed(title=f'The queue has been emptied {self.cap_str(ctx.guild)}', color=self.color)
        await ctx.send(embed=embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            """ Respond to a permissions error with an explanation message. """
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot remove players without permission to {missing_perm}!'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)
