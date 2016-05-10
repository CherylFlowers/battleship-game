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
    email = ndb.StringProperty()


class Game(ndb.Model):
    """A game with 2 users and the status."""
    user1 = ndb.KeyProperty(kind='User', required=True)
    user2 = ndb.KeyProperty(kind='User', required=True)

    # 0 = In Progress, 1 = Finished, 2 = Cancelled
    status = ndb.IntegerProperty(required=True)
    winner = ndb.KeyProperty(kind='User')


class Move(ndb.Model):
    """A move made by a user."""
    game_id = ndb.KeyProperty(kind='Game', required=True)
    user_id = ndb.KeyProperty(kind='User', required=True)
    row = ndb.StringProperty(required=True)
    col = ndb.IntegerProperty(required=True)

    # 0 = miss, 1 = hit, 2 = duplicate move
    status = ndb.IntegerProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)
    hits = ndb.IntegerProperty(required=True)
    miss = ndb.IntegerProperty(required=True)
    sunk = ndb.IntegerProperty(required=True)


class MoveSequence(ndb.Model):
    """Keeps track of the sequence of moves."""
    current_sequence = ndb.IntegerProperty(required=True)


class Boat(ndb.Model):
    """A boat on a users board."""
    game_id = ndb.KeyProperty(kind='Game', required=True)
    user_id = ndb.KeyProperty(kind='User', required=True)

    # 0 = CARRIER, 1 = BATTLESHIP, 2 = SUBMARINE, 3 = DESTROYER, 4 = PATROL
    boat_type = ndb.IntegerProperty(required=True)
    row = ndb.StringProperty(required=True)
    col = ndb.IntegerProperty(required=True)
    hit = ndb.BooleanProperty()
