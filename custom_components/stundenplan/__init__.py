from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, FRONTEND_URL_BASE

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)

_FRONTEND_PATH = Path(__file__).parent / "frontend"
_STATIC_PATHS_REGISTERED = "static_paths_registered"


def entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return effective configuration.

    Older test versions stored the complete configuration sometimes in
    entry.data and sometimes in entry.options.  We always merge both so an
    update cannot make an existing schedule disappear.
    """
    data = dict(entry.data or {})
    data.update(dict(entry.options or {}))
    return data


async def _async_register_static_paths(hass: HomeAssistant) -> None:
    """Register frontend assets that are shipped with the integration."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_STATIC_PATHS_REGISTERED):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL_BASE,
                str(_FRONTEND_PATH),
                cache_headers=True,
            )
        ]
    )
    domain_data[_STATIC_PATHS_REGISTERED] = True


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain and register frontend paths early."""
    await _async_register_static_paths(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_static_paths(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry_config(entry)

    async def _reload_entry(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
