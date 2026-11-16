"""Sensors of a SolarBright inverter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONF_HOST, EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SolarBrightConfigEntry
from .const import CONF_MODEL, CONF_SERIAL, DOMAIN, STATUSES
from .coordinator import SolarBrightCoordinator, SolarBrightData


@dataclass(frozen=True, kw_only=True)
class SolarBrightSensorDescription(SensorEntityDescription):
    """Describes a SolarBright sensor."""

    value_fn: Callable[[SolarBrightData], Any]
    keep_last: bool = False  # energy counters: keep (and restore) the last known value


# The keys are part of the unique IDs; keep them stable so entity IDs do not change.
SENSORS: tuple[SolarBrightSensorDescription, ...] = (
    SolarBrightSensorDescription(
        key="current_power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.current_power,
    ),
    SolarBrightSensorDescription(
        key="daily_energy",
        translation_key="daily_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda d: d.daily_energy,
        keep_last=True,
    ),
    SolarBrightSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=lambda d: d.total_energy,
        keep_last=True,
    ),
    SolarBrightSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=STATUSES,
        value_fn=lambda d: d.status,
    ),
    SolarBrightSensorDescription(
        key="rated_power",
        translation_key="rated_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.rated_power,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBrightConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of one inverter."""
    coordinator = entry.runtime_data
    async_add_entities(
        (SolarBrightEnergySensor if d.keep_last else SolarBrightSensor)(coordinator, d)
        for d in SENSORS
    )


class SolarBrightSensor(CoordinatorEntity[SolarBrightCoordinator], SensorEntity):
    """A sensor fed by the coordinator."""

    _attr_has_entity_name = True
    entity_description: SolarBrightSensorDescription

    def __init__(
        self, coordinator: SolarBrightCoordinator, description: SolarBrightSensorDescription
    ) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        serial = entry.data.get(CONF_SERIAL)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="SolarBright",
            model=entry.data.get(CONF_MODEL),
            name=f"SolarBright {serial}" if serial else "SolarBright inverter",
            serial_number=serial,
            configuration_url=f"http://{entry.data[CONF_HOST]}/",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        return None if data is None else self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if self.entity_description.key != "status" or data is None:
            return None
        return {
            "inverter_status_code": data.inverter_status,
            "last_seen": data.last_seen.isoformat() if data.last_seen else None,
        }


class SolarBrightEnergySensor(SolarBrightSensor, RestoreSensor):
    """Energy counter: keeps its last value while the inverter sleeps and across restarts."""

    _last: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (restored := await self.async_get_last_sensor_data()) is not None:
            self._last = restored.native_value
        self._update_last()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_last()
        super()._handle_coordinator_update()

    def _update_last(self) -> None:
        data = self.coordinator.data
        value = None if data is None else self.entity_description.value_fn(data)
        if value is not None:
            self._last = value

    @property
    def native_value(self) -> Any:
        return self._last
