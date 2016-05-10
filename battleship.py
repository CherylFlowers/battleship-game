"""

Server-side Google App Engine API for Battleship Game; uses Google Cloud Endpoints.

"""


import endpoints

from google.appengine.ext import ndb

from protorpc import messages
from protorpc import message_types
from protorpc import remote

import battle_consts
import battle_users
import battle_game
import battle_boat
import battle_utils

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
from battle_messages import ListOfMoves
from battle_messages import ReturnGameState
from battle_messages import ListOfBoats
from battle_messages import ListOfRankings

from battle_models import User
from battle_models import Game
from battle_models import Move
from battle_models import MoveSequence
from battle_models import Boat

import string
from operator import itemgetter


@endpoints.api(name='battleship',
               version='v1',
               description="Battleship Game API"
               )
class BattleshipApi(remote.Service):
    """
    Battleship API v1
    """

    @endpoints.method(USER_POST_REQUEST,
                      StringMessage,
                      name='create_user',
                      path='createUser',
                      http_method='POST'
                      )
    def create_user(self, request):
        """
        Create a User. Username is required. Username must be unique.
        """
        if battle_users._userExists(request.username):
            raise endpoints.ConflictException(
                '{} already exists. Please enter a unique username.'.format(request.username))

        new_user = battle_users._createUser(request.username)

        return StringMessage(message='User {} successfully created! Websafe Key: {}'.format(request.username, new_user.key.urlsafe()))

    @endpoints.method(NEW_GAME_REQUEST,
                      StringMessage,
                      name='new_game',
                      path='newGame',
                      http_method='POST'
                      )
    def new_game(self, request):
        """
        Create a new game.
        """
        user1_key = battle_utils._getNDBKey(request.websafe_username1_key)
        user2_key = battle_utils._getNDBKey(request.websafe_username2_key)

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
        if battle_game._gameInProgress(user1_key, user2_key):
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
        battle_boat._generateBoardAndBoats(game_key, user1_key)

        # Auto-generate all boats on user 2's board.
        battle_boat._generateBoardAndBoats(game_key, user2_key)

        return StringMessage(message='Game was successfully created! Websafe Key: {}'.format(game_key.urlsafe()))

    @endpoints.method(CANCEL_GAME_REQUEST,
                      StringMessage,
                      name='cancel_game',
                      path='cancelGame',
                      http_method='POST'
                      )
    def cancel_game(self, request):
        """
        Cancel a game that's in progress.
        """
        current_game = battle_game._validateAndGetGame(request.websafe_game_key)

        # Notify if the game is already in cancelled status.
        if current_game.status == 2:
            return StringMessage(message='Game is already cancelled.')

        # Notify if the game is finished.
        if current_game.status == 1:
            return StringMessage(message='Game is already finished, cannot cancel.')

        # Set the status of the game to cancelled.
        current_game.status = 2
        current_game.put()

        return StringMessage(message='Game was successfully cancelled.')

    @endpoints.method(GET_USER_GAMES_REQUEST,
                      ListOfGames,
                      name='get_user_games',
                      path='getUserGames',
                      http_method='GET'
                      )
    def get_user_games(self, request):
        """Return all active games for a user."""

        user_key = battle_utils._getNDBKey(request.websafe_user_key)

        games = battle_game._getListOfGamesForUser(user_key)

        return ListOfGames(
            all_games=[battle_game._copyGameToList(
                each_game) for each_game in games]
        )

    @endpoints.method(MOVE_POST_REQUEST,
                      StringMessage,
                      name='make_move',
                      path='makeMove',
                      http_method='POST'
                      )
    def make_move(self, request):
        """Make a move. Requires game ID, user ID, row and col."""

        # Validate that the game exists and get Game object.
        current_game = battle_game._validateAndGetGame(request.websafe_game_key)

        # Validate that the user exists and get User object.
        selected_user = battle_users._getUserViaWebsafeKey(
            request.websafe_user_key)

        # Validate the row.
        my_row = request.row.upper()

        if my_row not in battle_consts.VALID_ROWS:
            raise endpoints.BadRequestException(
                'That was not a valid row. Valid rows are one of the following: ABCDEFGHIJ.')

        # Validate the column.
        my_col = int(request.col)

        if my_col not in battle_consts.VALID_COLS:
            raise endpoints.BadRequestException(
                'That was not a valid column. Valid columns are 1-10 inclusive.')

        return_message = ''

        game_key = battle_utils._getNDBKey(request.websafe_game_key)
        user_key = battle_utils._getNDBKey(request.websafe_user_key)

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
        last_user_move = battle_game._getUsersLastMove(game_key, user_key)

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
            # Get the Boat entity.
            selected_boat = battle_boat._getBoat(game_key,
                                                 user_key,
                                                 my_row,
                                                 my_col
                                                 )

            # If the boat is returned then the user has a hit!
            if selected_boat:
                # Log a hit on the boat.
                selected_boat.hit = True
                selected_boat.put()

                # Set the move status to a hit and increment the hit counter.
                a_new_move.status = 1  # hit
                a_new_move.hits += 1
                return_message = 'That was a hit!'

                # Determine if the move has sunk a boat.
                if battle_boat._boatIsSunk(game_key,
                                           user_key,
                                           selected_boat.boat_type
                                           ):

                    if battle_game._userHasWonGame(game_key,
                                                   user_key
                                                   ):
                        return_message = 'You won!'
                    else:
                        # The move has sunk a boat! Notify the user.
                        a_new_move.sunk += 1

                        name_of_ship = '<error: unknown ship>'

                        if boat_type == battle_consts.CARRIER:
                            name_of_ship = 'Carrier'

                        if boat_type == battle_consts.BATTLESHIP:
                            name_of_ship = 'Battleship'

                        if boat_type == battle_consts.SUBMARINE:
                            name_of_ship = 'Submarine'

                        if boat_type == battle_consts.DESTROYER:
                            name_of_ship = 'Destroyer'

                        if boat_type == battle_consts.PATROL:
                            name_of_ship = 'Patrol'

                        return_message = 'You sunk the {}!'.format(name_of_ship)
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

    @endpoints.method(GET_GAME_HISTORY_REQUEST,
                      ListOfMoves,
                      name='get_game_history',
                      path='getGameHistory',
                      http_method='GET'
                      )
    def get_game_history(self, request):
        """Get a list of all moves for a game."""
        game_key = battle_utils._getNDBKey(request.websafe_game_key)

        moves = battle_game._getAllMovesForAGame(game_key)

        return ListOfMoves(
            all_moves=[battle_game._copyMoveToList(
                each_move) for each_move in moves]
        )

    @endpoints.method(GET_GAME_STATE,
                      ReturnGameState,
                      name='get_game',
                      path='getGameState',
                      http_method='GET'
                      )
    def get_game(self, request):
        """Returns the current state of the game ie. Username : Hits 3 : Miss 12 : Sunk 0"""

        # Get the game info and the game key.
        selected_game = battle_game._validateAndGetGame(
            request.websafe_game_key)
        game_key = battle_utils._getNDBKey(request.websafe_game_key)

        user_states = []

        # Get game state for user 1.
        user_states.append(battle_game._getGameStateForUser(
            game_key, selected_game, 1))

        # Get game state for user 2.
        user_states.append(battle_game._getGameStateForUser(
            game_key, selected_game, 2))

        # Return the pre-formatted state messages.
        return ReturnGameState(user_states=[StringMessage(message=each_state) for each_state in user_states])

    @endpoints.method(GET_BOAT_LIST,
                      ListOfBoats,
                      name='get_user_boats',
                      path='getUserBoats',
                      http_method='GET'
                      )
    def get_user_boats(self, request):
        """Get a list of a users' boat coordinates for a game."""

        # Get the game key.
        battle_game._validateAndGetGame(request.websafe_game_key)
        game_key = battle_utils._getNDBKey(request.websafe_game_key)

        # Get the user key.
        battle_users._getUserViaWebsafeKey(request.websafe_user_key)
        user_key = battle_utils._getNDBKey(request.websafe_user_key)

        # Grab all the boat coords for this user for the game.
        boat_list = Boat.query(Boat.game_id == game_key,
                               Boat.user_id == user_key).order(Boat.boat_type, Boat.col, Boat.row)

        return ListOfBoats(all_boats=[battle_boat._copyBoatToList(each_boat) for each_boat in boat_list])

    @endpoints.method(GET_USER_SCORE,
                      StringMessage,
                      name='get_user_score',
                      path='getUserScore',
                      http_method='GET'
                      )
    def get_user_score(self, request):
        """Get the number of games that a user has won and lost."""
        user_score = battle_users._getUserScore(request.websafe_user_key)
        return StringMessage(message=battle_users._getUserScoreMessage(user_score))

    @endpoints.method(message_types.VoidMessage,
                      ListOfRankings,
                      name='get_user_rankings',
                      path='getUserRankings',
                      http_method='GET'
                      )
    def get_user_rankings(self, request):
        """Get a list of users ordered by wins/losses."""
        all_rankings = []

        # Get a list of all users.
        all_users = User.query()

        # Iterate through the users.
        for each_user in all_users:
            # Get the users' score.
            single_rank = battle_users._getUserScore(each_user.key.urlsafe())

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
        return ListOfRankings(rankings=[StringMessage(message=battle_users._getUserScoreMessage(each_rank)) for each_rank in all_rankings])


api = endpoints.api_server([BattleshipApi])  # Register API
