#!/usr/bin/env python3
# mapDraft.py
# cameronshinn

import discord
from discord.ext import commands

class Map:
    def __init__(self, name, dev_name, emoji, image_url):
        self.name = name
        self.dev_name = dev_name
        self.emoji = emoji
        self.image_url = image_url

de_cache = Map('Cache', 'de_cache', '<:de_cache:632416021910650919>',
               'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/cache.png')
de_cbble = Map('Cobblestone', 'de_cbble', '<:de_cbble:632416085899214848>',
               'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/cobblestone.png')
de_dust2 = Map('Dust II', 'de_dust2', '<:de_dust2:632416148658323476>',
               'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/dust_ii.png')
de_inferno = Map('Inferno', 'de_inferno', '<:de_inferno:632416390112084008>',
                 'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/inferno.png')
de_mirage = Map('Mirage', 'de_mirage', '<:de_mirage:632416441551028225>',
                'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/mirage.png')
de_nuke = Map('Nuke', 'de_nuke', '<:de_nuke:632416475029962763>',
              'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/nuke.png')
de_overpass = Map('Overpass', 'de_overpass', '<:de_overpass:632416513562902529>',
                  'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/overpass.png')
de_train = Map('Train', 'de_train', '<:de_train:632416540687335444>',
               'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/train.png')
de_vertigo = Map('Vertigo', 'de_vertigo', '<:de_vertigo:632416584870395904>',
                 'https://github.com/cameronshinn/csgo-queue-bot/blob/master/assets/map_icons/vertigo.png')

map_pool = [
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

class MapDraftCog(commands.Cog):
    """ Handles the map drafer command """

    def __init__(self, bot, color):
        """ Set attributes """
        self.bot = bot
        self.map_pool = map_pool
        self.color = color
        self.guild_msgs = {} # Map guild -> last send map draft message
        self.guild_maps_left = {} # Map guild -> list of maps left in draft

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command """
        await ctx.trigger_typing()

    def maps_left_str(self, guild):
        """ Get the maps left string representation for a given giuld """
        x_emoji = ':heavy_multiplication_x:'
        maps_left = self.guild_maps_left[guild] if guild in self.guild_maps_left.keys() else self.map_pool
        return ''.join(f'{m.emoji}  {m.name}\n' if m in maps_left else f'{x_emoji}  ~~{m.name}~~\n' for m in self.map_pool)

    @commands.command(brief='Start (or restart) a map draft')
    async def mdraft(self, ctx):
        """ Start a map draft by sending a map draft embed panel """
        embed = discord.Embed(title='Map draft has begun!', description=self.maps_left_str(ctx.guild), color=self.color)
        embed.set_footer(text='React to a map icon below to ban the corresponding map')
        msg = await ctx.send(embed=embed)
        await msg.edit(embed=embed)

        for m in self.map_pool:
            await msg.add_reaction(m.emoji)

        self.guild_maps_left[ctx.guild] = self.map_pool.copy()
        self.guild_msgs[ctx.guild] = msg

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """ Remove a map from the draft when a user reacts with the corresponding icon """
        if user == self.bot.user:
            return

        guild = user.guild

        if guild not in self.guild_msgs.keys() or reaction.message.id != self.guild_msgs[guild].id:
            return

        maps_left = self.guild_maps_left[guild]

        for m in maps_left:
            if str(reaction.emoji) == m.emoji:
                async for u in reaction.users():
                    await reaction.remove(u)

                maps_left.remove(m)
                msg = self.guild_msgs[guild]

                if len(maps_left) == 1:
                    map_result = maps_left[0]
                    await msg.clear_reactions()
                    embed_title = f'We\'re going to {map_result.name}! {map_result.emoji}'
                    embed = discord.Embed(title=embed_title, color=self.color)
                    embed.set_image(url=map_result.image_url)
                    embed.set_footer(text=f'Be sure to select {map_result.name} in the PopFlash lobby')
                    await msg.edit(embed=embed)
                    self.guild_maps_left.pop(guild)
                else:
                    embed_title = f'**{user.name}** has banned **{m.name}**'
                    embed = discord.Embed(title=embed_title, description=self.maps_left_str(guild), color=self.color)
                    embed.set_thumbnail(url=m.image_url)
                    embed.set_footer(text='React to a map icon below to ban the corresponding map')
                    await msg.edit(embed=embed)
