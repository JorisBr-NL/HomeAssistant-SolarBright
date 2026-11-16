"""Parsing of /js/status.js."""

import pytest

from custom_components.solarbright.api import InvalidResponse, normalize_host, parse_status

from .conftest import SERIAL, status_js


def test_parse_normal_reading():
    reading = parse_status(status_js())
    assert reading.serial == SERIAL
    assert reading.model == "SB-TEST"
    assert reading.rated_power == 4200
    assert reading.current_power == 1234
    assert reading.daily_energy == pytest.approx(15.67)
    assert reading.total_energy == pytest.approx(9876.5)
    assert reading.status == "1"


@pytest.mark.parametrize("total", ["", "0", "abc"])
def test_empty_or_zero_total_is_unknown(total):
    assert parse_status(status_js(total=total)).total_energy is None


def test_empty_power_is_unknown():
    assert parse_status(status_js(power="")).current_power is None


@pytest.mark.parametrize(
    "text",
    ["<html>not an inverter</html>", 'webData="a,b,c"', status_js(serial="")],
)
def test_invalid_responses(text):
    with pytest.raises(InvalidResponse):
        parse_status(text)


@pytest.mark.parametrize(
    ("raw", "host"),
    [
        ("192.0.2.10", "192.0.2.10"),
        ("  http://192.0.2.10/ ", "192.0.2.10"),
        ("https://inverter.local/js/status.js", "inverter.local"),
    ],
)
def test_normalize_host(raw, host):
    assert normalize_host(raw) == host
