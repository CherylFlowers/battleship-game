"""

Google App Engine HTTP handlers

"""


import webapp2
from battle_utils import send_email_reminder


class SendEmailReminderHandler(webapp2.RequestHandler):

    def post(self):
        """
        Schedule an email to remind a user of games in progress.
        """
        send_email_reminder()
        self.response.set_status(204)  # 204 = no content


app = webapp2.WSGIApplication([
    ('/crons/send_email_reminder', SendEmailReminderHandler)
], debug=True)
