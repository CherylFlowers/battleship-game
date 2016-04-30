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
from battle_containers import GET_GAME_HISTORY_REQUEST
from battle_containers import GET_GAME_STATE
from battle_containers import GET_BOAT_LIST
from battle_containers import GET_USER_SCORE

from battle_messages import StringMessage
from battle_messages import ListOfGames
from battle_messages import SingleGame
from battle_messages import ListOfMoves
from battle_messages import SingleMoveForList
from battle_messages import ReturnGameState
from battle_messages import SingleBoatForList
from battle_messages import ListOfBoats
from battle_messages import ListOfRankings

from battle_models import User
from battle_models import Game
from battle_models import Move
from battle_models import MoveSequence
from battle_models import Boat

from random import randint
import string
from operator import itemgetter
from itertools import groupby


# CONSTS ----------------------------------------------------------------------

VALID_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
VALID_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

CARRIER = 0
BATTLESHIP = 1
SUBMARINE = 2
DESTROYER = 3
PATROL = 4

CARRIER_HITS = 5
BATTLESHIP_HITS = 4
SUBMARINE_HITS = 3
DESTROYER_HITS = 3
PATROL_HITS = 2

BOARD_ROWS = "ABCDEFGHIJ"


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

#   _moveHasHitABoat ----------------------------------------------------------

    def _moveHasHitABoat(self,
                         game_id,
                         user_id,
                         move_row,
                         move_col
                         ):
        """
        Determine if the users move has hit a boat.

        Args:
          game_id: the id of the game being played.
          user_id: the id of the user that's making the move.
          move_row: the row of the users move.
          move_col: the col of the users move.

        Returns:
          True if the move has hit a boat.
          False if the move did not hit a boat.
        """
        # Get the game so we can determine who the users' opponent is.
        selected_game = self._validateAndGetGame(game_id.urlsafe())

        # Grab the opponent user id.
        if selected_game.user1 == user_id:
            opponent_user_id = selected_game.user2
        else:
            opponent_user_id = selected_game.user1

        # Check the opponents board.
        if Boat.query(Boat.game_id == game_id,
                      Boat.user_id == opponent_user_id,
                      Boat.row == move_row,
                      Boat.col == move_col).get():
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

#   _copyToMoveList -----------------------------------------------------------

    def _copyToMoveList(self,
                        move_to_copy
                        ):
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
            if hasattr(move_to_copy, field.name):
                setattr(selected_move, field.name,
                        getattr(move_to_copy, field.name))
            elif (field.name == "websafe_game_key_for_move"):
                # Encode the key so it's suitable to embed in a URL.
                setattr(selected_move, field.name,
                        move_to_copy.game_id.urlsafe())
            elif (field.name == "websafe_user_key_for_move"):
                setattr(selected_move, field.name,
                        move_to_copy.user_id.urlsafe())

        # Verify all values in the move message have been assigned a value.
        selected_move.check_initialized()

        # Return the updated move message.
        return selected_move

#   _copyToBoatList -----------------------------------------------------------

    def _copyToBoatList(self,
                        boat_to_copy
                        ):
        """
        Populate the outbound boat message with values from boat_to_copy.

        Args:
            boat_to_copy: the boat object to copy to the outbound message

        Returns:
            an outbound message populated with info from boat_to_copy arg
        """
        selected_boat = SingleBoatForList()

        # Iterate through all fields in the boat message.
        for field in selected_boat.all_fields():
            # If a field in the boat_to_copy arg matches a field in the
            # boat message, copy the value from the arg to the message.
            if hasattr(boat_to_copy, field.name):
                setattr(selected_boat, field.name,
                        getattr(boat_to_copy, field.name))

        # Verify all values in the boat message have been assigned a value.
        selected_boat.check_initialized()

        # Return the updated boat message.
        return selected_boat

#   _getUsersLastMove ---------------------------------------------------------

    def _getUsersLastMove(self,
                          game_key,
                          user_key
                          ):
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

#   _getGameStateForUser ------------------------------------------------------

    def _getGameStateForUser(self,
                             game_key,
                             selected_game,
                             user_to_get
                             ):
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
        last_user_move = self._getUsersLastMove(game_key, user_key)

        # Need to get the users' name.
        user_profile = self._validateAndGetUser(websafe_user_key)

        if last_user_move is None:
            return user_profile.user_name + ' has not made any moves yet.'

        return 'User ' + str(user_profile.user_name) + ' : Hits ' + str(last_user_move.hits) + ' : Miss ' + str(last_user_move.miss) + ' : Sunk ' + str(last_user_move.sunk)

#   _buildBoard ---------------------------------------------------------------

    def _buildBoard(self):
        """
        Build a 10x10 board.

        Returns:
          A list of tuples representing a blank 10x10 board.
        """
        x = 1
        y = 1
        master_coord = []

        for x in range(1, 11):
            for y in range(1, 11):
                single_coord = [x, y]
                master_coord.append(single_coord)
                y += 1
            x += 1

        return master_coord

#   _addBoat ------------------------------------------------------------------

    def _addBoat(self,
                 game_key,
                 user_key,
                 master_coord,
                 boat_type,
                 boat_hits
                 ):
        """
        Add a boat to a users' board.

        Args:
          game_key: the key of the game that's being played.
          user_key: the key of the user that's playing.
          master_coord: the co-ordinates that are still available.
          boat_type: the type of boat that's being added.
          boat_hits: the number of hits to sink the boat.

        Returns:
          True if the boat was successfully added to the players' board.
          False if the boat could not be added. Will attempt 5 times.
        """
        # Attempt to place the boat on the users' board. Since this method is
        # using random rows and cols it may eventually come into conflict with
        # another boat. If that's the case, the method will try up to 5 times
        # to reposition the new boat on the board (for sanity sake). If it's
        # still unsuccessful then the method will return false.
        for iBoatAttempts in range(0, 6):
            # Determine if the boat should be placed horizontal or vertical.
            direction = randint(0, 1)

            # The list_value will be opposite of the direction value as it
            # will be retrieving the available coordinates for the boat.
            if direction == 0:
                list_value = 1
            else:
                list_value = 0

            # Grab a starting point for the boat.
            # If direction = 0 then start_point is a row
            # If direction = 1 then start_point is a col
            start_point = randint(1, 10)

            # Search the master list for all open coords on
            # the start_point (row or col).
            available_coord = []

            for mc in range(0, len(master_coord)):
                if master_coord[mc][direction] == start_point:
                    available_coord.append(master_coord[mc][list_value])

            # Sort the coordinates so it's easier to find a group of coords.
            available_coord.sort()

            # Determine if the ranges in the available_coord are large
            # enough to hold the boat.
            #   enumerate(available_coord) - attach an incrementing index to each coord
            #   lambda (i, x): i - x) - subtract the element index from the element
            #   value to determine grouping characteristics

            boat_coord = []

            for key, group in groupby(enumerate(available_coord), lambda (i, x): i - x):
                group = map(itemgetter(1), group)
                if len(group) >= boat_hits:
                    boat_coord = group
                    break

            # If boat_coord is empty, then it means that the boat cannot
            # fit on this row/col. Start over and find a new set of coords.
            if len(boat_coord) == 0:
                continue

            # Add the boat coordinates to the Boat table.
            for each_coord in range(0, len(boat_coord)):
                if each_coord + 1 > boat_hits:
                    break

                if direction == 0:
                    boat_row = start_point
                    boat_col = boat_coord[each_coord]
                else:
                    boat_row = boat_coord[each_coord]
                    boat_col = start_point

                new_boat = Boat(
                    game_id=game_key,
                    user_id=user_key,
                    boat_type=boat_type,
                    row=BOARD_ROWS[boat_row],
                    col=boat_col
                )
                new_boat.put()

                new_boat_coord = (new_boat.row, new_boat.col)

                # Remove coords from master coord so they can't be used again.
                for mc in range(0, len(master_coord)):
                    if master_coord[mc] == new_boat_coord:
                        del master_coord[mc]
                        break

            # The boat was successfully added to the board.
            return True

        # The method tried 5 times to add the boat to the board and was
        # unsuccessful.
        return False

#   _getUserScore -------------------------------------------------------------

    def _getUserScore(self,
                      websafe_user_key
                      ):
        """
        Determine the total number of games that a user has won or lost.

        Args:
          websafe_user_key: the user to search for

        Returns:
          a tuple with the use rname[0], games won[1] and games lost[2]
        """

        # Validate that the user exists and get User object.
        selected_user = self._validateAndGetUser(websafe_user_key)

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

#   _getUserScoreMessage ------------------------------------------------------

    def _getUserScoreMessage(self,
                             user_score,
                             ):
        """
        Generate a message with the users wins/losses.

        Args:
          user_score: a tuple with the games won[0], games lost[1], username[2]
                      this can be generated via _getUserScore.

        Returns:
          a string in the format; <username> : Wins <x> : Losses <x>
        """
        return user_score[0] + ' : Wins ' + str(user_score[1]) + ' : Losses ' + str(user_score[2])

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
        user1_key = ndb.Key(urlsafe=request.websafe_username1_key)
        user2_key = ndb.Key(urlsafe=request.websafe_username2_key)

        # Ensure the users exist in the database.
        if not user1_key.get():
            raise endpoints.BadRequestException(
                'websafe_username1_key does not exist.')

        if not user2_key.get():
            raise endpoints.BadRequestException(
                'websafe_username2_key does not exist.')

        # Ensure the users are not the same.
        if (request.websafe_username1_key == request.websafe_username2_key):
            raise endpoints.BadRequestException('Users cannot be the same.')

        # Ensure a game is not already in progress.
        q = Game.query(Game.user1.IN([user1_key, user2_key]),
                       Game.user2.IN([user1_key, user2_key]),
                       Game.status == 0  # In Progress
                       ).count()

        if q > 0:
            raise endpoints.BadRequestException(
                'A game is currently in progress for these users.')

        # Create a new game.
        a_new_game = Game(
            user1=user1_key,
            user2=user2_key,
            status=0,  # In Progress
        )
        game_key = a_new_game.put()

        # Auto-generate all boats on user 1's board.

        # Get a list of all available co-ords on the board.
        master_coord_user1 = self._buildBoard()

        self._addBoat(game_key,
                      user1_key,
                      master_coord_user1,
                      CARRIER,
                      CARRIER_HITS)

        self._addBoat(game_key,
                      user1_key,
                      master_coord_user1,
                      BATTLESHIP,
                      BATTLESHIP_HITS)

        self._addBoat(game_key,
                      user1_key,
                      master_coord_user1,
                      SUBMARINE,
                      SUBMARINE_HITS)

        self._addBoat(game_key,
                      user1_key,
                      master_coord_user1,
                      DESTROYER,
                      DESTROYER_HITS)

        self._addBoat(game_key,
                      user1_key,
                      master_coord_user1,
                      PATROL,
                      PATROL_HITS)

        # Auto-generate all boats on user 2's board.

        # Get a list of all available co-ords on the board.
        master_coord_user2 = self._buildBoard()

        self._addBoat(game_key,
                      user2_key,
                      master_coord_user2,
                      CARRIER,
                      CARRIER_HITS)

        self._addBoat(game_key,
                      user2_key,
                      master_coord_user2,
                      BATTLESHIP,
                      BATTLESHIP_HITS)

        self._addBoat(game_key,
                      user2_key,
                      master_coord_user2,
                      SUBMARINE,
                      SUBMARINE_HITS)

        self._addBoat(game_key,
                      user2_key,
                      master_coord_user2,
                      DESTROYER,
                      DESTROYER_HITS)

        self._addBoat(game_key,
                      user2_key,
                      master_coord_user2,
                      PATROL,
                      PATROL_HITS)

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

        # Get the next move sequence. The sequence is used to generate
        # the game history.
        internal_move_counter = MoveSequence.query().get()

        if internal_move_counter is None:
            # If this is the first time the sequence counter is
            # being used, init it to 1.
            internal_move_counter = MoveSequence(current_sequence=1)

        # Query the Move kind for the last move for the user.
        # The Move kind stores a running total of hits, miss and sunk.
        # Use/increment these values for the next move.
        last_user_move = self._getUsersLastMove(game_key, user_key)

        if last_user_move is None:
            last_user_move = Move(hits=0, miss=0, sunk=0)

        a_new_move = Move(
            game_id=game_key,
            user_id=user_key,
            row=my_row,
            col=my_col,
            status=0,
            hits=last_user_move.hits,
            miss=last_user_move.miss,
            sunk=last_user_move.sunk,
            sequence=internal_move_counter.current_sequence
        )

        if Move.query(ndb.AND(Move.game_id == game_key,
                              Move.user_id == user_key,
                              Move.row == my_row,
                              Move.col == my_col
                              )).get():
            # Don't increment the hits, miss or sunk here,
            # they have already been accounted for.
            a_new_move.status = 2  # duplicate move
            return_message = 'Whoops! You already made that move.'
        else:
            # Determine if the move has hit a boat.
            if self._moveHasHitABoat(game_key,
                                     user_key,
                                     my_row,
                                     my_col
                                     ):
                a_new_move.status = 1  # hit
                a_new_move.hits += 1
                return_message = 'That was a hit!'

                # TODO
                # Determine if the move has sunk a boat.
                # a_new_move.sunk += 1
                # return_message = 'You sunk the {}!'.format(name_of_ship)
            else:
                a_new_move.status = 0  # miss
                a_new_move.miss += 1
                return_message = 'That was a miss.'

        # Save the Move.
        a_new_move.put()

        # Increment the sequence and save that too.
        internal_move_counter.current_sequence += 1
        internal_move_counter.put()

        return StringMessage(message=return_message)

#   @endpoints.method get_game_history ----------------------------------------

    @endpoints.method(GET_GAME_HISTORY_REQUEST,
                      ListOfMoves,
                      name='get_game_history',
                      path='gameGetHistory',
                      http_method='GET'
                      )
    def get_game_history(self,
                         request
                         ):
        """Get a list of all moves for a game."""
        # Raise an exception if the game ID is blank.
        if request.websafe_game_key is None:
            raise endpoints.BadRequestException(
                'websafe_game_key cannot be blank.')

        game_key = ndb.Key(urlsafe=request.websafe_game_key)

        # Get all moves for a game.
        moves = Move.query(Move.game_id == game_key)
        moves = moves.order(Move.sequence)

        return ListOfMoves(
            all_moves=[self._copyToMoveList(each_move) for each_move in moves]
        )

#   @endpoints.method get_game ------------------------------------------------

    @endpoints.method(GET_GAME_STATE,
                      ReturnGameState,
                      name='get_game',
                      path='gameGetState',
                      http_method='GET'
                      )
    def get_game(self,
                 request
                 ):
        """Returns the current state of the game ie. Username : Hits 3 : Miss 12 : Sunk 0"""

        # Get the game info and the game key.
        selected_game = self._validateAndGetGame(request.websafe_game_key)
        game_key = ndb.Key(urlsafe=request.websafe_game_key)

        user_states = []

        # Get game state for user 1.
        user_states.append(self._getGameStateForUser(
            game_key, selected_game, 1))

        # Get game state for user 2.
        user_states.append(self._getGameStateForUser(
            game_key, selected_game, 2))

        # Return the pre-formatted state messages.
        # return ReturnGameState(user_states=[StringMessage(each_state) for
        # each_state in user_states])
        return ReturnGameState(user_states=[StringMessage(message=each_state) for each_state in user_states])

#   @endpoints.method get_user_boats ------------------------------------------

    @endpoints.method(GET_BOAT_LIST,
                      ListOfBoats,
                      name='get_user_boats',
                      path='getUserBoats',
                      http_method='GET'
                      )
    def get_user_boats(self,
                       request
                       ):
        """Get a list of a users' boat coordinates for a game."""

        # Get the game key.
        self._validateAndGetGame(request.websafe_game_key)
        game_key = ndb.Key(urlsafe=request.websafe_game_key)

        # Get the user key.
        self._validateAndGetUser(request.websafe_user_key)
        user_key = ndb.Key(urlsafe=request.websafe_user_key)

        # Grab all the boat coords for this user for the game.
        boat_list = Boat.query(Boat.game_id == game_key,
                               Boat.user_id == user_key).order(Boat.boat_type, Boat.col, Boat.row)

        return ListOfBoats(all_boats=[self._copyToBoatList(each_boat) for each_boat in boat_list])

#   @endpoints.method get_user_scores -----------------------------------------

    @endpoints.method(GET_USER_SCORE,
                      StringMessage,
                      name='get_user_score',
                      path='getUserScore',
                      http_method='GET'
                      )
    def get_user_score(self,
                       request
                       ):
        """Get the number of games that a user has won and lost."""
        user_score = self._getUserScore(request.websafe_user_key)
        return StringMessage(message=self._getUserScoreMessage(user_score))

#   @endpoints.method get_user_rankings ---------------------------------------

    @endpoints.method(message_types.VoidMessage,
                      ListOfRankings,
                      name='get_user_rankings',
                      path='getUserRankings',
                      http_method='GET'
                      )
    def get_user_rankings(self,
                          request
                          ):
        """Get a list of users ordered by wins/losses."""
        all_rankings = []

        # Get a list of all users.
        all_users = User.query()

        # Iterate through the users.
        for each_user in all_users:
            # Get the users' score.
            single_rank = self._getUserScore(each_user.key.urlsafe())

            # Only include the user if they've actually played a game.
            if (single_rank[1] == 0) and (single_rank[2] == 0):
                continue

            # Save the score to the main list.
            all_rankings.append(single_rank)

        # Sort the list by losses ascending first ie. loss 1, loss 5, loss 8
        all_rankings = sorted(all_rankings,
                              key=itemgetter(2))

        # Then sort it by wins descending ie. wins 10, wins 2, wins 1
        all_rankings = sorted(all_rankings,
                              key=itemgetter(1),
                              reverse=True)

        # Return the user rankings.
        return ListOfRankings(rankings=[StringMessage(message=self._getUserScoreMessage(each_rank)) for each_rank in all_rankings])


api = endpoints.api_server([BattleshipApi])  # Register API
