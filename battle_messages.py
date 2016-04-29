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


class SingleMove(messages.Message):
    """Inbound request to make a move."""
    a_game_id = messages.StringField(1)
    a_user_id = messages.StringField(2)
    a_row = messages.StringField(3)
    a_col = messages.IntegerField(4)


class GameHistory(messages.Message):
    """Inbound request for a history of all moves in a game."""
    a_game_id = messages.StringField(1)


class GetGameState(messages.Message):
    """Inbound request for the current state of a game."""
    a_game_id = messages.StringField(1)


class GetBoatList(messages.Message):
    """Inbound request for a list of the users' boat coordinates."""
    a_game_id = messages.StringField(1)
    a_user_id = messages.StringField(2)


class GetSingleUserScore(messages.Message):
    """Inbound request for a single users' wins and losses."""
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


class SingleMoveForList(messages.Message):
    """Outbound message to return a single move."""
    websafe_game_key_for_move = messages.StringField(1)
    websafe_user_key_for_move = messages.StringField(2)
    row = messages.StringField(3)
    col = messages.IntegerField(4)
    status = messages.IntegerField(5)
    sequence = messages.IntegerField(6)


class ListOfMoves(messages.Message):
    """Outbound message to return a list of moves."""
    all_moves = messages.MessageField(SingleMoveForList, 1, repeated=True)


class ReturnGameState(messages.Message):
    """Outbound response to return the state of a game for a user."""
    user_states = messages.MessageField(StringMessage, 1, repeated=True)


class SingleBoatForList(messages.Message):
    """Outbound message to return a single boat."""
    boat_type = messages.IntegerField(1)
    row = messages.StringField(2)
    col = messages.IntegerField(3)


class ListOfBoats(messages.Message)	:
    """Outbound message to return a list of boats."""
    all_boats = messages.MessageField(SingleBoatForList, 1, repeated=True)
