"""

Helper module to hold custom ProtoRPC messages types.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote


class SingleUser(messages.Message):
    """Inbound user information."""
    a_username = messages.StringField(1)


class NewGame(messages.Message):
    """Inbound info for a new game."""
    a_username1 = messages.StringField(1)
    a_username2 = messages.StringField(2)


class StringMessage(messages.Message):
    """Outbound string message."""
    message = messages.StringField(1)
