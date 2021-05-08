import time

from pyhuelights.core import Color


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
    def __init__(self, transition_time=None):
        self.transition_time = transition_time

    def update_state(self, light):
        if self.transition_time is not None:
            light.state.transition_time = self.transition_time


class ColorLoopEffect(LightEffect):
    def update_state(self, light):
        start_time = time.time()
        light.state.effect = "colorloop"
        yield light.state

        sleep_time = self.transition_time - (time.time() - start_time)
        if sleep_time > 0:
            time.sleep(sleep_time)

        light.state.effect = "none"
        yield light.state


class SetLightStateEffect(LightEffect):
    def __init__(self, on, color=None, brightness=None, transition_time=None):
        if color and not isinstance(color, Color):
            raise ValueError("Expected a Color instance.")

        super().__init__(transition_time)
        self.on = on
        self.color = color
        self.brightness = brightness

    def update_state(self, light):
        super().update_state(light)
        light.state.on = self.on
        if self.brightness is not None:
            light.state.brightness = self.brightness

        if self.color is not None:
            light.state.set_color(self.color)

        yield light.state


class SwitchOnEffect(SetLightStateEffect):
    def __init__(self, **kwargs):
        super().__init__(on=True, brightness=254, **kwargs)


class SwitchOffEffect(SetLightStateEffect):
    def __init__(self, **kwargs):
        super().__init__(on=False, **kwargs)


class RotateEffect(LightEffect):
    def __init__(self, colors, transition_time):
        super().__init__(transition_time)
        self.effects = [SetLightStateEffect(True, x, 100) for x in colors]

    def update_state(self, lights):
        if self.transition_time is None:
            raise Exception("Transition time is required.")

        len_effects = len(self.effects)
        start_time = time.time()
        iteration = -1
        while time.time() - start_time <= self.transition_time:
            iteration += 1
            for index, light in enumerate(lights):
                effect_index = (index + iteration) % len_effects
                yield from self.effects[effect_index].update_state(light)
            time.sleep(0.1)
