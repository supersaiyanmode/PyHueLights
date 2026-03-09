# PyHueLights

(Yet another) Philips Hue SDK for Python 3.10+.

## Features

- Full Async Support**:
- High-level Abstractions: Simple `Light` and `Color` models (`RGB`, `Temperature`, `HueSat`).
- SSE Event Streaming: Real-time updates from your Bridge.
- *obust Discovery: Supports mDNS, NUPNP discoveries.

## Installation

```bash
pip install git+https://github.com/supersaiyanmode/pyhuelights.git@master
```

## Quick Start

```python
import asyncio
from pyhuelights import DefaultDiscovery, LightsManager
from pyhuelights.core import RGB, Temperature
from pyhuelights.model import HueApp
from pyhuelights.registration import register
from pyhuelights.animations import SetLightStateEffect

async def main():
    # 1. Discover the bridge
    conn = await DefaultDiscovery().discover()

    # 2. Register (Press the link button on the bridge first!)
    store = {}  # Or a dict-like object.
    auth_conn = await register(conn, HueApp("my_app", "my_device"), store)

    # 3. Manage Lights
    manager = LightsManager(auth_conn)
    lights = await manager.get_all_lights()

    my_light = lights['1']

    await manager.run_effect(my_light,
                             SetLightStateEffect(on=True, color=RGB(255, 0, 0))

if __name__ == "__main__":
    asyncio.run(main())
```

## SSE Events

Listen to real-time events from the bridge:

```python
async for light in manager.iter_events():
    print(f"Light {light._model.id} changed! New color: {light.color}")
```

## License

MIT
