"""Constants for Visual Climate Scheduler."""

DOMAIN = "visual_climate_scheduler"
INTEGRATION_TITLE = "Visual Climate Scheduler"
ATTR_ZONE_ID = "zone_id"
ATTR_ROOM_ID = "room_id"
ATTR_TEMPERATURE = "temperature"

CONF_AREA_ID = "area_id"
CONF_ADD_ANOTHER = "add_another"
CONF_CLIMATE_ENTITY_IDS = "climate_entity_ids"
CONF_ROOM_ID = "room_id"
CONF_ROOM_NAME = "room_name"
CONF_SHOW_PANEL = "show_panel"

PANEL_COMPONENT = "visual-climate-scheduler-panel"
PANEL_URL_PATH = DOMAIN
PANEL_STATIC_URL = f"/{DOMAIN}_static"
# Changes whenever the bundled panel JavaScript changes, so a browser never
# reuses an older editor after an integration update.
PANEL_ASSET_VERSION = "1.0.0"

STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN
