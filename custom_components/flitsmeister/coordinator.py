"""Coordinator implementation for Flitsmeister integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from flitsmeister import FM

from .const import DOMAIN, DATA_USER, DATA_STATISTICS

LOGGER = logging.getLogger(__name__)



class FMCoordinator(DataUpdateCoordinator):
    """Get the latest data and update the states."""

    api: FM

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: FM,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.api = api

        super().__init__(
            hass,
            LOGGER,
            name="Flitsmeister coordinator",
            update_interval=timedelta(minutes=60),
        )

    async def _async_update_data(self):
        """Get the latest data from Flitsmeister."""
        LOGGER.debug("Fetching Flitsmeister data.")

        user = await self.api.user()
        statistics = await self.api.statistics()

        return {
            DATA_USER: user,
            DATA_STATISTICS: statistics,
        }
