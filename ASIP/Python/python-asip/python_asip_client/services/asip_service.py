__author__ = 'Gianluca Barbon'

# notice that in java this is an interface, but python as no interfaces!
# Superclass for ASIP services.


class AsipService:

    # Public constants for autoevent requests
    AUTOEVENT_REQUEST = 'A'

    def __init__(self):
        pass

    # A service must have an ID.
	# A service should implement setter and getter for ID.
    def get_service_id(self):
        pass

    # id is a char
    def set_service_id(self, id):
        pass

    # A service must specify how to process responses
    # message is a string
    def process_response(self, message):
        pass