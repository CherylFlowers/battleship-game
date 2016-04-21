"""

Server-side Google App Engine API for Battleship Game; uses Google Cloud Endpoints.

"""


import endpoints

from google.appengine.ext import ndb

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from battle_containers import USER_POST_REQUEST
from battle_containers import NEW_GAME_REQUEST
from battle_containers import CANCEL_GAME_REQUEST

from battle_messages import StringMessage

from battle_models import User
from battle_models import Game


# @endpoints.api BattleshipApi ------------------------------------------------

@endpoints.api(name='battleship',
               version='v1',
               description="Battleship Game API"
               )
class BattleshipApi(remote.Service):
    """
    Battleship API v1
    """

#   _validateBlankUser --------------------------------------------------------

    def _validateBlankUser(self,
                           user_to_validate,
                           custom_error_message
                           ):
        """
        Ensure the username is not blank.

        Args:
          user_to_validate: the username to verify.
          custom_error_message: enter a custom error message.

        Returns:
          Raises a BadRequestException if the user is blank.
          Returns true if the user is not blank.
        """
        if user_to_validate is None:
            raise endpoints.BadRequestException(
                '{} cannot be blank.'.format(custom_error_message))
        return True

#   _getUser ------------------------------------------------------------------

    def _getUser(self,
                 user_to_get
                 ):
        """
        Query the database for a user.

        Args:
          user_to_get: the username to get from the database.

        Returns:
          True if the user is found.
          False if the user is not found.
        """
        if User.query(User.user_name == user_to_get).get():
            return True
        return False

#   @endpoints.method create_user ---------------------------------------------

    @endpoints.method(USER_POST_REQUEST,
                      StringMessage,
                      name='create_user',
                      path='user',
                      http_method='POST'
                      )
    def create_user(self,
                    request
                    ):
        """
        Create a User. Username is required. Username must be unique.
        """
        self._validateBlankUser(request.username, 'Username')

        if self._getUser(request.username):
            raise endpoints.ConflictException(
                '{} user already exists.'.format(request.username))

        new_user = User(user_name=request.username)
        new_user.put()

        return StringMessage(message='{} was successfully created!'.format(request.username))

#   @endpoints.method new_game ------------------------------------------------

    @endpoints.method(NEW_GAME_REQUEST,
                      StringMessage,
                      name='new_game',
                      path='game',
                      http_method='POST'
                      )
    def new_game(self,
                 request
                 ):
        """
        Create a new game.
        """
        # Ensure the users are not blank.
        self._validateBlankUser(request.username1, 'username1')
        self._validateBlankUser(request.username2, 'username2')

        # Ensure the users exist in the database.
        if not self._getUser(request.username1):
            raise endpoints.BadRequestException(
                '{} does not exist.'.format(request.username1))

        if not self._getUser(request.username2):
            raise endpoints.BadRequestException(
                '{} does not exist.'.format(request.username2))

        # Ensure the users are not the same.
        if (request.username1 == request.username2):
            raise endpoints.BadRequestException('Users cannot be the same.')

        # Ensure a game is not already in progress.
        q = Game.query(Game.user1.IN([request.username1, request.username2]),
                       Game.user2.IN([request.username1, request.username2]),
                       Game.status == 0  # In Progress
                       ).count()

        if q > 0:
            raise endpoints.BadRequestException(
                'A game is currently in progress for {} and {}.'.format(
                    request.username1, request.username2))

        # Create a new game.
        a_new_game = Game(
            user1=request.username1,
            user2=request.username2,
            status=0,  # In Progress
        )
        a_new_game.put()

        return StringMessage(message='Game was successfully created!')

#   @endpoints.method cancel_game ---------------------------------------------

    @endpoints.method(CANCEL_GAME_REQUEST,
                      StringMessage,
                      name='cancel_game',
                      path='gameCancel',
                      http_method='POST'
                      )
    def cancel_game(self,
                    request
                    ):
        """
        Cancel a game that's in progress.
        """
        # Raise an exception if the game ID is blank.
        if request.websafe_game_key is None:
            raise endpoints.BadRequestException('Game ID cannot be blank.')

        # Get Game from Datastore.
        try:
            current_game = ndb.Key(urlsafe=request.websafe_game_key).get()
        except:
            return StringMessage(message='Game does not exist.')

        # Notify if the game is already in cancelled status.
        if current_game.status == 2:
            return StringMessage(message='Game is already cancelled.')

        # Notify if the game is finished.
        if current_game.status == 1:
            return StringMessage(message='Game is already finished, cannot cancel.')

        # Set the status of the game to cancelled.
        current_game.status = 2

        # Save the game.
        current_game.put()

        return StringMessage(message='Game was successfully cancelled.')


api = endpoints.api_server([BattleshipApi])  # Register API
