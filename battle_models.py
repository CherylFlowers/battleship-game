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
