"""
edge/bus_simulator.py
---------------------
Provides vehicle identification and telemetry for simulated buses.
Does NOT handle GPS location (see gps_simulator.py).
"""
from __future__ import annotations

import dataclasses
import random
from typing import Dict, Optional


@dataclasses.dataclass
class BusConfig:
    bus_id: str
    route_id: str
    video_source: Optional[str]   # path to demo video file
    status: str = "Active"        # Active | Idle | Maintenance
    speed_kmh_range: tuple = (25, 40)

    def sample_speed(self) -> float:
        lo, hi = self.speed_kmh_range
        return round(random.uniform(lo, hi), 1)


# ---------------------------------------------------------------------------
# Fleet registry – 3 simulated buses as required by the spec
# ---------------------------------------------------------------------------
FLEET: Dict[str, BusConfig] = {
    "BUS-01": BusConfig(
        bus_id="BUS-01",
        route_id="ROUTE-RED",
        video_source=None,        # overridden by --video CLI arg
        status="Active",
        speed_kmh_range=(28, 42),
    ),
    "BUS-02": BusConfig(
        bus_id="BUS-02",
        route_id="ROUTE-BLUE",
        video_source=None,
        status="Active",
        speed_kmh_range=(20, 35),
    ),
    "BUS-03": BusConfig(
        bus_id="BUS-03",
        route_id="ROUTE-GREEN",
        video_source=None,
        status="Active",
        speed_kmh_range=(30, 45),
    ),
}


class BusSimulator:
    """
    Maintains runtime state for a single simulated bus.
    Instantiate one BusSimulator per runner process.
    """

    def __init__(self, bus_id: str = "BUS-01", video_source: Optional[str] = None):
        if bus_id not in FLEET:
            raise ValueError(f"Unknown bus_id '{bus_id}'. Known buses: {list(FLEET.keys())}")
        self.config = dataclasses.replace(FLEET[bus_id])
        if video_source:
            self.config.video_source = video_source

    @property
    def bus_id(self) -> str:
        return self.config.bus_id

    @property
    def route_id(self) -> str:
        return self.config.route_id

    @property
    def status(self) -> str:
        return self.config.status

    def current_speed(self) -> float:
        return self.config.sample_speed()
