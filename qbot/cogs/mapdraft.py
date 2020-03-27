# mapdraft.py

import discord
from discord.ext import commands


class Map:
    """ A group of attributes representing a map. """

    def __init__(self, name, dev_name, emoji, image_url):
        """ Set attributes. """
        self.name = name
        self.dev_name = dev_name
        self.emoji = emoji
        self.image_url = image_url


BASE_URL = 'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/'

de_cache = Map('Cache', 'de_cache', '<:de_cache:632416021910650919>',
               f'{BASE_URL}cache.jpg')
de_cbble = Map('Cobblestone', 'de_cbble', '<:de_cbble:632416085899214848>',
               f'{BASE_URL}cobblestone.jpg')
de_dust2 = Map('Dust II', 'de_dust2', '<:de_dust2:632416148658323476>',
               f'{BASE_URL}dust-ii.jpg')
de_inferno = Map('Inferno', 'de_inferno', '<:de_inferno:632416390112084008>',
                 f'{BASE_URL}inferno.jpg')
de_mirage = Map('Mirage', 'de_mirage', '<:de_mirage:632416441551028225>',
                f'{BASE_URL}mirage.jpg')
de_nuke = Map('Nuke', 'de_nuke', '<:de_nuke:632416475029962763>',
              f'{BASE_URL}nuke.jpg')
de_overpass = Map('Overpass', 'de_overpass', '<:de_overpass:632416513562902529>',
                  f'{BASE_URL}overpass.jpg')
de_train = Map('Train', 'de_train', '<:de_train:632416540687335444>',
               f'{BASE_URL}train.jpg')
de_vertigo = Map('Vertigo', 'de_vertigo', '<:de_vertigo:632416584870395904>',
                 f'{BASE_URL}vertigo.jpg')

ALL_MAPS = [
    de_cache,
    de_cbble,
    de_dust2,
    de_inferno,
    de_mirage,
    de_nuke,
    de_overpass,
    de_train,
    de_vertigo
]

DEFAULT_MAP_POOL = [
    de_dust2,
    de_inferno,
    de_mirage,
    de_nuke,
    de_overpass,
    de_train,
    de_vertigo
]


class MDraftData:
    """ Holds guild-specific map draft data. """

    def __init__(self, map_pool=DEFAULT_MAP_POOL, maps_left=None, message=None):
        self.map_pool = map_pool
        self.maps_left = maps_left
        self.message = message


class MapDraftCog(commands.Cog):
    """ Handles the map drafter. """

    footer = 'React to any of the map icons below to ban the corresponding map'

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.color = color
        self.guild_mdraft_data = {}  # Map guild -> guild map draft data

    @commands.Cog.listener()
    async def on_ready(self):
        """" Initialize mdraft data for each guild the bot is in. """
        for guild in self.bot.guilds:
            if guild not in self.guild_mdraft_data:  # Don't add if guild already loaded
                self.guild_mdraft_data[guild] = MDraftData()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty mdraft data object for guilds that are added. """
        self.guild_mdraft_data[guild] = MDraftData()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove mdraft data when a guild is removed. """
        self.guild_mdraft_data.pop(guild)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    def maps_left_str(self, guild):
        """ Get the maps left string representation for a given giuld. """
        x_emoji = ':heavy_multiplication_x:'
        mdraft_data = self.guild_mdraft_data[guild]
        maps_left = mdraft_data.map_pool if mdraft_data.maps_left is None else mdraft_data.maps_left
        out_str = ''

        for m in mdraft_data.map_pool:
            out_str += f'{m.emoji}  {m.name}\n' if m in maps_left else f'{x_emoji}  ~~{m.name}~~\n'

        return out_str

    @commands.command(brief='Start (or restart) a map draft')
    async def mdraft(self, ctx):
        """ Start a map draft by sending a map draft embed panel. """
        mdraft_data = self.guild_mdraft_data[ctx.guild]
        mdraft_data.maps_left = mdraft_data.map_pool.copy()  # Set or reset map pool
        embed = discord.Embed(title='Map draft has begun!', description=self.maps_left_str(ctx.guild), color=self.color)
        embed.set_footer(text=MapDraftCog.footer)
        msg = await ctx.send(embed=embed)
        await msg.edit(embed=embed)

        for m in mdraft_data.map_pool:
            await msg.add_reaction(m.emoji)

        mdraft_data.message = msg

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """ Remove a map from the draft when a user reacts with the corresponding icon. """
        if user == self.bot.user:
            return

        guild = user.guild
        mdraft_data = self.guild_mdraft_data[guild]

        if mdraft_data.message is None or reaction.message.id != mdraft_data.message.id:
            return

        for m in mdraft_data.maps_left.copy():  # Iterate over copy to modify original w/o consequences
            if str(reaction.emoji) == m.emoji:
                async for u in reaction.users():
                    await reaction.remove(u)

                mdraft_data.maps_left.remove(m)

                if len(mdraft_data.maps_left) == 1:
                    map_result = mdraft_data.maps_left[0]
                    await mdraft_data.message.clear_reactions()
                    embed_title = f'We\'re going to {map_result.name}! {map_result.emoji}'
                    embed = discord.Embed(title=embed_title, color=self.color)
                    embed.set_image(url=map_result.image_url)
                    embed.set_footer(text=f'Be sure to select {map_result.name} in the PopFlash lobby')
                    await mdraft_data.message.edit(embed=embed)
                    mdraft_data.maps_left = None
                    mdraft_data.message = None
                else:
                    embed_title = f'**{user.name}** has banned **{m.name}**'
                    embed = discord.Embed(title=embed_title, description=self.maps_left_str(guild), color=self.color)
                    embed.set_thumbnail(url=m.image_url)
                    embed.set_footer(text=MapDraftCog.footer)
                    await mdraft_data.message.edit(embed=embed)

                break

    @commands.command(usage='setmp {+|-}<map name> ...',
                      brief='Add or remove maps from the mdraft map pool (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def setmp(self, ctx, *args):
        """"""
        mdraft_data = self.guild_mdraft_data[ctx.guild]

        if len(args) == 0:
            embed = discord.Embed(title='Current map pool', color=self.color)
        else:
            original_mp = mdraft_data.map_pool.copy()  # Save map pool copy incase outcome state is invalid
            description = ''
            any_wrong_arg = False  # Indicates if the command was used correctly

            for arg in args:
                map_name = arg[1:]  # Remove +/- prefix
                map_obj = next((m for m in ALL_MAPS if m.dev_name == map_name), None)

                if map_obj is None:
                    description += f'\u2022 Could not interpret `{arg}`\n'
                    any_wrong_arg = True
                    continue

                if arg.startswith('+'):  # Add map
                    mdraft_data.map_pool = [m for m in ALL_MAPS if m in mdraft_data.map_pool or m.dev_name == map_name]
                    description += f'\u2022 Added `{map_name}`\n'
                elif arg.startswith('-'):  # Remove map
                    mdraft_data.map_pool = [m for m in mdraft_data.map_pool if m.dev_name != map_name]
                    description += f'\u2022 Removed `{map_name}`\n'

            if len(mdraft_data.map_pool) < 3:
                mdraft_data.map_pool = original_mp
                description = 'Pool cannot have fewer than 3 maps!'

            embed = discord.Embed(title='Modified map pool', description=description, color=self.color)

            if any_wrong_arg:  # Add example usage footer if command was used incorrectly
                embed.set_footer(text=f'Ex: {self.bot.command_prefix[0]}setmp +de_cache -de_mirage')

        active_maps = ''.join(f'{m.emoji}  `{m.dev_name}`\n' for m in mdraft_data.map_pool)
        inactive_maps = ''.join(f'{m.emoji}  `{m.dev_name}`\n' for m in ALL_MAPS if m not in mdraft_data.map_pool)

        if not inactive_maps:
            inactive_maps = '*None*'

        embed.add_field(name='__Active Maps__', value=active_maps)
        embed.add_field(name='__Inactive Maps__', value=inactive_maps)
        await ctx.send(embed=embed)

    @setmp.error
    async def setmp_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot set the map pool without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)
