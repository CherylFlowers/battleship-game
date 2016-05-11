"""

Google App Engine HTTP handlers

"""


import webapp2
from battle_utils import schedule_email_reminder


class ScheduleEmailReminderHandler(webapp2.RequestHandler):

    def post(self):
        """
        Schedule an email to remind a user of games in progress.
        """
        schedule_email_reminder()
        self.response.set_status(204)  # 204 = no content


app = webapp2.WSGIApplication([
    ('/crons/schedule_email_reminder', ScheduleEmailReminderHandler)
], debug=True)
