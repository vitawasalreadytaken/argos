# Overriden in settings_local.py.
TARGET_CONF_URLS = (
	'http://www.example.com/targets.json',
)

TARGET_CONF_TIMEOUT = 10
HTTP_CHECK_TIMEOUT = 5

from settings_local import *
