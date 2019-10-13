#!/usr/bin python3
# maps.py
# cameronshinn

class Map:
    def __init__(self, name, dev_name, emoji_icon, image_url):
        self.name = name
        self.dev_name = dev_name
        self.emoji_icon = emoji_icon
        self.image_url = image_url

de_cache = Map('Cache', 'de_cache', '<:de_cache:632416021910650919>',
               'https://liquipedia.net/commons/images/thumb/d/d9/Cache_csgo.jpg/533px-Cache_csgo.jpg')
de_cbble = Map('Cobblestone', 'de_cbble', '<:de_cbble:632416085899214848>',
               'https://liquipedia.net/commons/images/thumb/2/27/Cbble_csgo.png/533px-Cbble_csgo.png')
de_dust2 = Map('Dust II', 'de_dust2', '<:de_dust2:632416148658323476>',
               'https://liquipedia.net/commons/images/1/12/Csgo_dust2.0.jpg')
de_inferno = Map('Inferno', 'de_inferno', '<:de_inferno:632416390112084008>',
                 'https://liquipedia.net/commons/images/2/2b/De_new_inferno.jpg')
de_mirage = Map('Mirage', 'de_mirage', '<:de_mirage:632416441551028225>',
                'https://liquipedia.net/commons/images/f/f3/Csgo_mirage.jpg')
de_nuke = Map('Nuke', 'de_nuke', '<:de_nuke:632416475029962763>',
              'https://liquipedia.net/commons/images/5/5e/Nuke_csgo.jpg')
de_overpass = Map('Overpass', 'de_overpass', '<:de_overpass:632416513562902529>',
                  'https://liquipedia.net/commons/images/0/0f/Csgo_overpass.jpg')
de_train = Map('Train', 'de_train', '<:de_train:632416540687335444>',
               'https://liquipedia.net/commons/images/5/56/Train_csgo.jpg')
de_vertigo = Map('Vertigo', 'de_vertigo', '<:de_vertigo:632416584870395904>',
                 'https://liquipedia.net/commons/images/5/59/Csgo_de_vertigo_new.jpg')

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
