"""

Holds all methods relating to game actions and/or Game kind.

"""


import endpoints

from google.appengine.ext import ndb

from battle_models import Game
from battle_models import Boat
from battle_models import Move

from battle_consts import TOTAL_HITS

from battle_messages import SingleGame
from battle_messages import SingleMoveForList

from battle_users import _getUserViaWebsafeKey


def _validateAndGetGame(websafe_game_to_validate):
    """
    Validates that a game exists and returns the Game object.

    Args:
      websafe_game_to_validate: the url-safe key of the game.

    Returns:
      An error is raised if the game doesn't exist.
      If the game exists then a Game object is returned.
    """
    try:
        selected_game = ndb.Key(urlsafe=websafe_game_to_validate).get()
    except:
        raise endpoints.BadRequestException('Game does not exist.')

    return selected_game


def _userHasWonGame(game_key, user_key):
    """
    Determine if the user has won the game.

    Args:
      game_key: the game id of the game to verify
      user_key: the user id of the user that just made a move
    Returns:
      True if the user has just won.
      False if the user did not win.
    """
    # Get the game so we can determine who the users' opponent is.
    selected_game = _validateAndGetGame(game_key.urlsafe())

    # Grab the opponent user id.
    if selected_game.user1 == user_key:
        opponent_user_id = selected_game.user2
    else:
        opponent_user_id = selected_game.user1

    if Boat.query(Boat.game_id == game_key,
                  Boat.user_id == opponent_user_id,
                  Boat.hit == True).count() == TOTAL_HITS:
        return True
    return False


def _copyGameToList(game_to_copy):
    """
    Populate the outbound game message with values from game_to_copy.

    Args:
      game_to_copy: the game object to copy to the outbound message

    Returns:
      an outbound message populated with info from game_to_copy arg
    """
    selected_game = SingleGame()

    # Iterate through all fields in the game message.
    for field in selected_game.all_fields():
        # If a field in the game_to_copy arg matches a field in the
        # game message, copy the value from the arg to the message.
        if field.name == "user1":
            setattr(selected_game, field.name, game_to_copy.user1.urlsafe())
        elif field.name == "user2":
            setattr(selected_game, field.name, game_to_copy.user2.urlsafe())
        elif field.name == "websafeKey":
            # Encode the key so it's suitable to embed in a URL.
            setattr(selected_game, field.name, game_to_copy.key.urlsafe())
        elif hasattr(game_to_copy, field.name):
            setattr(selected_game, field.name,
                    getattr(game_to_copy, field.name))

    # Verify all values in the game message have been assigned a value.
    selected_game.check_initialized()

    # Return the updated game message.
    return selected_game


def _copyMoveToList(move_to_copy):
    """
    Populate the outbound move message with values from move_to_copy.

    Args:
      move_to_copy: the move object to copy to the outbound message

    Returns:
      an outbound message populated with info from move_to_copy arg
    """
    selected_move = SingleMoveForList()

    # Iterate through all fields in the move message.
    for field in selected_move.all_fields():
        # If a field in the move_to_copy arg matches a field in the
        # move message, copy the value from the arg to the message.
        if (field.name == "websafe_user_key_for_move"):
            setattr(selected_move, field.name, move_to_copy.user_id.urlsafe())
        if (field.name == "status"):
            temp_status = ''

            if move_to_copy.status == 0:
                temp_status = 'Miss'

            if move_to_copy.status == 1:
                temp_status = 'Hit'

            if move_to_copy.status == 2:
                temp_status = 'Duplicate'

            setattr(selected_move, field.name, temp_status)
        elif hasattr(move_to_copy, field.name):
            setattr(selected_move, field.name,
                    getattr(move_to_copy, field.name))

    # Verify all values in the move message have been assigned a value.
    selected_move.check_initialized()

    # Return the updated move message.
    return selected_move


def _getUsersLastMove(game_key, user_key):
    """
    Return the last move that the user made in a specific game.

    Args:
      game_key: the key of the game that the user is playing.
      user_key: the key of the user to get the move for.

    Returns:
      A Move object.
    """
    return Move.query(Move.game_id == game_key,
                      Move.user_id == user_key).order(-Move.sequence).get()


def _getGameLastMove(game_key):
    """
    Return the last move made in a specific game.

    Args:
      game_key: the key of the game.

    Returns:
      A Move object.
    """
    return Move.query(Move.game_id == game_key).order(-Move.sequence).get()


def _getGameStateForUser(game_key, selected_game, user_to_get):
    """
    Get the game state for a user for a selected game.

    Args:
      game_key: the key of the game.
      selected_game: the Game object.
      user_to_get: an integer indicating which user to get the state for.

    Returns:
      A string in the format; <username> : Hits <x> : Miss <x> : Sunk <x>
    """
    # Using the game info, get the user key.
    if user_to_get == 1:
        user_key = selected_game.user1
        websafe_user_key = selected_game.user1.urlsafe()
    else:
        user_key = selected_game.user2
        websafe_user_key = selected_game.user2.urlsafe()

    # Get the last user move. The move contains the sum
    # of hits, misses and sunk boats.
    last_user_move = _getUsersLastMove(game_key, user_key)

    # Need to get the users' name.
    user_profile = _getUserViaWebsafeKey(websafe_user_key)

    if last_user_move is None:
        return user_profile.user_name + ' has not made any moves yet.'

    return 'User ' + str(user_profile.user_name) + ' : Hits ' + str(last_user_move.hits) + ' : Miss ' + str(last_user_move.miss) + ' : Sunk ' + str(last_user_move.sunk)


def _gameInProgress(user1_key, user2_key):
    """
    Determine if two users have a game in progress.
    It doesn't really matter which games, just get a count.

    Args:
      user1_key: the key of one of the users in the game.
      user2_key: the key of one of the users in the game.

    Returns:
      True if there's a game in progress.
      False if there's no game in progress.
    """
    q = Game.query(Game.user1.IN([user1_key, user2_key]),
                   Game.user2.IN([user1_key, user2_key]),
                   Game.status == 0  # In Progress
                   ).count()
    if q > 0:
        return True
    return False


def _getListOfGamesForUser(user_key):
    """
    Get a list of all games that are currently in progress for a user.

    Args:
      user_key: the user to get the games for.

    Returns:
      A list of Game entities.
    """
    games = Game.query(ndb.AND(Game.status == 0, ndb.OR(
        Game.user1 == user_key, Game.user2 == user_key)))
    games = games.order(Game.user1, Game.user2)
    return games


def _getAllMovesForAGame(game_key):
    """
    Get a listing of all moves for a game.

    Args:
      game_key: the game that you want to get moves for.

    Return
      a list of all moves in a game ordered by sequence.
    """
    moves = Move.query(Move.game_id == game_key)
    moves = moves.order(Move.sequence)
    return moves
