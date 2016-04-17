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


class StringMessage(messages.Message):
    """Outbound string message."""
    message = messages.StringField(1)
