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
from battle_containers import GET_USER_GAMES_REQUEST
from battle_containers import MOVE_POST_REQUEST

from battle_messages import StringMessage
from battle_messages import ListOfGames
from battle_messages import SingleGame

from battle_models import User
from battle_models import Game
from battle_models import Move


# CONSTS ----------------------------------------------------------------------

VALID_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
VALID_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


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

#   _validateAndGetGame -------------------------------------------------------

    def _validateAndGetGame(self,
                            websafe_game_to_validate
                            ):
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

#   _validateAndGetUser -------------------------------------------------------

    def _validateAndGetUser(self,
                            websafe_user_to_validate
                            ):
        """
        Validates that a user exists and returns the User object.

        Args:
          websafe_user_to_validate: the url-safe key of the user.

        Returns:
          An error is raised if the user doesn't exist.
          If the user exists then a User object is returned.
        """
        try:
            selected_user = ndb.Key(urlsafe=websafe_user_to_validate).get()
        except:
            raise endpoints.BadRequestException('User does not exist.')

        return selected_user

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

#   _copyToGameList -----------------------------------------------------------

    def _copyToGameList(self,
                        game_to_copy
                        ):
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
            if hasattr(game_to_copy, field.name):
                setattr(selected_game, field.name,
                        getattr(game_to_copy, field.name))
            elif field.name == "websafeKey":
                # Encode the key so it's suitable to embed in a URL.
                setattr(selected_game, field.name, game_to_copy.key.urlsafe())

        # Verify all values in the game message have been assigned a value.
        selected_game.check_initialized()

        # Return the updated game message.
        return selected_game

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
        current_game = self._validateAndGetGame(request.websafe_game_key)

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

#   @endpoints.method get_user_games ------------------------------------------

    @endpoints.method(GET_USER_GAMES_REQUEST,
                      ListOfGames,
                      name='get_user_games',
                      path='gameGetUserGames',
                      http_method='GET'
                      )
    def get_user_games(self,
                       request
                       ):
        """Return all active games for a user."""
        self._validateBlankUser(request.websafe_user_key, 'websafe_user_key')

        # Get User from Datastore.
        selected_user = self._validateAndGetUser(request.websafe_user_key)

        # Get all games that are currently in progress for that user.
        games = Game.query(ndb.AND(Game.status == 0,
                                   ndb.OR(
                                       Game.user1 == selected_user.user_name,
                                       Game.user2 == selected_user.user_name)))
        games = games.order(Game.user1, Game.user2)

        return ListOfGames(
            all_games=[self._copyToGameList(each_game) for each_game in games]
        )

#   @endpoints.method make_move -----------------------------------------------

    @endpoints.method(MOVE_POST_REQUEST,
                      StringMessage,
                      name='make_move',
                      path='gameMakeMove',
                      http_method='POST'
                      )
    def make_move(self,
                  request
                  ):
        """Make a move. Requires game ID, user ID, row and col."""

        # Validate that the game exists and get Game object.
        current_game = self._validateAndGetGame(request.websafe_game_key)

        # Validate that the user exists and get User object.
        selected_user = self._validateAndGetUser(request.websafe_user_key)

        # Validate the row.
        my_row = request.row.upper()

        if my_row not in VALID_ROWS:
            raise endpoints.BadRequestException(
                'That was not a valid row. Valid rows are one of the following: ABCDEFGHIJ.')

        # Validate the column.
        my_col = int(request.col)

        if my_col not in VALID_COLS:
            raise endpoints.BadRequestException(
                'That was not a valid column. Valid columns are 1-10 inclusive.')

        return_message = ''

        game_key = ndb.Key(urlsafe=request.websafe_game_key)
        user_key = ndb.Key(urlsafe=request.websafe_user_key)

        if Move.query(ndb.AND(Move.game_id == game_key,
                              Move.user_id == user_key,
                              Move.row == my_row,
                              Move.col == my_col
                              )).get():
            return_message = 'Whoops! You already made that move.'
        else:
            # TODO
            # Once boats are implemented determine if the move has hit a boat.

            a_new_move = Move(
                game_id=game_key,
                user_id=user_key,
                row=my_row,
                col=my_col,
                status=0  # miss
            )
            a_new_move.put()
            return_message = 'That was a miss.'

        return StringMessage(message=return_message)


api = endpoints.api_server([BattleshipApi])  # Register API
