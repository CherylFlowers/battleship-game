"""

Google App Engine HTTP handlers

"""


import webapp2
from battle_utils import schedule_email_reminder
from battle_utils import send_email_reminder


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write(
            'Hello world! Battleship doesn''t have a front end yet!')


class ScheduleEmailReminderHandler(webapp2.RequestHandler):

    def post(self):
        """
        Schedule an email to remind a user of games in progress.
        """
        schedule_email_reminder()
        self.response.set_status(204)  # 204 = no content


class SendEmailReminderHandler(webapp2.RequestHandler):

    def post(self):
        """
        Send email to remind a user of games in progress.
        """
        send_email_reminder()
        self.response.set_status(204)  # 204 = no content


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/crons/schedule_email_reminder', ScheduleEmailReminderHandler),
    ('/tasks/send_email_reminder', SendEmailReminderHandler),
], debug=True)
