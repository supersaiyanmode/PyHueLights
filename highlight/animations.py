import time


def linear_transition(start, end, steps):
    if steps < 1:
        raise ValueError("No of steps need to be at least 1.")

    delta = [float(y - x) / steps for x, y in zip(start, end)]
    cur = list(start)

    for _ in range(steps):
        cur = [x + y for x, y in zip(cur, delta)]
        yield cur

    yield end


def quadratic_transition(start, end, steps, a=1):
    # Shift origin
    shift = start
    start = [x - y for x, y in zip(start, shift)]
    end = [x - y for x, y in zip(end, shift)]

    cur = start
    for _ in range(steps):
        pass


class LightEffect(object):
    def __init__(self, transition_time=3):
        self.transition_time = transition_time

    def update_state(self, light):
        raise NotImplementedError


class ColorLoopEffect(LightEffect):
    def update_state(self, light):
        start_time = time.time()
        light.state.effect = "colorloop"
        yield light.state

        time.sleep(self.transition_time - (time.time() - start_time))

        light.state.effect = "none"
        yield light.state


class SwitchOffEffect(LightEffect):
    def update_state(self, light):
        if self.transition_time:
            light.state.transition_time = self.transition_time

        light.state.on = False
        yield light.state

class SwitchOnEffect(LightEffect):
    def update_state(self, light):
        if self.transition_time:
            light.state.transition_time = self.transition_time

        light.state.on = True
        yield light.state
