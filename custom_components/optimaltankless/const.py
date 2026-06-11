"""Constants for the Optimal Tankless integration."""

DOMAIN = "optimaltankless"

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_SERIAL_NUMBER = "serial_number"

# Optimal Hardware Backend (public Swagger: https://hwbe.itsoptimal.com/api)
API_BASE_URL = "https://hwbe.itsoptimal.com"

# Mobile app uses this BFF; HWBE client routes work directly for integrations.
BFF_BASE_URL = "https://bff.itsoptimal.com"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 300

SERVICE_SET_SCAN_INTERVAL = "set_scan_interval"

ATTR_FLOW_RATE = "flow_rate_gpm"
ATTR_INLET_TEMP = "inlet_temperature"
ATTR_OUTLET_TEMP = "outlet_temperature"
ATTR_POWER_KW = "power_kw"
ATTR_HEATER_CAPACITY = "heater_capacity"
ATTR_AVAILABLE_FLOW = "available_flow_rate"
ATTR_INPUT_VOLTAGE = "input_voltage"
ATTR_ERROR_CODE = "error_code"

MIN_TEMP_F = 80
MAX_TEMP_F = 140

# configData bit flag for vacation mode — confirm by toggling in app and
# comparing GET /client/device/{serial}/commands (current unit uses configData=38).
VACATION_MODE_CONFIG_BIT = 0x02
