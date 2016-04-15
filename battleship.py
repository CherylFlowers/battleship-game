"""

Server-side Google App Engine API for Battleship Game; uses Google Cloud Endpoints.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote


# @endpoints.api BattleshipApi ------------------------------------------------

@endpoints.api(name='battleship',
               version='v1',
               description="Battleship Game API"
               )
class BattleshipApi(remote.Service):
    """
    Battleship API v1
    """


api = endpoints.api_server([BattleshipApi])  # Register API
