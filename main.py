"""

Google App Engine HTTP handlers

"""


import webapp2
from battleship import BattleshipApi


class SendEmailReminderHandler(webapp2.RequestHandler):

    def get(self):
        """
        Send an email to remind a user of games in progress.
        """
        BattleshipApi.send_email_reminder()
        self.response.set_status(204)  # 204 = no content


app = webapp2.WSGIApplication([
    ('/crons/send_email_reminder', SendEmailReminderHandler)
], debug=True)
