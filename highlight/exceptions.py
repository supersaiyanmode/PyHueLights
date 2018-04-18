""" This module contains all the exceptions used by Highlight module. """


class HighlightException(Exception):
    """ Highlight-module level exception base class."""

    def __init__(self, msg):
        super(HighlightException, self).__init__(msg)


class DiscoveryFailed(HighlightException):
    """ Unable to discover the Hue Bridge. """
    def __init__(self):
        super(DiscoveryFailed, self).__init__("No Hue bridges found.")


class RequestFailed(HighlightException):
    """
    Raised for all exceptions stemming from failure in requesting info from
    the bridge.
    """
    def __init__(self, status_code, response):
        super(RequestFailed, self).__init__("Request to bridge failed.")
        self.unexpected_status_code = status_code
        self.response = response


class RegistrationFailed(HighlightException):
    """ Raised when registration fails because of any reason."""

    def __init__(self, msg="Registration failed."):
        super(RegistrationFailed, self).__init__(msg)
