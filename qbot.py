# qbot.py
# cameronshinn

import asyncio
import copy
import datetime
import discord
import time

LOGO_COLOR = 0xF4B903
THUMBNAIL = 'https://i.imgur.com/5v6mLwb.png'
POPFLASH_URL = 'https://popflash.site/scrim/'
MAP_POOL = ['Cache', 'Cobblestone', 'Dust II', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Train', 'Vertigo']
GITHUB = 'github.com/cameronshinn/csgo-queue-bot'

class QueueGuild:
    def __init__(self, guild):
        self.spaces = 10
        self.guild = guild # Guild that class instance belongs to
        self.queue = [] # Where users in queue are held
        self.mapPool = MAP_POOL
        self.mapsLeft = None # Set to None when there is no ongoing map draft
        self.teams = {} # Where teams are stored when drafting (team name : list of members)
        self.playersLeft = None # Set to None when there is no ongoing player draft
        self.commandVector = { 'q!help':     self.help_command, # Map command strings to handler functions for easy lookup
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
        self.thumbnailUrl = THUMBNAIL
        self.color = LOGO_COLOR

    @property
    def helpEmbed(self):
        embed = discord.Embed(title='__Queue Commands__', color=self.color)
        embed.add_field(name='`q!help`', value='Display help message page', inline=False)
        embed.add_field(name='`q!join`', value='Join the queue', inline=False)
        embed.add_field(name='`q!leave`', value='Leave the queue', inline=False)
        embed.add_field(name='`q!view`', value='Display who is currently in the queue', inline=False)
        embed.add_field(name='`q!empty`', value='Empty the queue', inline=False)
        embed.add_field(name='`q!popflash`', value='Link this server\'s designated Popflash lobby', inline=False)
        embed.add_field(name='`q!mdraft`', value='Start (or restart) a map draft', inline=False)
        embed.add_field(name='`q!ban <map/number>`', value='Ban the specified map from the map draft', inline=False)
        embed.add_field(name='`q!pdraft`', value='Start (or restart) a player draft', inline=False)
        embed.add_field(name='`q!pick <number>`', value='Pick a player for your team', inline=False)
        embed.add_field(name='`q!about`', value='Display information about the 10-ManQ bot', inline=False)
        return embed

    @property
    def queueEmbed(self):
        if self.queue: # If there are users in the queue
            enumQueue = enumerate(self.queue, start=1)
            queueStr = ''.join(f'{enumUser[0]}. {enumUser[1].display_name}\n' for enumUser in enumQueue)
        else: # No users in queue
            queueStr = '_The queue is empty..._'

        embed = discord.Embed(title='__Players in queue for 10-mans__', description=queueStr, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    @property
    def popflashEmbed(self): # Set with property decorator since the server name can change over time
        guildUrl = POPFLASH_URL + ''.join(char.lower() for char in str(self.guild) if char.isalpha() or char.isdigit())
        return discord.Embed(title="Popflash lobby is up!", description=guildUrl, color=self.color)

    @property
    def pdraftStr(self):
        if self.playersLeft == None:
            return None

        tempStr = ''

        if not self.playersLeft == []:
            tempStr += '__Players Left__\n' + ''.join(f'{i}. {p.display_name}\n' for i, p in enumerate(self.playersLeft, 1))

        if len(self.teams) != 0:
            for team in self.teams.keys():
                tempStr += f'\n__{team}__\n' + ''.join(p.display_name + '\n' for p in self.teams[team])

        return tempStr
    
    @property
    def aboutEmbed(self):
        embed = discord.Embed(title='__10-ManQ Queue Bot__', description='The definitive bot for setting up 10-man lobbies', color=self.color)
        embed.set_thumbnail(url=self.thumbnailUrl)
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
            userMentions = ''    
                
            for user in self.queue:
                userMentions += user.mention + ' '
            
            self.queue.clear()
            await message.channel.send(userMentions, embed=self.popflashEmbed)

    async def leave_command(self, message):
        if message.author in self.queue:
            self.queue.remove(message.author)
            embed = discord.Embed(title=f'**{message.author.display_name}** has been removed from the queue _({len(self.queue)}/{self.spaces})_', color=self.color)
        else:
            embed = discord.Embed(title=f'**{message.author.display_name}** was never in the queue', color=self.color)

        await message.channel.send(embed=embed)

    async def view_command(self, message):
        await message.channel.send(embed=self.queueEmbed)

    async def start_command(self, message):
        userMentions = ''    
            
        for user in self.queue:
            userMentions += str(user.id) + ' '
        
        self.queue.clear()

        await message.channel.send(userMentions, embed=self.popflashEmbed)

    async def empty_command(self, message):
        self.queue.clear()
        embed = discord.Embed(title=f'The queue has been emptied _({len(self.queue)}/{self.spaces})_', color=self.color)
        await message.channel.send(embed=embed)

    async def help_command(self, message):
        await message.channel.send(embed=self.helpEmbed)

    async def popflash_command(self, message):
        await message.channel.send(embed=self.popflashEmbed)

    async def mdraft_command(self, message):
        self.mapsLeft = copy.copy(self.mapPool) # Need to copy to preseve the original map pool
        mapsLeftStr = ''.join(f'{i}. {m}\n' for i, m in enumerate(self.mapsLeft, 1))
        embed = discord.Embed(title=f'Map draft has begun!', description=mapsLeftStr, color=self.color)
        await message.channel.send(embed=embed)

    async def ban_command(self, message):
        csMap = message.content.split(' ', 1)[1] # Remove command from input

        # Check if map number specified and convert to map name if so
        if csMap.isdigit() and int(csMap) > 0 and int(csMap) <= len(self.mapPool): # Check if digit and in range
            i = int(csMap)
            csMap = self.mapPool[i - 1] # Convert to map name

        if self.mapsLeft == None: # Will only ever be None when there's no active map draft
            embed = discord.Embed(title='Map draft has not started!', color=self.color)
        elif csMap.lower in self.mapsLeft: # Remove map from remaining
            self.mapsLeft.remove(csMap)
            mapsLeftStr = ''.join([f'{i}. {m}\n' if m in self.mapsLeft else f'{i}. ~~{m}~~\n' for i, m in enumerate(self.mapPool, 1)])
            embed = discord.Embed(title=f'{csMap} has been banned', description=mapsLeftStr, color=self.color)
        elif csMap in self.mapPool: # Otherwise map must already be banned
            mapsLeftStr = ''.join([f'{i}. {m}\n' if m in self.mapsLeft else f'{i}. ~~{m}~~\n' for i, m in enumerate(self.mapPool, 1)])
            embed = discord.Embed(title=f'{csMap} has already been banned', description=mapsLeftStr, color=self.color)
        else: # Otherwise input is not map
            embed = discord.Embed(title=f'{csMap} is not a map', color=self.color)
            
        if len(self.mapsLeft) == 1: # End draft when no choices left
            embed = discord.Embed(title=f'We\'re going to {self.mapsLeft[0]}!', color=self.color)
            self.mapsLeft = None # Set to None when there is no ongoing map draft

        await message.channel.send(embed=embed)

    async def pdraft_command(self, message):
        if not len(self.queue) == self.spaces: # Queue isn't full
            embed = discord.Embed(title=f'Cannot start player draft until the queue is full! _({len(self.queue)}/{self.spaces})_', color=self.color)
        else:
            self.playersLeft = copy.copy(self.queue) # Copy so we don't modify the queue
            playersLeftStr = ''.join(f'{i}. {p}\n' for i, p in enumerate(self.playersLeft, 1))
            embed = discord.Embed(title='Player draft has begun!', description=self.pdraftStr, color=self.color)

        await message.channel.send(embed=embed)

    async def pick_command(self, message):
        playerNum = message.content.split(' ', 1)[1] # Remove command from input
        
        if self.playersLeft == None: # Will only ever be None when there's no active player draft
            embed = discord.Embed(title='Player draft has not started!', color=self.color)
        elif message.author not in self.queue: # Don't let people not in queue make draft picks
            embed = discord.Embed(title='You cannot pick a player unless you are in the queue!', color=self.color)
        elif not playerNum.isdigit() or not (int(playerNum) > 0 and int(playerNum) <= len(self.playersLeft)):
            embed = discord.Embed(title=f'{playerNum} is not a player!', description=self.pdraftStr, color=self.color)
        elif message.author in (p for p in self.teams[t] for t in self.teams.keys()): # Check if they are in a team
            for team in self.teams.keys(): # Iterate through teams
                if message.author in self.teams[team]: # If picker in this team
                    self.teams[team].append(self.playersLeft.pop(int(playerNum) - 1)) # Add player pick to picker's team
                    embed = discord.Embed(title=f'**{team}** has picked **{self.teams[team][-1].display_name}**', description=self.pdraftStr, color=self.color)
                    break
        elif len(self.teams) >= 2: # Check if there are already 2 teams
            embed = discord.Embed(title='There are already two teams!', description=self.pdraftStr, color=self.color)
        else: # Create new team with picker and pickee
            teamName = 'Team ' + str(message.author.display_name)
            self.teams.update({teamName: [message.author, self.playersLeft.pop(int(playerNum) - 1)]})
            embed = discord.Embed(title=f'**{teamName}** has picked **{self.teams[teamName][-1].display_name}**', description=self.pdraftStr, color=self.color)

        if self.playersLeft != None and len(self.playersLeft) == 1:
            for team in self.teams.keys(): # Iterate through teams
                if message.author not in self.teams[team]:
                    self.teams[team].append(self.playersLeft.pop(0)) # Add last player to other team
                    embed = discord.Embed(title='Teams are set!', description=self.pdraftStr, color=self.color)
                    self.playersLeft = None # Set to None when there is no ongoing player draft
                    break

        await message.channel.send(embed=embed)

    async def about_command(self, message):
        await message.channel.send(embed=self.aboutEmbed)

    async def notFound_command(self, message):
        embed = discord.Embed(title=f'`{message.content}` isn\'t a recognized command', description='Type `q!help` for a list of commands', color=self.color)
        await message.channel.send(embed=embed)

    def commandHandler(self, message):
        tokens = message.content.split()
        command = tokens[0]

        return self.commandVector.get(command, self.notFound_command)(message)

class QueueBot:
    def __init__(self, token):
        self.client = discord.Client()
        self.token = token # Discord API bot token
        self.queueGuildDict = {} # Map guild name string to corresponding QueueGuild object

        @self.client.event
        async def on_ready(): # NOTE: Not sure if async is necessary here
            print(self.startupBanner)

            # Check and populate connected guilds on startup
            for guild in self.client.guilds:
                self.queueGuildDict.update({ guild: QueueGuild(guild) }) # NOTE: This could not update new guilds adding the bot if only run on ready

        @self.client.event
        async def on_message(message): # NOTE: Not sure if async is necessary here (given that called function is async)
            if message.content.lstrip().startswith('q!'):
                await self.queueGuildDict[message.guild].commandHandler(message)

        self.client.run(self.token)

    @property
    def startupBanner(self):
        userName = self.client.user.name
        userID = self.client.user.id
        line = '=' * max(len(userName), len(str(userID)))
        return f'{line}\nLogged in as...\n{userName}\n{userID}\n{line}'
