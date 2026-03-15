import time
import asyncio
from typing import Any, AsyncGenerator

from pyhuelights.core import Color, Light, RGB, Temperature, HueSat
from pyhuelights.colorutils import rgb_to_xy


async def linear_transition(start, end, steps) -> AsyncGenerator[Any, None]:
    if steps < 1:
        raise ValueError("No of steps need to be at least 1.")

    delta = [float(y - x) / steps for x, y in zip(start, end)]
    cur = list(start)

    for _ in range(steps):
        cur = [x + y for x, y in zip(cur, delta)]
        yield cur

    yield end


class ColorLoopEffect:

    def __init__(self, transition_time: int | None = None):
        self.transition_time = transition_time

    async def update_state(self, light: Light) -> AsyncGenerator[Any, None]:
        if self.transition_time is not None:
            light._model.state.transition_time = self.transition_time

        start_time = time.time()
        light._model.state.effect = "colorloop"
        yield light._model.state

        if self.transition_time is not None:
            sleep_time = self.transition_time - (time.time() - start_time)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

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

    async def update_state(self, light: Light) -> AsyncGenerator[Any, None]:
        state = light._model.state
        if self.transition_time is not None:
            state.transition_time = self.transition_time

        state.on = self.on
        if self.brightness is not None:
            light.brightness = self.brightness

        if self.color is not None:
            if isinstance(self.color, Temperature):
                state.temperature = self.color.value
                state.color_mode = 'ct'
            elif isinstance(self.color, HueSat):
                state.hue = self.color.hue
                state.saturation = self.color.saturation
                state.color_mode = 'hs'
            elif isinstance(self.color, RGB):
                state.xy = list(
                    rgb_to_xy(self.color.r, self.color.g, self.color.b))
                state.color_mode = 'xy'

        yield state


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

    async def update_state(self, light: Light) -> AsyncGenerator[Any, None]:
        len_effects = len(self.effects)
        start_time = time.time()
        iteration = -1
        while time.time() - start_time <= self.transition_time:
            iteration += 1
            effect_index = iteration % len_effects
            async for state in self.effects[effect_index].update_state(light):
                yield state
            await asyncio.sleep(0.1)
