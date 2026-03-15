from typing import List, Dict, Generator, Tuple, Any, AsyncGenerator, Type
from dataclasses import dataclass
import colorsys

from .model import validate_xy, Light as LightRaw, Group, update_from_object
from .network import BaseResourceManager, dict_parser
from .colorutils import rgb_to_xy, xy_to_rgb


@dataclass(frozen=True)
class LightMetadata:
    type: str
    model_id: str
    software_version: str
    name: str


class Temperature:

    def __init__(self, value: int):
        if not (2000 <= value <= 6500):
            raise ValueError("Temperature must be between 2000 and 6500")
        self.value = value

    def __repr__(self) -> str:
        return f"Temperature({self.value})"


class HueSat:

    def __init__(self, hue: int, saturation: int):
        if not (0 <= hue <= 65535):
            raise ValueError("Hue must be between 0 and 65535")
        if not (0 <= saturation <= 254):
            raise ValueError("Saturation must be between 0 and 254")
        self.hue = hue
        self.saturation = saturation

    def __repr__(self) -> str:
        return f"HueSat(hue={self.hue}, saturation={self.saturation})"


class RGB:

    def __init__(self, r: int, g: int, b: int):
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB components must be between 0 and 255")
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self) -> str:
        return f"RGB({self.r}, {self.g}, {self.b})"


Color = Temperature | HueSat | RGB


@dataclass(frozen=True)
class LightCapabilities:
    control: Any
    streaming: Any
    supported_color_models: List[Type[Color]]


class Light:
    """ High-level abstraction over a Light model. """

    def __init__(self, light_model: LightRaw):
        self._model = light_model

    @property
    def id(self) -> str:
        return self._model.unique_id

    @property
    def metadata(self) -> LightMetadata:
        return LightMetadata(
            type=self._model.type,
            model_id=self._model.model_id,
            software_version=self._model.software_version,
            name=self._model.name
        )

    @property
    def capabilities(self) -> LightCapabilities:
        control = self._model.capabilities.control
        models: List[Type[Color]] = []
        if "colorgamut" in control:
            models.extend([RGB, HueSat])
        if "ct" in control:
            models.append(Temperature)

        return LightCapabilities(
            control=control,
            streaming=self._model.capabilities.streaming,
            supported_color_models=models
        )

    @property
    def color(self) -> Color:
        state = self._model.state
        if state.color_mode == 'xy':
            r, g, b = xy_to_rgb(state.xy[0], state.xy[1], state.brightness
                                or 254)
            return RGB(r, g, b)
        elif state.color_mode == 'ct':
            return Temperature(state.temperature)
        elif state.color_mode == 'hs':
            return HueSat(state.hue, state.saturation)

        raise ValueError(
            f"Unknown or unsupported color mode: {state.color_mode}")

    @color.setter
    def color(self, value: Color) -> None:
        state = self._model.state
        if isinstance(value, Temperature):
            state.temperature = value.value
            state.color_mode = 'ct'
        elif isinstance(value, HueSat):
            state.hue = value.hue
            state.saturation = value.saturation
            state.color_mode = 'hs'
        elif isinstance(value, RGB):
            state.xy = list(rgb_to_xy(value.r, value.g, value.b))
            state.color_mode = 'xy'
        else:
            raise ValueError("Expected Temperature, HueSat, or RGB instance.")

    @property
    def brightness(self) -> int | None:
        return self._model.state.brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._model.state.brightness = value


class LightsManager(BaseResourceManager):

    async def get_all_lights(self) -> Dict[str, Light]:
        """ Retrieves all lights from the bridge, and returns a dict."""
        obj = await self.make_request(relative_url="/lights", method="get")
        raw_lights = self.parse_response(obj, parser=dict_parser(LightRaw))
        return {k: Light(v) for k, v in raw_lights.items()}

    async def get_all_groups(self) -> Dict[str, Group]:
        """ Retrieves all groups on the bridge."""
        obj = await self.make_request(relative_url='/groups', method='get')
        return self.parse_response(obj, parser=dict_parser(Group))

    async def run_effect(self, light: Light | List[Light],
                         effect: Any) -> None:
        """
        Runs the change represented by effect on the given light instance(s).
        """
        lights = [light] if isinstance(light, (Light, LightRaw)) else light

        for l in lights:
            if isinstance(l, LightRaw):
                l = Light(l)

            l._model.reset()
            async for state in effect.update_state(l):
                await self.make_resource_update_request(state)

    async def iter_events(self) -> AsyncGenerator[Light, None]:
        """ Iterates over real-time events from the bridge. """
        async for change in super().iter_events():
            for data in change["data"]:
                light_id = data.get("id_v1")
                if not light_id or not light_id.startswith("/lights"):
                    continue

                raw_light = await self.get_resource(
                    resource_id=light_id.replace("/lights/", ""), typ=LightRaw)
                yield Light(raw_light)
