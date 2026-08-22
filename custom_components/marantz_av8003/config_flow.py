"""Config flow for the Marantz AV8003 integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
    }
)


async def _async_test_connection(host: str, port: int) -> bool:
    """Try to open a TCP connection and get a power-status response."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=5
        )
    except (OSError, asyncio.TimeoutError) as err:
        raise CannotConnect from err

    try:
        writer.write(b"PW?\r")
        await writer.drain()
        try:
            data = await asyncio.wait_for(reader.read(64), timeout=3)
        except asyncio.TimeoutError as err:
            raise CannotConnect from err
        if not data:
            raise CannotConnect
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass

    return True


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the gateway."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marantz AV8003."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            try:
                await _async_test_connection(
                    user_input[CONF_HOST], user_input[CONF_PORT]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
