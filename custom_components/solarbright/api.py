"""Local API of SolarBright inverters: read and parse ``/js/status.js``.

The inverter serves a small JavaScript file with a line like::

    webData="<serial>,,,<model>,<rated W>,<power W>,<daily 0.01 kWh>,<total 0.1 kWh>,,<status>,..."

This module has no Home Assistant imports, so it can be tested on its own.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

import aiohttp

STATUS_PATH = "/js/status.js"
REQUEST_TIMEOUT = 10  # seconds

_WEB_DATA = re.compile(r'webData\s*=\s*"([^"]*)"')
_MIN_FIELDS = 8


class SolarBrightError(Exception):
    """Base error for the SolarBright API."""


class CannotConnect(SolarBrightError):
    """The inverter did not answer (offline, wrong address, HTTP error)."""


class InvalidResponse(SolarBrightError):
    """The inverter answered, but not with the expected data."""


@dataclass(frozen=True)
class InverterReading:
    """One reading of the inverter. ``None`` means the field was empty or invalid."""

    serial: str
    model: str | None
    rated_power: int | None  # W
    current_power: int | None  # W
    daily_energy: float | None  # kWh, resets each day
    total_energy: float | None  # kWh, lifetime
    status: str | None  # raw status field of the inverter


def normalize_host(host: str) -> str:
    """Accept '192.168.1.50', 'http://192.168.1.50/' and the like; return the bare host."""
    host = host.strip()
    host = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", host)
    return host.split("/", 1)[0]


def _field(fields: list[str], index: int) -> str | None:
    if index >= len(fields):
        return None
    value = fields[index].strip()
    return value or None


def _int(fields: list[str], index: int) -> int | None:
    value = _field(fields, index)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_status(text: str) -> InverterReading:
    """Parse the content of ``/js/status.js``."""
    match = _WEB_DATA.search(text)
    if not match:
        raise InvalidResponse("webData not found")
    fields = match.group(1).split(",")
    if len(fields) < _MIN_FIELDS:
        raise InvalidResponse(f"webData has {len(fields)} fields, expected at least {_MIN_FIELDS}")

    serial = _field(fields, 0)
    if serial is None:
        raise InvalidResponse("webData has no serial number")

    daily = _int(fields, 6)
    total = _int(fields, 7)
    return InverterReading(
        serial=serial,
        model=_field(fields, 3),
        rated_power=_int(fields, 4),
        current_power=_int(fields, 5),
        daily_energy=None if daily is None else daily / 100,
        # A lifetime total of 0 is a glitch of the inverter (it happens while it starts up).
        total_energy=None if not total or total < 0 else total / 10,
        status=_field(fields, 9),
    )


async def async_read_inverter(session: aiohttp.ClientSession, host: str) -> InverterReading:
    """Read the inverter at ``host``."""
    url = f"http://{host}{STATUS_PATH}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as resp:
            if resp.status != 200:
                raise CannotConnect(f"HTTP {resp.status}")
            raw = await resp.read()
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise CannotConnect(str(err) or type(err).__name__) from err
    return parse_status(raw.decode("utf-8", errors="replace"))
