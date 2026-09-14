"""
edge/bus_simulator.py
---------------------
Provides vehicle identification and telemetry for simulated buses.
Does NOT handle GPS location (see gps_simulator.py).
"""
from __future__ import annotations

import dataclasses
import random
import time
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
            
        self._current_speed = self.config.sample_speed()
        self._speed_history = []
        self._large_speed_changes = 0

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
        return self._current_speed
        
    def tick(self, dt: float = 1.0/30.0) -> float:
        # Introduce occasional erratic behavior for testing
        if random.random() < 0.005:
            accel = random.uniform(-25.0, 25.0) # km/h per second (harsh)
        else:
            accel = random.uniform(-2.0, 2.0) # normal
            
        self._current_speed += accel * dt
        self._current_speed = max(0, min(self._current_speed, 100))
        
        decel_g = 0.0
        if accel < 0:
            # 1 km/h/s = ~0.277 m/s^2. 1g = 9.8 m/s^2
            decel_m_s2 = abs(accel) * 0.2777
            decel_g = decel_m_s2 / 9.8
            
        if abs(accel) > 15.0:
            self._large_speed_changes += 1
            
        self._speed_history.append((self._current_speed, decel_g))
        if len(self._speed_history) > 150:
            self._speed_history.pop(0)
            
        # Slowly decay the counter of large speed changes
        if random.random() < 0.05:
            self._large_speed_changes = max(0, self._large_speed_changes - 1)
            
        return self._current_speed

    def check_rash_driving(self) -> bool:
        if not self._speed_history:
            return False
            
        current_speed, current_decel = self._speed_history[-1]
        
        if current_speed > 80.0:
            return True
            
        if current_decel > 0.4:
            return True
            
        if self._large_speed_changes >= 3:
            self._large_speed_changes = 0
            return True
            
        return False
