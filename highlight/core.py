""" Contains Bridge, Light classes."""


class Bridge(object):
    """ Represents a Philips Hue bridge."""

    def __init__(self, host):
        self.host = host
