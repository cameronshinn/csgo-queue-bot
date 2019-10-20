#!/usr/bin/env python3
# qbot.py
# cameronshinn

# Import libraries
import asyncio
import datetime
import dbl
import copy
import datetime
import discord
import time
from discord.ext import commands, tasks

# Import other files
import maps

LOGO_COLOR = 0xF4B903
THUMBNAIL = 'https://i.imgur.com/5v6mLwb.png'
POPFLASH_URL = 'https://popflash.site/scrim/'
GITHUB = 'github.com/cameronshinn/csgo-queue-bot'

class MapDraftPanel:
    def __init__(self, map_pool, color):
        self.map_pool = map_pool
        self.maps_left = copy.copy(self.map_pool)
        self.color = color
        self.msg = None
        self.embed_title = f'Map draft has begun!'
        self.embed = discord.Embed(title=self.embed_title, description=self.maps_left_str, color=self.color)
        self.embed.set_footer(text='React to a map icon below to ban the corresponding map')
        
    @property
    def maps_left_str(self):
        return ''.join(f'{m.emoji_icon}  {m.name}\n' if m in self.maps_left else f':heavy_multiplication_x:  ~~{m.name}~~\n' for m in self.map_pool)

    async def send_panel(self, channel):
        panel = await channel.send(embed=self.embed)
        await panel.edit(embed=self.embed) # Edit it so the placement doesn't shift when picking first map

        for m in self.maps_left:
            await panel.add_reaction(m.emoji_icon)

        self.msg = panel

    async def ban_map(self, reaction, user):
        if self.msg == None or self.msg.id != reaction.message.id:
            return self.msg

        for m in self.maps_left:
            if str(reaction.emoji) ==  m.emoji_icon:
                async for u in reaction.users():
                    await reaction.remove(u)

                self.maps_left.remove(m)

                if len(self.maps_left) == 1:
                    map_result = self.maps_left[0]
                    await self.msg.clear_reactions()
                    self.embed_title = f'We\'re going to {map_result.name}! {map_result.emoji_icon}'
                    self.embed = discord.Embed(title=self.embed_title, color=self.color)
                    self.embed.set_image(url=map_result.image_url)
                    self.embed.set_footer(text=f'Be sure to select {map_result.name} in the PopFlash lobby')
                    await self.msg.edit(embed=self.embed)
                    self.maps_left = copy.copy(self.map_pool)
                    self.msg = None
                    return self.msg
                else:
                    self.embed_title = f'**{user.name}** has banned **{m.name}**'
                    self.embed = discord.Embed(title=self.embed_title, description=self.maps_left_str, color=self.color)
                    self.embed.set_thumbnail(url=m.image_url)
                    self.embed.set_footer(text='React to a map icon below to ban the corresponding map')
                    await self.msg.edit(embed=self.embed)
                    return self.msg

class QueueGuild:
    def __init__(self, guild):
        self.spaces = 10
        self.guild = guild # Guild that class instance belongs to
        self.queue = [] # Where users in queue are held
        self.map_pool = maps.map_pool
        self.draft_panels = {'mdraft': None}
        self.teams = {} # Where teams are stored when drafting (team name : list of members)
        self.players_left = None # Set to None when there is no ongoing player draft
        self.command_vector = { 'q!help':     self.help_command, # Map command strings to handler functions for easy lookup
                                'q!join':     self.join_command,
                                'q!leave':    self.leave_command,
                                'q!view':     self.view_command,
                                'q!empty':    self.empty_command,
                                'q!popflash': self.popflash_command,
                                'q!mdraft':   self.mdraft_command,
                                'q!pdraft':   self.pdraft_command,
                                'q!pick':     self.pick_command,
                                'q!about':    self.about_command }
        self.react_vector = {}
        self.thumbnail_url = THUMBNAIL
        self.color = LOGO_COLOR

    @staticmethod
    def warning_message(str_in):
        return f':warning:  {str_in}  :warning:'

    @property
    def help_embed(self):
        embed = discord.Embed(title='__Queue Commands__', color=self.color)
        embed.add_field(name='**q!help**', value='_Display help message page_', inline=False)
        embed.add_field(name='**q!join**', value='_Join the queue_', inline=False)
        embed.add_field(name='**q!leave**', value='_Leave the queue_', inline=False)
        embed.add_field(name='**q!view**', value='_Display who is currently in the queue_', inline=False)
        embed.add_field(name='**q!empty**', value='_Empty the queue_', inline=False)
        embed.add_field(name='**q!popflash**', value='_Link this server\'s designated PopFlash lobby_', inline=False)
        embed.add_field(name='**q!pdraft**', value='_Start (or restart) a player draft_', inline=False)
        embed.add_field(name='**q!pick <number>**', value='_Pick a player for your team_', inline=False)
        embed.add_field(name='**q!mdraft**', value='_Start (or restart) a map draft_', inline=False)
        embed.add_field(name='**q!about**', value='_Display information about the 10-ManQ bot_', inline=False)
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
        guild_url = POPFLASH_URL + ''.join(char for char in str(self.guild) if char.isalpha() or char.isdigit())
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
        embed = discord.Embed(title='__10-ManQ Queue Bot__', description='_The definitive bot for setting up 10-man lobbies_\n\nThis bot gives players a convenient way to find Discord server members who want to play in-house pickup games of CS:GO\n\n[Join our support server here](https://discordapp.com/invite/tskeyDA)\n\n[Source code can be found here on GitHub](https://github.com/cameronshinn/csgo-queue-bot)', color=self.color)
        embed.set_thumbnail(url=self.thumbnail_url)
        return embed

    async def join_command(self, message):
        if message.author in self.queue: # User already in queue
            embed = discord.Embed(title=self.warning_message(f'**{message.author.display_name}** is already in the queue'), color=self.color)
        elif len(self.queue) >= self.spaces: # Queue full
            embed = discord.Embed(title=self.warning_message(f'Unable to add **{message.author.display_name}**\nQueue is full _({len(self.queue)}/{self.spaces})_'), color=self.color)
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
            embed = discord.Embed(title=self.warning_message(f'**{message.author.display_name}** was never in the queue'), color=self.color)

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

    async def pdraft_command(self, message):
        if not len(self.queue) == self.spaces: # Queue isn't full
            embed = discord.Embed(title=self.warning_message(f'Cannot start player draft until the queue is full! _({len(self.queue)}/{self.spaces})_'), color=self.color)
        else:
            self.players_left = copy.copy(self.queue) # Copy so we don't modify the queue
            players_leftStr = ''.join(f'{i}. {p}\n' for i, p in enumerate(self.players_left, 1))
            embed = discord.Embed(title='Player draft has begun!', description=self.pdraft_str, color=self.color)

        await message.channel.send(embed=embed)

    async def pick_command(self, message):
        player_num = message.content.split(' ', 1)[1] # Remove command from input
        
        if self.players_left == None: # Will only ever be None when there's no active player draft
            embed = discord.Embed(title=self.warning_message('Player draft has not started!'), color=self.color)
        elif message.author not in self.queue: # Don't let people not in queue make draft picks
            embed = discord.Embed(title=self.warning_message('You cannot pick a player unless you are in the queue!'), color=self.color)
        elif not player_num.isdigit() or not (int(player_num) > 0 and int(player_num) <= len(self.players_left)):
            embed = discord.Embed(title=self.warning_message(f'{player_num} is not a player!'), description=self.pdraft_str, color=self.color)
        elif message.author in (p for t in self.teams.values() for p in t): # Check if they are in a team
            for team in self.teams.keys(): # Iterate through teams
                if message.author in self.teams[team]: # If picker in this team
                    self.teams[team].append(self.players_left.pop(int(player_num) - 1)) # Add player pick to picker's team
                    embed = discord.Embed(title=f'**{team}** has picked **{self.teams[team][-1].display_name}**', description=self.pdraft_str, color=self.color)
                    break
        elif len(self.teams) >= 2: # Check if there are already 2 teams
            embed = discord.Embed(title=self.warning_message('There are already two teams!'), description=self.pdraft_str, color=self.color)
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

    async def mdraft_command(self, message):
        self.draft_panels['mdraft'] = MapDraftPanel(self.map_pool, self.color)
        await self.draft_panels['mdraft'].send_panel(message.channel)

    async def about_command(self, message):
        await message.channel.send(embed=self.about_embed)

    async def not_found_command(self, message):
        embed = discord.Embed(title=self.warning_message(f'`{message.content}` isn\'t a recognized command'), description='Type `q!help` for a list of commands', color=self.color)
        await message.channel.send(embed=embed)

    def command_handler(self, message):
        tokens = message.content.split()
        command = tokens[0]

        return self.command_vector.get(command, self.not_found_command)(message)

    def react_handler(self, reaction, user):
        if self.draft_panels['mdraft'] != None:
            retval = self.draft_panels['mdraft'].ban_map(reaction, user)
            
            if retval is None:
                self.draft_panels['mdraft'] = None

            return retval

class QueueBot(commands.Cog):
    def __init__(self, client, discord_token, dbl_token=None):
        self.client = client
        self.discord_token = discord_token # Discord API bot token
        
        if dbl_token:
            self.dbl_token = dbl_token # top.gg DBL token
            self.dblpy = dbl.DBLClient(self.client, self.dbl_token)

        self.queue_guild_dict = {} # Map guild name string to corresponding QueueGuild object

        @self.client.event
        async def on_ready():
            print(self.startupBanner)

            # Check and populate connected guilds on startup
            print(f'\nBot is online in {len(self.client.guilds)} servers:')
            
            for guild in self.client.guilds:
                print(f'    {guild}')
                self.queue_guild_dict.update({ guild: QueueGuild(guild) })

            print('')

        @self.client.event
        async def on_guild_join(guild):
            print(f'{self.timestamp()}\n    Bot has been added to guild: {guild}\n')
            self.queue_guild_dict.update({ guild: QueueGuild(guild) })
            
        @self.client.event
        async def on_guild_remove(guild):
            print(f'{self.timestamp()}\n    Bot has been removed from guild: {guild}\n')
            self.queue_guild_dict.pop(guild, None)
                
        @self.client.event
        async def on_message(message): # NOTE: Not sure if async is necessary here (given that called function is async)
            if message.author == self.client.user:
                return

            if message.content.lstrip().startswith('q!'):
                print(f'{self.timestamp()}\n    Command: "{message.content}"\n    Sender:  {message.author}\n    Guild:   {message.guild}\n')
                await self.queue_guild_dict[message.guild].command_handler(message)

        @self.client.event
        async def on_reaction_add(reaction, user):
            if user == self.client.user:
                return

            try:
                await self.queue_guild_dict[reaction.message.guild].react_handler(reaction, user)
            except TypeError: # Temp solution to stop flooding the command prompt with exceptions
                pass

        # Start bot
        if dbl_token:
            self.update_stats.start()
        
        self.client.run(self.discord_token)

    @tasks.loop(minutes=60)
    async def update_stats(self):
        """Post server count to top.gg"""
        print('Attempting to post server count to top.gg...')
        
        try:
            await self.dblpy.post_guild_count()
            print(f'Posted server count ({self.dblpy.guild_count()})\n')
        except Exception as e:
            raise Exception(f'Failed to post server count {type(e).__name__}\n\n')

    @update_stats.before_loop
    async def wait_for_bot(self):
        """Wait until the bot is ready before starting the update stats loop"""
        await self.client.wait_until_ready()
        await asyncio.sleep(5) # Give the bot time to run on_ready()

    @staticmethod
    def timestamp():
        return datetime.datetime.now().strftime("%x - [%X]")

    @property
    def startupBanner(self):
        user_name = self.client.user.name
        user_id = self.client.user.id
        line = '=' * max(len(user_name), len(str(user_id)))
        return f'{line}\nLogged in as...\n{user_name}\n{user_id}\n{line}'
