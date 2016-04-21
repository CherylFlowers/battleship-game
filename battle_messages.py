"""

Helper module to hold custom ProtoRPC messages types.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote


#   Inbound Requests ----------------------------------------------------------


class SingleUser(messages.Message):
    """Inbound user information."""
    a_username = messages.StringField(1)


class NewGame(messages.Message):
    """Inbound info for a new game."""
    a_username1 = messages.StringField(1)
    a_username2 = messages.StringField(2)


class CancelGame(messages.Message):
    """Inbound request to cancel a game."""
    a_game_id = messages.StringField(1)


class GetUserGames(messages.Message):
    """Inbound request for all users' active games."""
    a_user_id = messages.StringField(1)


#   Outbound Response ---------------------------------------------------------


class StringMessage(messages.Message):
    """Outbound string message."""
    message = messages.StringField(1)


class SingleGame(messages.Message):
    """Outbound message to return a single game."""
    user1 = messages.StringField(1)
    user2 = messages.StringField(2)
    status = messages.IntegerField(3, variant=messages.Variant.INT32)
    websafeKey = messages.StringField(4)


class ListOfGames(messages.Message):
    """Outbound message to return a list of games."""
    all_games = messages.MessageField(SingleGame, 1, repeated=True)
