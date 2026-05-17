"""Constants for GuardSaaS Plates integration."""

DOMAIN = "guardsaas_plates"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_MANDATORY_PLATES = "mandatory_plates"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
CONF_SCAN_INTERVAL = "scan_interval"  # legacy: seconds, used by versions <= 0.1.2
CONF_CACHE_FILE = "cache_file"

DEFAULT_NAME = "GuardSaaS Plates"
DEFAULT_UPDATE_INTERVAL_HOURS = 3.0
DEFAULT_SCAN_INTERVAL = 10800  # legacy fallback in seconds
DEFAULT_MANDATORY_PLATES = ["1947ОР", "3123DC", "7СРТ3892"]
DEFAULT_CACHE_FILE = ".guardsaas_allowed_license_plate_numbers.json"

LOGIN_URL = "https://app.guardsaas.ru/login"
LOGIN_CHECK_URL = "https://app.guardsaas.ru/login_check"
EXPORT_URL = "http://app.guardsaas.ru/employee/list/export"
LOGOUT_URL = "https://app.guardsaas.ru/logout"

USER_AGENT = "Home Assistant GuardSaaS Plates"
TIMEOUT_GET = 15
TIMEOUT_POST = 15
