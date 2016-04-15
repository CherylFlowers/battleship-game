"""

Google App Engine HTTP handlers

"""


import webapp2


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write(
            'Hello world! Battleship doesn''t have a front end yet!')


app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
