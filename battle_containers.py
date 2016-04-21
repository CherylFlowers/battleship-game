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
from battle_messages import GetUserGames
from battle_messages import SingleMove
from battle_messages import GameHistory


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

GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    GetUserGames,
    websafe_user_key=messages.StringField(1, required=True),
)

MOVE_POST_REQUEST = endpoints.ResourceContainer(
    SingleMove,
    websafe_game_key=messages.StringField(1, required=True),
    websafe_user_key=messages.StringField(2, required=True),
    row=messages.StringField(3, required=True),
    col=messages.IntegerField(4, required=True),
)

GET_GAME_HISTORY_REQUEST = endpoints.ResourceContainer(
    GameHistory,
    websafe_game_key=messages.StringField(1, required=True),
)
