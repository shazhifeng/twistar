from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks

from utils import *

class RelationshipTest(unittest.TestCase):    
    @inlineCallbacks
    def setUp(self):
        yield initDB(self.mktemp())
        self.user = yield User(first_name="First", last_name="Last", age=10).save()
        self.avatar = yield Avatar(name="an avatar name", user_id=self.user.id).save()
        self.picture = yield Picture(name="a pic", size=10, user_id=self.user.id).save()
        self.favcolor = yield FavoriteColor(name="blue").save()
        self.config = Registry.getConfig()


    @inlineCallbacks
    def test_belongs_to(self):
        user = yield self.picture.user.get()
        self.assertEqual(user, self.user)


    @inlineCallbacks
    def test_set_belongs_to(self):
        user = yield User(first_name="new one").save()
        yield self.picture.user.set(user)
        self.assertEqual(user.id, self.picture.user_id)


    @inlineCallbacks
    def test_has_many(self):
        # First, make a few pics
        ids = [self.picture.id]
        for _ in range(3):
            pic = yield Picture(user_id=self.user.id).save()
            ids.append(pic.id)
            
        pics = yield self.user.pictures.get()
        picids = [pic.id for pic in pics]
        self.assertEqual(ids, picids)


    @inlineCallbacks
    def test_set_has_many(self):
        # First, make a few pics
        pics = [self.picture]
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [pic.id for pic in pics]

        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [pic.id for pic in results]
        self.assertEqual(picids, resultids)

        # now try resetting
        pics = []
        for _ in range(3):
            pic = yield Picture(name="a pic").save()
            pics.append(pic)
        picids = [pic.id for pic in pics]
        
        yield self.user.pictures.set(pics)
        results = yield self.user.pictures.get()
        resultids = [pic.id for pic in results]
        self.assertEqual(picids, resultids)        


    @inlineCallbacks
    def test_has_one(self):
        avatar = yield self.user.avatar.get()
        self.assertEqual(avatar, self.avatar)


    @inlineCallbacks
    def test_set_has_one(self):
        avatar = yield Avatar(name="another").save()
        yield self.user.avatar.set(avatar)
        yield avatar.refresh()
        self.assertEqual(avatar.user_id, self.user.id)


    @inlineCallbacks
    def test_habtm(self):
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        args = {'user_id': self.user.id, 'favorite_color_id': colors[0].id}
        yield self.config.insert('favorite_colors_users', args)
        args = {'user_id': self.user.id, 'favorite_color_id': colors[1].id}
        yield self.config.insert('favorite_colors_users', args)
        
        newcolors = yield self.user.favorite_colors.get()
        newcolorids = [color.id for color in newcolors]        
        self.assertEqual(newcolorids, colorids)


    @inlineCallbacks
    def test_set_habtm(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        yield user.favorite_colors.set(colors)
        newcolors = yield user.favorite_colors.get()
        newcolorids = [color.id for color in newcolors]        
        self.assertEqual(newcolorids, colorids)        


    @inlineCallbacks
    def test_set_habtm_blank(self):
        user = yield User().save()
        color = yield FavoriteColor(name="red").save()
        colors = [self.favcolor, color]
        colorids = [color.id for color in colors]

        yield user.favorite_colors.set(colors)
        # now blank out
        yield user.favorite_colors.set([])
        newcolors = yield user.favorite_colors.get()
        self.assertEqual(len(newcolors), 0)