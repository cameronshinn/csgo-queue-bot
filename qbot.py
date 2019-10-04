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
        self.guild = guild
        self.queue = []
        self.alertees = set()
        self.commandVector = { 'q!help':     self.help_command,
                               'q!join':     self.join_command,
                               'q!leave':    self.leave_command,
                               'q!view':     self.view_command,
                               'q!empty':    self.empty_command,
                               'q!popflash': self.popflash_command,
                               'q!draft':    self.draft_command,
                               'q!ban':      self.ban_command,
                               'q!about':    self.about_command }
        self.thumbnailUrl = THUMBNAIL
        self.color = LOGO_COLOR
        self.mapPool = MAP_POOL
        self.mapsLeft = None

    @property
    def helpEmbed(self):
        embed = discord.Embed(title='__Queue Commands__', color=self.color)
        embed.add_field(name='`q!help`', value='Display help message page', inline=False)
        embed.add_field(name='`q!join`', value='Join the queue', inline=False)
        embed.add_field(name='`q!leave`', value='Leave the queue', inline=False)
        embed.add_field(name='`q!view`', value='Display who is currently in the queue', inline=False)
        embed.add_field(name='`q!empty`', value='Empty the queue', inline=False)
        embed.add_field(name='`q!popflash`', value='Link this server\'s designated Popflash lobby', inline=False)
        embed.add_field(name='`q!draft`', value='Start (or restart) a map draft', inline=False)
        embed.add_field(name='`q!ban <map/number>`', value='Ban the specified map from the map draft', inline=False)
        embed.add_field(name='`q!about`', value='Display information about the 10-ManQ bot', inline=False)
        return embed

    @property
    def queueEmbed(self):
        if self.queue: # If there are members in the queue
            enumQueue = enumerate(self.queue, start=1)
            queueStr = ''.join(f'{enumUser[0]}. {enumUser[1].display_name}\n' for enumUser in enumQueue)
        else:
            queueStr = '_The queue is empty..._'

        embed = discord.Embed(title='__Players in queue for 10-mans__', description=queueStr, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    @property
    def popflashEmbed(self): # Set as a property since the server name can change over time
        guildUrl = POPFLASH_URL + ''.join(char.lower() for char in str(self.guild) if char.isalpha() or char.isdigit())
        return discord.Embed(title="Popflash lobby is up!", description=guildUrl, color=self.color)

    @property
    def aboutEmbed(self):
        embed = discord.Embed(title='__10-ManQ Queue Bot__', description='The definitive bot for setting up 10-man lobbies', color=self.color)
        embed.set_thumbnail(url=self.thumbnailUrl)
        embed.add_field(name='This bot was made to give CS:GO players a convenient way to find Discord server members who want to play in-house pickup games', value='github.com/cameronshinn/csgo-queue-bot', inline=False)
        return embed

    async def join_command(self, message):
        if message.author in self.queue:
            embed = discord.Embed(title=f'**{message.author.display_name}** is already in the queue', color=self.color)
        if len(self.queue) >= 10:
            embed = discord.Embed(title=f'Unable to add **{message.author.display_name}**\nQueue is full _({len(self.queue)}/10)_', color=self.color)
        else:
            self.queue.append(message.author)
            embed = discord.Embed(title=f'**{message.author.display_name}** has been added to the queue _({len(self.queue)}/10)_', color=self.color)

        await message.channel.send(embed=embed)

        if len(self.queue) == 10:
            userMentions = ''    
                
            for user in self.queue:
                userMentions += user.mention + ' '
            
            self.queue.clear()
            await message.channel.send(userMentions, embed=self.popflashEmbed)

    async def leave_command(self, message):
        if message.author in self.queue:
            self.queue.remove(message.author)
            embed = discord.Embed(title=f'**{message.author.display_name}** has been removed from the queue _({len(self.queue)}/10)_', color=self.color)
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
        embed = discord.Embed(title=f'The queue has been emptied _({len(self.queue)}/10)_', color=self.color)
        await message.channel.send(embed=embed)

    async def help_command(self, message):
        await message.channel.send(embed=self.helpEmbed)

    async def popflash_command(self, message):
        await message.channel.send(embed=self.popflashEmbed)

    async def draft_command(self, message):
        self.mapsLeft = copy.copy(self.mapPool) # Need to copy to preseve the original map pool
        mapsLeftStr = ''.join(f'{i}. {m}\n' for i, m in enumerate(self.mapsLeft, 1)) # TODO: Add support for command
        embed = discord.Embed(title=f'Draft has begun!', description=mapsLeftStr, color=self.color)
        await message.channel.send(embed=embed)

    async def ban_command(self, message):
        csMap = message.content.split(' ', 1)[1]

        if csMap.isdigit() and int(csMap) > 0 and int(csMap) <= len(self.mapPool):
            i = int(csMap)
            csMap = self.mapPool[i - 1]

        if self.mapsLeft == None:
            embed = discord.Embed(title='Map draft has not started!', color=self.color)
        elif csMap in self.mapsLeft:
            self.mapsLeft.remove(csMap)
            mapsLeftStr = ''.join([f'{i}. {m}\n' if m in self.mapsLeft else f'{i}. ~~{m}~~\n' for i, m in enumerate(self.mapPool, 1)])
            embed = discord.Embed(title=f'{csMap} has been banned', description=mapsLeftStr, color=self.color)
        elif csMap in self.mapPool:
            mapsLeftStr = ''.join([f'{i}. {m}\n' if m in self.mapsLeft else f'{i}. ~~{m}~~\n' for i, m in enumerate(self.mapPool, 1)])
            embed = discord.Embed(title=f'{csMap} has already been banned', description=mapsLeftStr, color=self.color)
        else:
            embed = discord.Embed(title=f'{csMap} is not a map', color=self.color)
            
        if len(self.mapsLeft) == 1:
            embed = discord.Embed(title=f'We\'re going to {self.mapsLeft[0]}!', color=self.color)
            self.mapsLeft = None

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
        self.token = token # Discord api bot token
        self.queueGuildDict = {} # Map guild name string to corresponding QueueGuild object

        @self.client.event
        async def on_ready(): # Not sure if async is necessary here
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
