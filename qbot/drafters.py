#!/usr/bin/env python3
# drafters.py
# cameronshinn

from discord.ext import commands

import maps

class MapDraftMsg:
    def __init__(self, guild, channel, map_pool):
        self.maps_left = map_pool.copy()
        self.msg = 

class MapDrafter(commands.Cog):
    def __init__(self, client, map_pool, color):
        self.client
        self.map_pool = maps.map_pool
        self.maps_left = copy.copy(self.map_pool)
        self.color = color
        self.msg = await self.send_panel(channel)

    @commands.Cog.listener()
    async def on_message(message):
        if message.split(' ')[0] == 'q!mdraft':
            MapDraftMsg(message.guild, message.channel)

    @commands.Cog.listener():
    async def on_reaction_add(self, reaction, user):
        if user == self.client.user or reaction.message != self.msg: # TODO: Also add checking valid emoji???
            return

        await self.ban_map(reaction, user)

    @property
    def maps_left_str(self):
        return ''.join(f'{m.emoji_icon}  {m.name}\n' if m in self.maps_left else f':heavy_multiplication_x:  ~~{m.name}~~\n' for m in self.map_pool)

    async def send_panel(self, channel):
        embed_title = f'Map draft has begun!'
        embed = discord.Embed(title=self.embed_title, description=self.maps_left_str, color=self.color)
        embed.set_footer(text='React to a map icon below to ban the corresponding map')
        msg = await channel.send(embed=embed)
        await msg.edit(embed=embed) # Edit it so the placement doesn't shift when picking first map # TODO: try removing all args???

        for m in self.maps_left:
            await msg.add_reaction(m.emoji_icon)

        return msg

    async def ban_map(self, reaction, user):
        if self.msg == None or self.msg.id != reaction.message.id:
            return self.msg

        for m in self.maps_left:
            if str(reaction.emoji) == m.emoji_icon:
                async for u in reaction.users():
                    await reaction.remove(u)

                self.maps_left.remove(m)

                if len(self.maps_left) == 1:
                    map_result = self.maps_left[0]
                    await self.msg.clear_reactions()
                    embed_title = f'We\'re going to {map_result.name}! {map_result.emoji_icon}'
                    embed = discord.Embed(title=self.embed_title, color=self.color)
                    embed.set_image(url=map_result.image_url)
                    embed.set_footer(text=f'Be sure to select {map_result.name} in the PopFlash lobby')
                    await self.msg.edit(embed=embed)
                    self.maps_left = copy.copy(self.map_pool)
                    self.msg = None
                    return self.msg
                else:
                    embed_title = f'**{user.name}** has banned **{m.name}**'
                    embed = discord.Embed(title=self.embed_title, description=self.maps_left_str, color=self.color)
                    embed.set_thumbnail(url=m.image_url)
                    embed.set_footer(text='React to a map icon below to ban the corresponding map')
                    await self.msg.edit(embed=self.embed)
                    return self.msg
