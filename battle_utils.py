"""

Holds all misc helper methods for the battleship API.

"""


from google.appengine.ext import ndb
from google.appengine.api import app_identity
from google.appengine.api import mail

from battle_users import _getUsersWithEmails
from battle_game import _getListOfGamesForUser
from battle_game import _getGameLastMove


def _getNDBKey(websafe_key_to_get):
    """
    Get the entity key from the websafe key passed in.

    Args:
      websafe_key_to_get: the url-safe key of any entity.

    Returns:
      A Datastore entity key.
    """
    return ndb.Key(urlsafe=websafe_key_to_get)


def schedule_email_reminder():
    """
    Schedule email to remind a user of games in progress.
    """

    # Get a list of users with emails.
    user_list = _getUsersWithEmails()

    # If no users have emails, exit the method.
    if not user_list:
        return

    for each_user in user_list:

        # Narrow down the list to users that are involved in an active game.
        game_list = _getListOfGamesForUser(each_user.key)

        # If this user is not involved in an active game, skip to the next user.
        if not game_list:
            continue

        for each_game in game_list:

            # Determine if the user made the last move.
            last_move = _getGameLastMove(each_game.key)

            # If the user made the last move there's no need
            # to notify them via email, skip to the next game.
            if last_move.user_id == each_user.key:
                continue

            # If the user did not make the last move add
            # an email notification to the task queue.

            # Get the name of the opponent.
            opponent = _getUserViaWebsafeKey(last_move.key.urlsafe())

            # Add the email to the task queue.
            taskqueue.add(params={'email': each_user.email,
                                  'opponent': opponent.user_name},
                          url='/tasks/send_email_reminder'
                          )


def send_email_reminder(request):
    """
    Send email to remind a user of games in progress.
    """
    mail.send_mail(
        'noreply@%s.appspotmail.com' % (
            app_identity.get_application_id()),          # from
        request.get('email'),                            # to
        'Battleship Game is waiting for your move ...',  # subject
        'Hey there! {} is waiting for you to make a move!' % request.get(
            'opponent')
    )
