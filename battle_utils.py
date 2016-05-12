"""

Holds all misc helper methods for the battleship API.

"""


from google.appengine.ext import ndb


def _getNDBKey(websafe_key_to_get):
    """
    Get the entity key from the websafe key passed in.

    Args:
      websafe_key_to_get: the url-safe key of any entity.

    Returns:
      A Datastore entity key.
    """
    return ndb.Key(urlsafe=websafe_key_to_get)
