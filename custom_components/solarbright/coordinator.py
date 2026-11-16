"""Data update coordinator for a SolarBright inverter."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import InverterReading, SolarBrightError, async_read_inverter
from .const import (
    CONF_MODEL,
    CONF_POLL_INTERVAL,
    CONF_RATED_POWER,
    CONF_SERIAL,
    CONF_SKIP_NIGHT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SKIP_NIGHT,
    DOMAIN,
    OFFLINE_AFTER_FAILURES,
    STATUS_NIGHT,
    STATUS_OFFLINE,
    STATUS_ONLINE,
)
from .guard import CounterGuard

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SolarBrightData:
    """What the sensors show."""

    status: str  # STATUS_ONLINE / STATUS_OFFLINE / STATUS_NIGHT
    current_power: int | None  # W; 0 while offline or at night
    daily_energy: float | None  # kWh; last good value, None if never read
    total_energy: float | None  # kWh; last good value, None if never read
    rated_power: int | None  # W
    inverter_status: str | None  # raw status field of the last good read
    last_seen: datetime | None  # time of the last good read


class SolarBrightCoordinator(DataUpdateCoordinator[SolarBrightData]):
    """Polls one SolarBright inverter."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host: str = entry.data[CONF_HOST]
        self.skip_night: bool = entry.options.get(CONF_SKIP_NIGHT, DEFAULT_SKIP_NIGHT)
        poll_interval = int(entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {self.host}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.reading: InverterReading | None = None  # last good read
        self._failures = 0
        self._last_power: int | None = None
        self._last_seen: datetime | None = None
        self._daily = CounterGuard()
        self._total = CounterGuard()

    @property
    def serial(self) -> str | None:
        return self.reading.serial if self.reading else self.config_entry.data.get(CONF_SERIAL)

    def _is_night(self) -> bool:
        sun = self.hass.states.get("sun.sun")
        return sun is not None and sun.state == "below_horizon"

    async def _async_update_data(self) -> SolarBrightData:
        # Skipping at night needs a known serial: a fresh setup always reads once.
        if self.skip_night and self.serial and self._is_night():
            return self._snapshot(STATUS_NIGHT)

        try:
            reading = await async_read_inverter(async_get_clientsession(self.hass), self.host)
        except SolarBrightError as err:
            return self._handle_failure(err)

        if self._failures >= OFFLINE_AFTER_FAILURES:
            _LOGGER.info("SolarBright %s is back online", self.host)
        self._failures = 0
        self.reading = reading
        self._last_seen = dt_util.utcnow()
        today = dt_util.now().date()
        self._daily.update(reading.daily_energy, today, daily_reset=True)
        self._total.update(reading.total_energy, today)
        if reading.current_power is not None:
            self._last_power = reading.current_power
        return self._snapshot(STATUS_ONLINE)

    def _handle_failure(self, err: SolarBrightError) -> SolarBrightData:
        self._failures += 1
        if self.data is None and not self.serial:
            # Never read and nothing stored: let setup retry (ConfigEntryNotReady).
            raise UpdateFailed(f"Cannot read SolarBright inverter at {self.host}: {err}") from err
        if self.data is not None and self._failures < OFFLINE_AFTER_FAILURES:
            _LOGGER.debug("SolarBright %s: read %d failed: %s", self.host, self._failures, err)
            return self.data  # a short hiccup: keep the last values
        if self._failures == OFFLINE_AFTER_FAILURES:
            _LOGGER.info("SolarBright %s is offline (%s); reporting 0 W", self.host, err)
        return self._snapshot(STATUS_OFFLINE)

    def _snapshot(self, status: str) -> SolarBrightData:
        reading = self.reading
        rated = reading.rated_power if reading else self.config_entry.data.get(CONF_RATED_POWER)
        return SolarBrightData(
            status=status,
            current_power=self._last_power if status == STATUS_ONLINE else 0,
            daily_energy=self._daily.value,
            total_energy=self._total.value,
            rated_power=rated,
            inverter_status=reading.status if reading else None,
            last_seen=self._last_seen,
        )

    def device_details(self) -> dict[str, str | int | None]:
        """Serial, model and rated power as stored in the config entry."""
        reading = self.reading
        data = self.config_entry.data
        return {
            CONF_SERIAL: self.serial,
            CONF_MODEL: (reading.model if reading else None) or data.get(CONF_MODEL),
            CONF_RATED_POWER: (reading.rated_power if reading else None)
            or data.get(CONF_RATED_POWER),
        }
