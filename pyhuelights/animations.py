import time
from typing import Generator, Any

from pyhuelights.core import Color, Light


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
    shift = start
    start = [x - y for x, y in zip(start, shift)]
    end = [x - y for x, y in zip(end, shift)]

    cur = start
    for _ in range(steps):
        pass


class ColorLoopEffect:

    def __init__(self, transition_time: int | None = None):
        self.transition_time = transition_time

    def update_state(self, light: Light) -> Generator[Any, None, None]:
        if self.transition_time is not None:
            light._model.state.transition_time = self.transition_time

        start_time = time.time()
        light._model.state.effect = "colorloop"
        yield light._model.state

        if self.transition_time is not None:
            sleep_time = self.transition_time - (time.time() - start_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        light._model.state.effect = "none"
        yield light._model.state


class SetLightStateEffect:

    def __init__(self,
                 on: bool,
                 color: Color | None = None,
                 brightness: int | None = None,
                 transition_time: int | None = None):
        self.on = on
        self.color = color
        self.brightness = brightness
        self.transition_time = transition_time

    def update_state(self, light: Light) -> Generator[Any, None, None]:
        if self.transition_time is not None:
            light._model.state.transition_time = self.transition_time

        light._model.state.on = self.on
        if self.brightness is not None:
            light.brightness = self.brightness

        if self.color is not None:
            light.color = self.color

        yield light._model.state


class SwitchOnEffect(SetLightStateEffect):

    def __init__(self, **kwargs):
        super().__init__(on=True, **kwargs)


class SwitchOffEffect(SetLightStateEffect):

    def __init__(self, **kwargs):
        super().__init__(on=False, **kwargs)


class RotateEffect:

    def __init__(self, colors: list[Color], transition_time: int):
        self.transition_time = transition_time
        self.effects = [SetLightStateEffect(True, x, 100) for x in colors]

    def update_state(self, light: Light) -> Generator[Any, None, None]:
        len_effects = len(self.effects)
        start_time = time.time()
        iteration = -1
        while time.time() - start_time <= self.transition_time:
            iteration += 1
            effect_index = iteration % len_effects
            yield from self.effects[effect_index].update_state(light)
            time.sleep(0.1)
