# qbot.py
# cameronshinn

import asyncio
import copy
import datetime
import discord
import time

import maps

LOGO_COLOR = 0xF4B903
THUMBNAIL = 'https://i.imgur.com/5v6mLwb.png'
POPFLASH_URL = 'https://popflash.site/scrim/'
GITHUB = 'github.com/cameronshinn/csgo-queue-bot'

class QueueGuild:
    def __init__(self, guild):
        self.spaces = 10
        self.guild = guild # Guild that class instance belongs to
        self.queue = [] # Where users in queue are held
        self.map_pool = [
            maps.de_cache,
            maps.de_dust2,
            maps.de_inferno,
            maps.de_mirage,
            maps.de_nuke,
            maps.de_overpass,
            maps.de_train
        ]
        self.maps_left = None # Set to None when there is no ongoing map draft
        self.teams = {} # Where teams are stored when drafting (team name : list of members)
        self.players_left = None # Set to None when there is no ongoing player draft
        self.command_vector = { 'q!help':     self.help_command, # Map command strings to handler functions for easy lookup
                               'q!join':     self.join_command,
                               'q!leave':    self.leave_command,
                               'q!view':     self.view_command,
                               'q!empty':    self.empty_command,
                               'q!popflash': self.popflash_command,
                               'q!mdraft':   self.mdraft_command,
                               'q!ban':      self.ban_command,
                               'q!pdraft':   self.pdraft_command,
                               'q!pick':     self.pick_command,
                               'q!about':    self.about_command }
        self.thumbnail_url = THUMBNAIL
        self.color = LOGO_COLOR

    @property
    def help_embed(self):
        embed = discord.Embed(title='__Queue Commands__', color=self.color)
        embed.add_field(name='`q!help`', value='Display help message page', inline=False)
        embed.add_field(name='`q!join`', value='Join the queue', inline=False)
        embed.add_field(name='`q!leave`', value='Leave the queue', inline=False)
        embed.add_field(name='`q!view`', value='Display who is currently in the queue', inline=False)
        embed.add_field(name='`q!empty`', value='Empty the queue', inline=False)
        embed.add_field(name='`q!popflash`', value='Link this server\'s designated PopFlash lobby', inline=False)
        embed.add_field(name='`q!mdraft`', value='Start (or restart) a map draft', inline=False)
        embed.add_field(name='`q!ban <map/number>`', value='Ban the specified map from the map draft', inline=False)
        embed.add_field(name='`q!pdraft`', value='Start (or restart) a player draft', inline=False)
        embed.add_field(name='`q!pick <number>`', value='Pick a player for your team', inline=False)
        embed.add_field(name='`q!about`', value='Display information about the 10-ManQ bot', inline=False)
        return embed

    @property
    def queue_embed(self):
        if self.queue: # If there are users in the queue
            enum_queue = enumerate(self.queue, start=1)
            queue_str = ''.join(f'{enumUser[0]}. {enumUser[1].display_name}\n' for enumUser in enum_queue)
        else: # No users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title='__Players in queue for 10-mans__', description=queue_str, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    @property
    def popflash_embed(self): # Set with property decorator since the server name can change over time
        guild_url = POPFLASH_URL + ''.join(char.lower() for char in str(self.guild) if char.isalpha() or char.isdigit())
        return discord.Embed(title="PopFlash lobby is up!", description=guild_url, color=self.color)

    @property
    def pdraft_str(self):
        if self.players_left == None:
            return None

        temp_str = ''

        if not self.players_left == []:
            temp_str += '__Players Left__\n' + ''.join(f'{i}. {p.display_name}\n' for i, p in enumerate(self.players_left, 1))

        if len(self.teams) != 0:
            for team in self.teams.keys():
                temp_str += f'\n__{team}__\n' + ''.join(p.display_name + '\n' for p in self.teams[team])

        return temp_str
    
    @property
    def about_embed(self):
        embed = discord.Embed(title='__10-ManQ Queue Bot__', description='The definitive bot for setting up 10-man lobbies', color=self.color)
        embed.set_thumbnail(url=self.thumbnail_url)
        embed.add_field(name='This bot was made to give CS:GO players a convenient way to find Discord server members who want to play in-house pickup games', value=GITHUB, inline=False)
        return embed

    async def join_command(self, message):
        if message.author in self.queue: # User already in queue
            embed = discord.Embed(title=f'**{message.author.display_name}** is already in the queue', color=self.color)
        if len(self.queue) >= self.spaces: # Queue full
            embed = discord.Embed(title=f'Unable to add **{message.author.display_name}**\nQueue is full _({len(self.queue)}/{self.spaces})_', color=self.color)
        else: # Space available and not already in queue
            self.queue.append(message.author)
            embed = discord.Embed(title=f'**{message.author.display_name}** has been added to the queue _({len(self.queue)}/{self.spaces})_', color=self.color)

        await message.channel.send(embed=embed)

        # Check and pop queue if full
        if len(self.queue) == self.spaces:
            user_mentions = ''    
                
            for user in self.queue:
                user_mentions += user.mention + ' '
            
            await message.channel.send(user_mentions, embed=self.popflash_embed)

    async def leave_command(self, message):
        if message.author in self.queue:
            self.queue.remove(message.author)
            embed = discord.Embed(title=f'**{message.author.display_name}** has been removed from the queue _({len(self.queue)}/{self.spaces})_', color=self.color)
        else:
            embed = discord.Embed(title=f'**{message.author.display_name}** was never in the queue', color=self.color)

        await message.channel.send(embed=embed)

    async def view_command(self, message):
        await message.channel.send(embed=self.queue_embed)

    async def start_command(self, message):
        user_mentions = ''    
            
        for user in self.queue:
            user_mentions += str(user.id) + ' '
        
        self.queue.clear()

        await message.channel.send(user_mentions, embed=self.popflash_embed)

    async def empty_command(self, message):
        self.queue.clear()
        embed = discord.Embed(title=f'The queue has been emptied _({len(self.queue)}/{self.spaces})_', color=self.color)
        await message.channel.send(embed=embed)

    async def help_command(self, message):
        await message.channel.send(embed=self.help_embed)

    async def popflash_command(self, message):
        await message.channel.send(embed=self.popflash_embed)

    async def mdraft_command(self, message):
        self.maps_left = copy.copy(self.map_pool) # Need to copy to preseve the original map pool
        maps_left_str = ''.join(f'{i}. {m.name}\n' for i, m in enumerate(self.maps_left, 1))
        embed = discord.Embed(title=f'Map draft has begun!', description=maps_left_str, color=self.color)
        await message.channel.send(embed=embed)

    async def ban_command(self, message):
        map_pick = message.content.split(' ', 1)[1] # Remove command from input

        # Check if map number specified and convert to map name if so
        if map_pick.isdigit() and int(map_pick) > 0 and int(map_pick) <= len(self.map_pool): # Check if digit and in range
            i = int(map_pick)
            map_pick = self.map_pool[i - 1] # Convert to map name
        else: # Look for map string in map names
            for m in self.map_pool:
                if m.name.lower() == map_pick.lower():
                    map_pick = m
                    break


        if self.maps_left == None: # Will only ever be None when there's no active map draft
            embed = discord.Embed(title='Map draft has not started!', color=self.color)
        elif map_pick in self.maps_left: # Remove map from remaining
            self.maps_left.remove(map_pick)
            maps_left_str = ''.join([f'{i}. {m.name}\n' if m in self.maps_left else f'{i}. ~~{m.name}~~\n' for i, m in enumerate(self.map_pool, 1)])
            embed = discord.Embed(title=f'**{map_pick.name}** has been banned', description=maps_left_str, color=self.color)
            embed.set_thumbnail(url=map_pick.image_url)
        elif map_pick in self.map_pool: # Otherwise map must already be banned
            maps_left_str = ''.join([f'{i}. {m.name}\n' if m in self.maps_left else f'{i}. ~~{m.name}~~\n' for i, m in enumerate(self.map_pool, 1)])
            embed = discord.Embed(title=f'**{map_pick.name}** has already been banned', description=maps_left_str, color=self.color)
            embed.set_thumbnail(url=map_pick.image_url)
        else: # Otherwise input is not map
            embed = discord.Embed(title=f'{map_pick} is not a map', color=self.color)

        if self.maps_left != None and len(self.maps_left) == 1: # End draft when no choices left
            embed = discord.Embed(title=f'We\'re going to **{self.maps_left[0].name}**!', color=self.color)
            embed.set_thumbnail(url=self.maps_left[0].image_url)
            embed.set_footer(text=f'Be sure to select {self.maps_left[0].name} in the PopFlash lobby')
            self.maps_left = None # Set to None when there is no ongoing map draft

        await message.channel.send(embed=embed)

    async def pdraft_command(self, message):
        # if not len(self.queue) == self.spaces: # Queue isn't full
        #     embed = discord.Embed(title=f'Cannot start player draft until the queue is full! _({len(self.queue)}/{self.spaces})_', color=self.color)
        # else:
        self.players_left = copy.copy(self.queue) # Copy so we don't modify the queue
        players_leftStr = ''.join(f'{i}. {p}\n' for i, p in enumerate(self.players_left, 1))
        embed = discord.Embed(title='Player draft has begun!', description=self.pdraft_str, color=self.color)

        await message.channel.send(embed=embed)

    async def pick_command(self, message):
        player_num = message.content.split(' ', 1)[1] # Remove command from input
        
        if self.players_left == None: # Will only ever be None when there's no active player draft
            embed = discord.Embed(title='Player draft has not started!', color=self.color)
        elif message.author not in self.queue: # Don't let people not in queue make draft picks
            embed = discord.Embed(title='You cannot pick a player unless you are in the queue!', color=self.color)
        elif not player_num.isdigit() or not (int(player_num) > 0 and int(player_num) <= len(self.players_left)):
            embed = discord.Embed(title=f'{player_num} is not a player!', description=self.pdraft_str, color=self.color)
        elif message.author in (p for t in self.teams.values() for p in t): # Check if they are in a team
            for team in self.teams.keys(): # Iterate through teams
                if message.author in self.teams[team]: # If picker in this team
                    self.teams[team].append(self.players_left.pop(int(player_num) - 1)) # Add player pick to picker's team
                    embed = discord.Embed(title=f'**{team}** has picked **{self.teams[team][-1].display_name}**', description=self.pdraft_str, color=self.color)
                    break
        elif len(self.teams) >= 2: # Check if there are already 2 teams
            embed = discord.Embed(title='There are already two teams!', description=self.pdraft_str, color=self.color)
        else: # Create new team with picker and pickee
            team_name = 'Team ' + str(message.author.display_name)
            self.teams.update({team_name: [message.author, self.players_left.pop(int(player_num) - 1)]})
            self.players_left.remove(message.author) # Need to remove picker since we can't pop sender without knowing their index
            embed = discord.Embed(title=f'**{team_name}** has picked **{self.teams[team_name][-1].display_name}**', description=self.pdraft_str, color=self.color)

        if self.players_left != None and len(self.players_left) == 1:
            for team in self.teams.keys(): # Iterate through teams
                if message.author not in self.teams[team]:
                    self.teams[team].append(self.players_left.pop(0)) # Add last player to other team
                    embed = discord.Embed(title='Teams are set!', description=self.pdraft_str, color=self.color)
                    self.players_left = None # Set to None when there is no ongoing player draft
                    break

        await message.channel.send(embed=embed)

    async def about_command(self, message):
        await message.channel.send(embed=self.about_embed)

    async def notFound_command(self, message):
        embed = discord.Embed(title=f'`{message.content}` isn\'t a recognized command', description='Type `q!help` for a list of commands', color=self.color)
        await message.channel.send(embed=embed)

    def command_handler(self, message):
        tokens = message.content.split()
        command = tokens[0]

        return self.command_vector.get(command, self.notFound_command)(message)

class QueueBot:
    def __init__(self, token):
        self.client = discord.Client()
        self.token = token # Discord API bot token
        self.queue_guild_dict = {} # Map guild name string to corresponding QueueGuild object

        @self.client.event
        async def on_ready(): # NOTE: Not sure if async is necessary here
            print(self.startupBanner)

            # Check and populate connected guilds on startup
            for guild in self.client.guilds:
                self.queue_guild_dict.update({ guild: QueueGuild(guild) }) # NOTE: This could not update new guilds adding the bot if only run on ready

        @self.client.event
        async def on_message(message): # NOTE: Not sure if async is necessary here (given that called function is async)
            if message.content.lstrip().startswith('q!'):
                await self.queue_guild_dict[message.guild].command_handler(message)

        self.client.run(self.token)

    @property
    def startupBanner(self):
        user_name = self.client.user.name
        user_id = self.client.user.id
        line = '=' * max(len(user_name), len(str(user_id)))
        return f'{line}\nLogged in as...\n{user_name}\n{user_id}\n{line}'
