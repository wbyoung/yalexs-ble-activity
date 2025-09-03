"""Constants for the Yale Access Bluetooth Activity integration."""

from typing import Final

DOMAIN: Final = "yalexs_ble_activity"
YALEXSBLE_PATCH_URL = (
    "git+https://github.com/wbyoung/yalexs-ble@yalexs-ble-{version}-patches"
)

ATTR_REMOTE_TYPE: Final = "remote_type"
ATTR_SLOT: Final = "slot"
ATTR_SOURCE: Final = "source"
ATTR_TIMESTAMP: Final = "timestamp"

CONF_LOCK_ENTITIES: Final = "lock_entities"

OPERATION_SENSOR_WRITE_DELAY: Final = 2

TRACE: Final = 5
