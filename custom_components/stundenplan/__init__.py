from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, HomeAssistant

from .const import CARD_URL, CARD_URL_VERSIONED, DOMAIN, FRONTEND_URL_BASE

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)

_FRONTEND_PATH = Path(__file__).parent / "frontend"
_STATIC_PATHS_REGISTERED = "static_paths_registered"
_RESOURCE_NOTIFICATION_ID = f"{DOMAIN}_resource_setup"
_LOGGER = logging.getLogger(__name__)


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


def _normalize_resource_url(url: str | None) -> str:
    """Return a normalized resource URL without query parameters."""
    return str(url or "").split("?", maxsplit=1)[0].rstrip("/")


def _resource_matches(url: str | None) -> bool:
    """Return whether a resource points to this integration card."""
    return _normalize_resource_url(url) == CARD_URL.rstrip("/")


async def _async_resource_notification(hass: HomeAssistant, details: str) -> None:
    """Show a persistent notification with resource setup instructions."""
    message = (
        "Die Lovelace-Resource fuer die Stundenplan-Karte ist nicht registriert.\n\n"
        "Bitte unter **Einstellungen -> Dashboards -> Ressourcen** den Eintrag anlegen:\n\n"
        f"- URL: `{CARD_URL}`\n"
        "- Typ: `module`\n\n"
        f"Hinweis: {details}"
    )
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "Stundenplan: Lovelace-Ressource fehlt",
            "message": message,
            "notification_id": _RESOURCE_NOTIFICATION_ID,
        },
        blocking=True,
    )


async def _async_dismiss_resource_notification(hass: HomeAssistant) -> None:
    """Dismiss the resource setup notification if it exists."""
    await hass.services.async_call(
        "persistent_notification",
        "dismiss",
        {"notification_id": _RESOURCE_NOTIFICATION_ID},
        blocking=True,
    )


async def _async_get_lovelace_resources(hass: HomeAssistant):
    """Return a Lovelace resources collection and its mode."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return None, None

    resources = getattr(lovelace, "resources", None)
    mode = getattr(lovelace, "mode", getattr(lovelace, "resource_mode", None))
    if resources is not None:
        return resources, mode

    dashboards = getattr(lovelace, "dashboards", None)
    if isinstance(dashboards, dict):
        for dashboard in dashboards.values():
            resources = getattr(dashboard, "resources", None)
            if resources is None:
                continue
            mode = getattr(
                dashboard,
                "mode",
                getattr(dashboard, "resource_mode", mode),
            )
            return resources, mode

    return None, mode


async def _async_list_resources(resources: Any) -> list[dict[str, Any]]:
    """Return currently registered Lovelace resources."""
    items_method = getattr(resources, "async_items", None) or getattr(
        resources, "items", None
    )
    if not callable(items_method):
        return []

    items = items_method()
    if inspect.isawaitable(items):
        items = await items
    return list(items or [])


async def _async_ensure_lovelace_resource(hass: HomeAssistant) -> None:
    """Ensure the card resource is available in Lovelace (storage mode)."""
    resources, mode = await _async_get_lovelace_resources(hass)
    if resources is None:
        await _async_resource_notification(
            hass, "Lovelace-Ressourcen konnten noch nicht geladen werden."
        )
        return

    if mode != "storage":
        await _async_resource_notification(
            hass,
            "Lovelace ist nicht im Storage-Mode. In YAML-Mode ist der Eintrag manuell noetig.",
        )
        return

    existing_resources = await _async_list_resources(resources)
    matching = next(
        (item for item in existing_resources if _resource_matches(item.get("url"))),
        None,
    )
    if matching is not None:
        current_url = str(matching.get("url") or "")
        if current_url != CARD_URL_VERSIONED:
            update_item = getattr(resources, "async_update_item", None)
            if callable(update_item):
                try:
                    await update_item(
                        matching["id"],
                        {"res_type": "module", "url": CARD_URL_VERSIONED},
                    )
                    _LOGGER.info(
                        "Updated Lovelace resource for Stundenplan card to %s",
                        CARD_URL_VERSIONED,
                    )
                except Exception as err:  # pragma: no cover - defensive runtime guard
                    _LOGGER.warning(
                        "Could not update Lovelace resource version automatically: %s",
                        err,
                    )
        await _async_dismiss_resource_notification(hass)
        return

    create_item = getattr(resources, "async_create_item", None)
    if not callable(create_item):
        await _async_resource_notification(
            hass,
            "Automatische Registrierung ist in dieser Lovelace-Konfiguration nicht verfuegbar.",
        )
        return

    try:
        await create_item({"res_type": "module", "url": CARD_URL_VERSIONED})
        _LOGGER.info(
            "Registered Lovelace resource for Stundenplan card: %s",
            CARD_URL_VERSIONED,
        )
        await _async_dismiss_resource_notification(hass)
    except Exception as err:  # pragma: no cover - defensive runtime guard
        _LOGGER.warning("Could not register Lovelace resource automatically: %s", err)
        await _async_resource_notification(
            hass,
            "Automatische Registrierung ist fehlgeschlagen. Bitte den Eintrag manuell anlegen.",
        )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain and register frontend paths early."""
    await _async_register_static_paths(hass)

    async def _register_lovelace_resource(_event: Any) -> None:
        await _async_ensure_lovelace_resource(hass)

    if hass.state == CoreState.running:
        await _register_lovelace_resource(None)
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            _register_lovelace_resource,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_static_paths(hass)
    await _async_ensure_lovelace_resource(hass)
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
