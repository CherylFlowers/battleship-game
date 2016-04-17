"""

Helper module to hold custom ResourceContainer definitions.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from battle_messages import SingleUser


USER_POST_REQUEST = endpoints.ResourceContainer(
    SingleUser,
    username=messages.StringField(1, required=True),
)
