"""

Holds all methods relating to boat actions and/or Boat kind.

"""


import endpoints

from google.appengine.ext import ndb

from battle_models import Boat

from battle_messages import SingleBoatForList

from battle_game import _validateAndGetGame

import battle_consts

from random import randint
from operator import itemgetter
from itertools import groupby


def _getBoat(game_id, user_id, move_row, move_col):
    """
    Get the Boat entity.

    Args:
      game_id: the id of the game being played.
      user_id: the id of the user.
      move_row: the row of the Boat.
      move_col: the col of the Boat.

    Returns:
      a Boat entity
    """
    return Boat.query(Boat.game_id == game_id,
                      Boat.user_id == user_id,
                      Boat.row == move_row,
                      Boat.col == move_col).get()


def _boatIsSunk(game_id, user_id, boat_type):
    """
    Determine if a boat is sunk.

    Args:
      game_id: the id of the game being played.
      user_id: the id of the user that's making the move.
      boat_type: the boat type to search for.

    Returns:
      True if the boat is sunk.
      False if the boat is not sunk.
    """
    boat_hits = 0

    if boat_type == battle_consts.CARRIER:
        boat_hits = battle_consts.CARRIER_HITS

    if boat_type == battle_consts.BATTLESHIP:
        boat_hits = battle_consts.BATTLESHIP_HITS

    if boat_type == battle_consts.SUBMARINE:
        boat_hits = battle_consts.SUBMARINE_HITS

    if boat_type == battle_consts.DESTROYER:
        boat_hits = battle_consts.DESTROYER_HITS

    if boat_type == battle_consts.PATROL:
        boat_hits = battle_consts.PATROL_HITS

    if Boat.query(Boat.game_id == game_id,
                  Boat.user_id == user_id,
                  Boat.boat_type == boat_type,
                  Boat.hit == True).count() == boat_hits:
        return True
    return False


def _copyBoatToList(boat_to_copy):
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
            if field.name == "boat_type":
                boat_name = ''

                if boat_to_copy.boat_type == battle_consts.CARRIER:
                    boat_name = 'Carrier'

                if boat_to_copy.boat_type == battle_consts.BATTLESHIP:
                    boat_name = 'Battleship'

                if boat_to_copy.boat_type == battle_consts.SUBMARINE:
                    boat_name = 'Submarine'

                if boat_to_copy.boat_type == battle_consts.DESTROYER:
                    boat_name = 'Destroyer'

                if boat_to_copy.boat_type == battle_consts.PATROL:
                    boat_name = 'Patrol'

                setattr(selected_boat, field.name, boat_name)

            else:
                setattr(selected_boat, field.name,
                        getattr(boat_to_copy, field.name))

    # Verify all values in the boat message have been assigned a value.
    selected_boat.check_initialized()

    # Return the updated boat message.
    return selected_boat


def _buildBoard():
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


def _addBoat(game_key, user_key, master_coord, boat_type, boat_hits):
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

            boat_row -= 1

            new_boat = Boat(
                game_id=game_key,
                user_id=user_key,
                boat_type=boat_type,
                hit=False,
                row=battle_consts.BOARD_ROWS[boat_row],
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


def _generateBoardAndBoats(game_key, user_key):
    """
    Generate a board and all boats for a user.

    Args:
      game_key: the game that the user is playing.
      user_key: the user that's playing.
    """

    # Get a list of all available co-ords on the board.
    master_coord = _buildBoard()

    # Create all boats for the user.
    _addBoat(game_key,
             user_key,
             master_coord,
             battle_consts.CARRIER,
             battle_consts.CARRIER_HITS)

    _addBoat(game_key,
             user_key,
             master_coord,
             battle_consts.BATTLESHIP,
             battle_consts.BATTLESHIP_HITS)

    _addBoat(game_key,
             user_key,
             master_coord,
             battle_consts.SUBMARINE,
             battle_consts.SUBMARINE_HITS)

    _addBoat(game_key,
             user_key,
             master_coord,
             battle_consts.DESTROYER,
             battle_consts.DESTROYER_HITS)

    _addBoat(game_key,
             user_key,
             master_coord,
             battle_consts.PATROL,
             battle_consts.PATROL_HITS)
