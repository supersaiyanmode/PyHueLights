#### This README is a work in progress.

# Highlight [![Build Status](https://travis-ci.org/supersaiyanmode/Highlight.svg?branch=master)](https://travis-ci.org/supersaiyanmode/Highlight)[![Coverage Status](https://coveralls.io/repos/github/supersaiyanmode/Highlight/badge.svg)](https://coveralls.io/github/supersaiyanmode/Highlight)
(Yet another) Philips Hue SDK (Python).


## Sample Code

    from highlight.discovery import DefaultDiscovery
    from highlight.core import *
    from highlight.manager import *
    from highlight.animations import *
    from highlight.registration import *
    
    conn = DefaultDiscovery().discover()
    register(conn, HueApp("test", ""), store)   # Remember to push the button on the hub within
                                                # the last 30 sec of executing this line.
    
    lm = LightsManager(conn)
    lights = lm.get_all_lights()
    lm.run_effect(lights['1'], ColorLoopEffect())
