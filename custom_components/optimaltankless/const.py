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


def entry_options(entry) -> dict:
    """Return config entry options, treating unset options as empty."""
    return dict(entry.options or {})

ATTR_FLOW_RATE = "flow_rate_gpm"
ATTR_INLET_TEMP = "inlet_temperature"
ATTR_OUTLET_TEMP = "outlet_temperature"
ATTR_POWER_W = "power_w"
ATTR_POWER_KW = "power_kw"
ATTR_HEATER_CAPACITY = "heater_capacity"
ATTR_AVAILABLE_FLOW = "available_flow_rate"
ATTR_INPUT_VOLTAGE = "input_voltage"
ATTR_ERROR_CODE = "error_code"
ATTR_CONFIG_DATA = "config_data"

MIN_TEMP_F = 80
MAX_TEMP_F = 140
MAX_POWER_KW = 12
MAX_POWER_W = MAX_POWER_KW * 1000
DEVICE_MODEL = "Electric Tankless Water Heater"


def clamp_temperature_f(value: float | int | None) -> float | None:
    """Clamp a setpoint to the heater's supported Fahrenheit range."""
    if value is None:
        return None
    return float(max(MIN_TEMP_F, min(MAX_TEMP_F, float(value))))

# configData bit flags are undocumented by Optimal. Bit 0x02 is set during
# normal operation (configData=38 on verified units) and is NOT vacation mode.
# Vacation detection is disabled until the correct bit/value is confirmed.
VACATION_MODE_CONFIG_BIT = 0x02  # reserved — do not use for read/write yet
