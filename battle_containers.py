"""

Helper module to hold custom ResourceContainer definitions.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from battle_messages import SingleUser
from battle_messages import NewGame
from battle_messages import CancelGame


USER_POST_REQUEST = endpoints.ResourceContainer(
    SingleUser,
    username=messages.StringField(1, required=True),
)

NEW_GAME_REQUEST = endpoints.ResourceContainer(
    NewGame,
    username1=messages.StringField(1, required=True),
    username2=messages.StringField(2, required=True),
)

CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    CancelGame,
    websafe_game_key=messages.StringField(1, required=True),
)
