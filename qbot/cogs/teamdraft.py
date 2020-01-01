#!/usr/bin/env python3
# teamdraft.py
# cameronshinn

import discord
from discord.ext import commands

EMOJI_LIST = [u'\u0031\u20E3',
              u'\u0032\u20E3',
              u'\u0033\u20E3',
              u'\u0034\u20E3',
              u'\u0035\u20E3',
              u'\u0036\u20E3',
              u'\u0037\u20E3',
              u'\u0038\u20E3',
              u'\u0039\u20E3',
              u'\U0001F51F']

class TeamDraftCog(commands.Cog):
    """ Handles the player drafter command """

    def __init__(self, bot, color):
        """ Set attributes and initialize empty draft teams """
        self.bot = bot
        self.color = color
        self.guild_player_pool = {} # Players participating in the draft for each guild
        self.guild_teams = {} # Teams for each guild
        self.guild_msgs = {} # Last team draft embed message sent for each guild

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each giuld the bot is in """
        for guild in self.bot.guilds:
            self.guild_player_pool[guild] = []
            self.guild_teams[guild] = [[], []]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added """
        self.guild_player_pool[guild] = []
        self.guild_teams[guild] = [[], []]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed """
        self.guild_player_pool.pop(guild, None)
        self.guild_teams.pop(guild, None)
        self.guild_msgs.pop(guild, None)

    def player_draft_embed(self, title, guild):
        """ Return the player draft embed based on the guild attributes """
        team_1 = self.guild_teams[guild][0]
        team_2 = self.guild_teams[guild][1]
        embed = discord.Embed(title=title, color=self.color)
        x_emoji = ':heavy_multiplication_x:'
        players_left_str = ''

        for e, p in self.guild_player_pool[guild].items():
            if p not in team_1 and p not in team_2:
                players_left_str += f'{e}  {p.display_name}\n'
            else:
                players_left_str += f'{x_emoji}  ~~{p.display_name}~~\n'

        def embed_team(team):
            team_name = 'Team' if len(team) == 0 else f'Team {team[0].display_name}'

            if len(team) == 0:
                team_players = '_Empty_'
            else:
                team_players = '\n'.join(p.display_name for p in team)

            embed.add_field(name=f'__{team_name}__', value=team_players)

        embed_team(team_1)
        embed.add_field(name='__Players Left__', value=players_left_str, inline=True)
        embed_team(team_2)
        return embed

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    @commands.command(brief='Start (or restart) a player draft from the last popped queue')
    async def tdraft(self, ctx):
        """ Start a player draft by sending a player draft embed panel """
        x_emoji = ':heavy_multiplication_x'
        queue_cog = self.bot.get_cog('QueueCog')
        players = queue_cog.popped_guild_queues.get(ctx.guild)

        if players is None:
            in_queue = len(queue_cog.guild_queues[ctx.guild])
            spots = queue_cog.spots
            embed = discord.Embed(title=f'Cannot start player draft until the queue is full! _({in_queue}/{spots})_', color=self.color)
        else:
            self.guild_player_pool[ctx.guild] = dict(zip(EMOJI_LIST, players))
            self.guild_teams[ctx.guild] = [[], []]
            embed = self.player_draft_embed('Team draft has begun!', ctx.guild)

        msg = await ctx.send(embed=embed)

        if players is not None:
            for emoji in EMOJI_LIST:
                await msg.add_reaction(emoji)

        self.guild_msgs[ctx.guild] = msg

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return

        guild = user.guild

        if guild not in self.guild_msgs.keys() or reaction.message.id != self.guild_msgs[guild].id:
            return

        players = self.guild_player_pool[guild] # Get player dictionary for corresponding guild
        player_pick = players.get(str(reaction.emoji))
        team_1 = self.guild_teams[guild][0]
        team_2 = self.guild_teams[guild][1]

        if user not in [p for e, p in players.items()]: # TODO: Change player dict to list
            return

        # Ignore if emoji doesn't correspond to player or they're already on a team
        if player_pick is None or player_pick in team_1 or player_pick in team_2:
            return

        # Check if user isn't in a team and no new teams can be made
        if user not in team_1 and user not in team_2 and len(team_1) != 0 and len(team_2) != 0:
            title = f'Cannot make a new team for **{user.display_name}**'
        else:
            async for u in reaction.users():
                await reaction.remove(u)

            if user in team_1:
                team_1.append(player_pick)
                picked_team = team_1
            elif user in team_2:
                team_2.append(player_pick)
                picked_team = team_2
            elif len(team_1) == 0:
                team_1.append(user)
                team_1.append(player_pick)
                picked_team = team_1
            elif len(team_2) == 0:
                team_2.append(user)
                team_2.append(player_pick)
                picked_team = team_2

            title = f'**{user.display_name}** picked **{player_pick.display_name}** for **Team {picked_team[0].display_name}**'

        embed = self.player_draft_embed(title, guild)
        await self.guild_msgs[guild].edit(embed=embed)
