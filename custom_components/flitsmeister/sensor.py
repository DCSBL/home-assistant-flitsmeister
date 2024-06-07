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
        key="km_driven",
        name="Distance driven",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].km_driven,
        device_class=SensorDeviceClass.DISTANCE,
    ),
    FMSensorEntityDescription(
        key="fines_avoided",
        name="Fines avoided",
        native_unit_of_measurement="fines",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].fines_avoided,
        icon="mdi:cash-check",
    ),
    FMSensorEntityDescription(
        key="sec_driven",
        name="Time driven",
        native_unit_of_measurement="s",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].sec_driven,
        device_class=SensorDeviceClass.DURATION,
    ),
    FMSensorEntityDescription(
        key="times_in_traffic",
        name="Times in traffic",
        native_unit_of_measurement="times",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].times_in_traffic,
        icon="mdi:car-multiple",
    ),
    FMSensorEntityDescription(
        key="top_100_sprint_ms",
        name="Top 100 sprint",
        native_unit_of_measurement="ms",
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[DATA_STATISTICS].top_100_sprint_ms,
        icon="mdi:flag-checkered",
        device_class=SensorDeviceClass.DURATION,
    ),    
    FMSensorEntityDescription(
        key="top_consecutive_days",
        name="Top consecutive days",
        native_unit_of_measurement="days",
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[DATA_STATISTICS].top_consecutive_days,
        icon="mdi:calendar",
    ),
    FMSensorEntityDescription(
        key="top_speed",
        name="Top speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[DATA_STATISTICS].top_speed,
        device_class=SensorDeviceClass.SPEED,
    ),
    FMSensorEntityDescription(
        key="total_ratings",
        name="Total ratings",
        native_unit_of_measurement="ratings",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data[DATA_STATISTICS].total_ratings,
        icon="mdi:star",
    ),
    FMSensorEntityDescription
    (
        key="countries_visited",
        name="Countries visited",
        native_unit_of_measurement="countries",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: len(data[DATA_STATISTICS].countries_visited),
        icon="mdi:earth",
    ),
    FMSensorEntityDescription(
        key="provinces_visited",
        name="Provinces visited",
        native_unit_of_measurement="provinces",
        suggested_display_precision=0,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: len(data[DATA_STATISTICS].provinces_visited),
        icon="mdi:map-marker-circle",
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
