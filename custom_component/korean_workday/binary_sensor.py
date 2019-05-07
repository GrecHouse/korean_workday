"""
Sensor to indicate whether the current day is a workday. (korean version)

For more details about this platform, please refer to the documentation at
https://www.home-assistant.io/components/workday/
https://github.com/GrecHouse/homeassistant/tree/master/custom_component/korean_workday
https://cafe.naver.com/stsmarthome/8226
"""

import logging
from datetime import datetime, timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, WEEKDAYS
from homeassistant.components.binary_sensor import BinarySensorDevice
import homeassistant.helpers.config_validation as cv
from homeassistant.util.json import load_json
import requests
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=1800)

ALLOWED_DAYS = WEEKDAYS + ['holiday']
CONF_SERVICE_KEY = 'service_key'
CONF_WORKDAYS = 'workdays'
CONF_EXCLUDES = 'excludes'
CONF_OFFSET = 'days_offset'
CONF_ADD_HOLIDAYS = 'add_holidays'

DEFAULT_WORKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
DEFAULT_EXCLUDES = ['sat', 'sun', 'holiday']
DEFAULT_NAME = 'Korean Workday'
DEFAULT_OFFSET = 0

PERSISTENCE = '.shopping_list.json'

SERVICE_URL = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey={0}&solYear={1}&solMonth={2}'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SERVICE_KEY): cv.string,
    vol.Optional(CONF_EXCLUDES, default=DEFAULT_EXCLUDES):
        vol.All(cv.ensure_list, [vol.In(ALLOWED_DAYS)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_OFFSET, default=DEFAULT_OFFSET): vol.Coerce(int),
    vol.Optional(CONF_WORKDAYS, default=DEFAULT_WORKDAYS):
        vol.All(cv.ensure_list, [vol.In(ALLOWED_DAYS)]),
    vol.Optional(CONF_ADD_HOLIDAYS): vol.All(cv.ensure_list, [cv.string]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Workday sensor."""
    sensor_name = config.get(CONF_NAME)
    service_key = config.get(CONF_SERVICE_KEY)
    workdays = config.get(CONF_WORKDAYS)
    excludes = config.get(CONF_EXCLUDES)
    days_offset = config.get(CONF_OFFSET)
    add_holidays = config.get(CONF_ADD_HOLIDAYS)

    obj_holidays = []

    # Add custom holidays
    try:
        for dateStr in add_holidays:
            obj_holidays.append(dateStr)
            _LOGGER.debug("Add custom holiday : %s", dateStr)
    except TypeError:
        _LOGGER.debug("No custom holidays or invalid holidays")

    add_entities([IsWorkdaySensor(
        obj_holidays, workdays, excludes, days_offset, sensor_name, service_key)], True)


def day_to_string(day):
    """Convert day index 0 - 7 to string."""
    try:
        return ALLOWED_DAYS[day]
    except IndexError:
        return None

def get_date(date):
    """Return date. Needed for testing."""
    return date


class IsWorkdaySensor(BinarySensorDevice):
    """Implementation of a Workday sensor."""

    def __init__(self, obj_holidays, workdays, excludes, days_offset, name, service_key):
        """Initialize the Workday sensor."""
        self._name = name
        self._service_key = service_key
        self._obj_holidays = obj_holidays
        self._workdays = workdays
        self._excludes = excludes
        self._days_offset = days_offset
        self._state = None
        self._last_updated = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the device."""
        return self._state

    def is_include(self, day, now):
        """Check if given day is in the includes list."""
        if day in self._workdays:
            return True
        if 'holiday' in self._workdays and now in self._obj_holidays:
            return True
        return False

    def is_exclude(self, day, now):
        """Check if given day is in the excludes list."""
        if day in self._excludes:
            return True
        if 'holiday' in self._excludes and now in self._obj_holidays:
            return True
        return False

    def add_korean_holiday(self, now):
        """Check for korean holiday API results."""
        yy = str(now.year)
        mm = str('{:02d}'.format(now.month))
        req_url = SERVICE_URL.format(self._service_key, yy, mm)
        try:
            res = requests.get(req_url, timeout=10)
            res.raise_for_status()
            tree = ET.ElementTree(ET.fromstring(res.content))
            root = tree.getroot()
            if not ET.iselement(root.find('body')):
                _LOGGER.error( 'API Call Error. %s', res.content )
                return False
            _LOGGER.debug( 'API Call Success. %s', res.content )
            for item in root.findall('body/items/item/locdate'):
                self._obj_holidays.append(item.text)
                _LOGGER.debug("Add API holiday : %s", item.text)
        except Exception as ex:
            _LOGGER.error('Failed to get data.go.kr API Error: %s', ex)
        return False

    def add_shopping_list_holiday(self):
        """Check for user added holiday."""
        shopping_list = load_json(self.hass.config.path(PERSISTENCE), default=[])
        for item in shopping_list:
            if item['name'].startswith('#'):
                adddate = item['name'].replace('#','')
                try:
                    datetime.strptime(adddate, '%Y%m%d')
                    if item['complete']:
                        self._obj_holidays.remove(adddate)
                        _LOGGER.debug("Remove ShoppingList holiday : %s", adddate)
                    else:
                        self._obj_holidays.append(adddate)
                        _LOGGER.debug("Add ShoppingList holiday : %s", adddate)
                except ValueError:
                    _LOGGER.debug("Not date : %s", adddate)

    def set_last_updated(self, last_updated):
        """Set the state attributes."""
        self._last_updated = last_updated

    @property
    def state_attributes(self):
        """Return the attributes of the entity."""
        # return self._attributes
        return {
            CONF_WORKDAYS: self._workdays,
            CONF_EXCLUDES: self._excludes,
            CONF_OFFSET: self._days_offset,
            'last_updated': datetime.today()
        }

    async def async_update(self):
        """Get date and look whether it is a holiday."""
        # Default is no workday
        self._state = False

        # Get iso day of the week (1 = Monday, 7 = Sunday)
        date = get_date(datetime.today()) + timedelta(days=self._days_offset)
        day = date.isoweekday() - 1
        day_of_week = day_to_string(day)
        dateStr = date.strftime('%Y%m%d')

        self.add_shopping_list_holiday()

        if self._service_key and \
            ( self._last_updated is None or self._last_updated.strftime('%Y%m%d') != dateStr ) :
            _LOGGER.debug( 'last_updated : %s , now : %s', self._last_updated, datetime.today() )
            self.add_korean_holiday(date)

        if self.is_include(day_of_week, dateStr):
            self._state = True

        if self.is_exclude(day_of_week, dateStr):
            self._state = False

        self.set_last_updated(datetime.today())


