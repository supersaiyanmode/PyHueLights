""" This module contains all the exceptions used by Highlight module. """


class HighlightException(Exception):
    """ Highlight-module level exception base class."""

    def __init__(self, msg):
        super(HighlightException, self).__init__(msg)


class DiscoveryFailed(HighlightException):
    """ Unable to discover the Hue Bridge. """
    def __init__(self):
        super(DiscoveryFailed, self).__init__("No Hue bridges found.")
