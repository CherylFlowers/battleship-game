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
