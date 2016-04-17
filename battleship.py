"""

Server-side Google App Engine API for Battleship Game; uses Google Cloud Endpoints.

"""


import endpoints

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from battle_containers import USER_POST_REQUEST

from battle_messages import StringMessage

from battle_models import User


# @endpoints.api BattleshipApi ------------------------------------------------

@endpoints.api(name='battleship',
               version='v1',
               description="Battleship Game API"
               )
class BattleshipApi(remote.Service):
    """
    Battleship API v1
    """

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
        if request.username is None:
            raise endpoints.BadRequestException('Username cannot be blank.')

        if User.query(User.user_name == request.username).get():
            raise endpoints.ConflictException('That user already exists.')

        new_user = User(user_name=request.username)
        new_user.put()

        return StringMessage(message='{} was successfully created!'.format(request.username))


api = endpoints.api_server([BattleshipApi])  # Register API
