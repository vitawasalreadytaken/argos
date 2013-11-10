import os
LOG_FILE = os.path.join(os.path.dirname(__file__), 'argos.log')
STATE_DB = os.path.join(os.path.dirname(__file__), 'state.db')

# How often (in minutes) should cron execute us.
CRON_PERIOD = 10

# Overriden in settings_local.py.
TARGET_CONF_URLS = (
	'http://www.example.com/targets.json',
)

TARGET_CONF_TIMEOUT = 10
HTTP_CHECK_TIMEOUT = 5

HTTP_ALERT_FILTER = lambda result: result.status != 200
MIN_REPORT_INTERVAL = 7200

MANDRILL_ENDPOINT = 'https://mandrillapp.com/api/1.0/messages/send.json'
# Overriden in settings_local.py.
MANDRILL_API_KEY = ''
EMAIL_FROM = 'example@example.com'
EMAIL_TO = (
	'example@example.com',
)

import sh
EMAIL_FROM_NAME = 'argos@{0}'.format(sh.hostname().strip())


from settings_local import *
