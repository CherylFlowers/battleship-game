"""

Holds all methods relating to user actions and/or User kind.

"""


import endpoints

from google.appengine.ext import ndb

from battle_models import User
from battle_models import Game


def _createUser(username, email):
    """
    Create a new User.

    Args:
      username: the name of the user to create.
      email: the email address for the user.

    Returns:
      A User object if the user is successfully created.
    """
    new_user = User(user_name=username,
                    email=email)
    try:
        new_user.put()
    except:
        raise endpoints.BadRequestException('Could not save user.')
    return new_user


def _getUserViaWebsafeKey(websafe_user_key):
    """
    Validates that a user exists and returns the User object.

    Args:
      websafe_user_key: the url-safe key of the user.

    Returns:
      An error is raised if the user doesn't exist.
      If the user exists then a User object is returned.
    """
    try:
        selected_user = ndb.Key(urlsafe=websafe_user_key).get()
    except:
        raise endpoints.BadRequestException('User does not exist.')

    return selected_user


def _userExists(username):
    """
    Query the database for a user via username.

    Args:
      username: the username of the User to get from the database.

    Returns:
      True if the user is found.
      False if the user is not found.
    """
    if User.query(User.user_name == username).get():
        return True
    return False


def _emailExists(email):
    """
    Query the db for an email address.

    Args:
      email: the email to search for.

    Returns:
      True if the email is found.
      False if the email is not found.
    """
    if User.query(User.email == email).get():
        return True
    return False


def _getUserScore(websafe_user_key):
    """
    Determine the total number of games that a user has won or lost.

    Args:
      websafe_user_key: the url-safe key of the user.

    Returns:
      a tuple;
        user name[0]
        games won[1]
        games lost[2]
    """

    # Validate that the user exists and get User object.
    selected_user = _getUserViaWebsafeKey(websafe_user_key)

    # Get the user key.
    user_key = ndb.Key(urlsafe=websafe_user_key)

    # Get games the user won.
    games_won = Game.query(ndb.AND(Game.status == 1, Game.winner == user_key, ndb.OR(
        Game.user1 == user_key, Game.user2 == user_key))).count()

    # Get games the user lost.
    games_lost = Game.query(ndb.AND(Game.status == 1, Game.winner != user_key, ndb.OR(
        Game.user1 == user_key, Game.user2 == user_key))).count()

    # Create a tuple with the username, wins and losses.
    user_score = (selected_user.user_name, games_won, games_lost)

    return user_score


def _getUserScoreMessage(user_score):
    """
    Generate a message with the users wins/losses.

    Args:
      user_score: a tuple with the username[0], games won[1], games lost[2]
      (this can be generated via _getUserScore).

    Returns:
      a string in the format; <username> : Wins <x> : Losses <x>
    """
    return user_score[0] + ' : Wins ' + str(user_score[1]) + ' : Losses ' + str(user_score[2])
