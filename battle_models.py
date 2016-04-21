"""

Helper module to hold Datastore models.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile."""
    user_name = ndb.StringProperty(required=True)


class Game(ndb.Model):
    """A game with 2 users and the status."""
    user1 = ndb.StringProperty(required=True)
    user2 = ndb.StringProperty(required=True)

    # 0 = In Progress, 1 = Finished, 2 = Cancelled
    status = ndb.IntegerProperty(required=True)


class Move(ndb.Model):
    """A move made by a user."""
    game_id = ndb.KeyProperty(kind='Game', required=True)
    user_id = ndb.KeyProperty(kind='User', required=True)
    row = ndb.StringProperty(required=True)
    col = ndb.IntegerProperty(required=True)

    # 0 = miss, 1 = hit
    status = ndb.IntegerProperty(required=True)
