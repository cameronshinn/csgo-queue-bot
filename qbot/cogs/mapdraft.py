#!/usr/bin/env python3
# mapdraft.py
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
               'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/cache.jpg')
de_cbble = Map('Cobblestone', 'de_cbble', '<:de_cbble:632416085899214848>',
               'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/cobblestone.jpg')
de_dust2 = Map('Dust II', 'de_dust2', '<:de_dust2:632416148658323476>',
               'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/dust_ii.jpg')
de_inferno = Map('Inferno', 'de_inferno', '<:de_inferno:632416390112084008>',
                 'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/inferno.jpg')
de_mirage = Map('Mirage', 'de_mirage', '<:de_mirage:632416441551028225>',
                'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/mirage.jpg')
de_nuke = Map('Nuke', 'de_nuke', '<:de_nuke:632416475029962763>',
              'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/nuke.jpg')
de_overpass = Map('Overpass', 'de_overpass', '<:de_overpass:632416513562902529>',
                  'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/overpass.jpg')
de_train = Map('Train', 'de_train', '<:de_train:632416540687335444>',
               'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/train.jpg')
de_vertigo = Map('Vertigo', 'de_vertigo', '<:de_vertigo:632416584870395904>',
                 'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/map_images/vertigo.jpg')

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
        self.footer = 'React to any of the map icons below to ban the corresponding map'

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
        self.guild_maps_left[ctx.guild] = self.map_pool.copy()  # Set or reset map pool
        embed = discord.Embed(title='Map draft has begun!', description=self.maps_left_str(ctx.guild), color=self.color)
        embed.set_footer(text=self.footer)
        msg = await ctx.send(embed=embed)
        await msg.edit(embed=embed)

        for m in self.map_pool:
            await msg.add_reaction(m.emoji)

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

        for m in maps_left.copy():  # Iterate over copy to modify original w/o consequences
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
                    embed.set_footer(text=self.footer)
                    await msg.edit(embed=embed)

                break
