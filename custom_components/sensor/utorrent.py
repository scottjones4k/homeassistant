"""
Support for monitoring the uTorrent BitTorrent client API.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.transmission/
"""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_NAME, CONF_PORT,
    CONF_MONITORED_VARIABLES, STATE_UNKNOWN, STATE_IDLE)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)
_THROTTLED_REFRESH = None

DEFAULT_NAME = 'uTorrent'
DEFAULT_PORT = None

SENSOR_TYPES = {
    'current_status': ['Status', None],
    'download_speed': ['Down Speed', 'MB/s'],
    'upload_speed': ['Up Speed', 'MB/s']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_MONITORED_VARIABLES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_USERNAME): cv.string,
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the uTorrent sensors."""

    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    address = config.get(CONF_HOST)
    if (port is not None):
        address += ':' + str(port)
    baseUri = 'http://'+address+'/gui/'
    auth = (config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
    dev = []
    for variable in config[CONF_MONITORED_VARIABLES]:
        dev.append(uTorrentSensor(variable, name, baseUri, auth))

    add_devices(dev)


class uTorrentSensor(Entity):
    """Representation of a uTorrent sensor."""

    def __init__(self, sensor_type,  client_name, baseUri, auth):
        """Initialize the sensor."""
        self._name = SENSOR_TYPES[sensor_type][0]
        self.baseUri = baseUri
        self.auth = auth
        self.type = sensor_type
        self.client_name = client_name
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self.encoding = "utf-8"
        _LOGGER.error("init" + self._name)

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self.client_name, self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    # pylint: disable=no-self-use
    def refresh_utorrent_data(self):
        """Call the throttled uTorrent refresh method."""
        _LOGGER.error("refreshing " + self._name)
        res = requests.get(self.baseUri + 'token.html', auth=self.auth)
        token = res.content[44:108].decode(encoding)
        res2 = requests.get(self.baseUri + '?list=1&token='+token, auth=self.auth, cookies=res.cookies)
        js = json.loads(res2.content.decode(encoding))
        self.torrents = js['torrents']
        _LOGGER.error("refreshed " + self._name)

    def update(self):
        """Get the latest data from uTorrent and updates the state."""
        self.refresh_utorrent_data()
        
        upload = 0
        download = 0
        for torrent in self.torrents:
            upload += torrent[8]
            download += torrent[9]
        if self.type == 'current_status':
            if upload > 0 and download > 0:
                self._state = 'Up/Down'
            elif upload > 0 and download == 0:
                self._state = 'Seeding'
            elif upload == 0 and download > 0:
                self._state = 'Downloading'
            else:
                self._state = STATE_IDLE

        if self.type == 'download_speed':
            mb_spd = float(download)
            mb_spd = mb_spd / 1024 / 1024
            self._state = round(mb_spd, 2 if mb_spd < 0.1 else 1)
        elif self.type == 'upload_speed':
            mb_spd = float(upload)
            mb_spd = mb_spd / 1024 / 1024
            self._state = round(mb_spd, 2 if mb_spd < 0.1 else 1)