"""Fixtures for the SolarBright tests. Serial numbers and addresses are made up."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

HOST = "192.0.2.10"  # documentation range (RFC 5737)
URL = f"http://{HOST}/js/status.js"
SERIAL = "H0000TEST01"


def status_js(power="1234", daily="1567", total="98765", serial=SERIAL) -> str:
    """A status.js like the inverter serves it."""
    fields = [serial, "", "", "SB-TEST", "4200", power, daily, total, "", "1", ""]
    return f'var webData="{",".join(fields)}";\nvar other="x";\n'


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/solarbright in every test."""
    return
