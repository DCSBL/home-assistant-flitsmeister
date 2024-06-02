"""Flitsmeister user and statistics sensor implementation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CURRENCY_EURO,
    UnitOfEnergy,
    UnitOfVolume,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HassJob, HomeAssistant
from homeassistant.helpers import event
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import utcnow

from .const import (
    DATA_STATISTICS,
    DATA_USER,
    CONF_COORDINATOR,
    DOMAIN,
)
from .coordinator import FMCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class FMSensorEntityDescription(SensorEntityDescription):
    """Describes Flitsmeister sensor entity."""

    value_fn: Callable[[dict], StateType] = None


SENSOR_TYPES: tuple[FMSensorEntityDescription, ...] = (
    FMSensorEntityDescription(
        key="top_speed",
        name="Top speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[DATA_USER].statistics_top_speed,
    ),
    FMSensorEntityDescription(
        key="km_driven",
        name="Distance driven",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].km_driven,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Flitsmeister sensor entries."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][CONF_COORDINATOR]

    async_add_entities(
        [
            FMSensor(coordinator, description, config_entry)
            for description in SENSOR_TYPES
        ],
        True,
    )


class FMSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Flitsmeister sensor."""

    def __init__(
        self,
        coordinator: FMCoordinator,
        description: FMSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description: FMSensorEntityDescription = description
        self._attr_unique_id = f"{entry.unique_id}.{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}")},
            name=f"Flitsmeister",
            manufacturer="Flitsmeister",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.flitsmeister.nl",
        )

        super().__init__(coordinator)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.native_value is not None
