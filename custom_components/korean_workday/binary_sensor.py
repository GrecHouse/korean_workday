"""
Sensor to indicate whether the current day is a workday. (for korean)

For more details about this platform, please refer to the documentation at
https://www.home-assistant.io/components/workday/
https://github.com/GrecHouse/korean_workday
"""

import logging
from datetime import datetime, timedelta
from pytz import timezone
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, WEEKDAYS, EVENT_HOMEASSISTANT_START
try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
except:
    from homeassistant.components.binary_sensor import BinarySensorDevice as BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.util.json import load_json
import json
import async_timeout

_LOGGER = logging.getLogger(__name__)

ALLOWED_DAYS = WEEKDAYS + ['holiday']
CONF_SERVICE_KEY = 'service_key'
CONF_WORKDAYS = 'workdays'
CONF_EXCLUDES = 'excludes'
CONF_OFFSET = 'days_offset'
CONF_ADD_HOLIDAYS = 'add_holidays'
CONF_HOLIDAY_NAME = 'holiday_name'
CONF_INPUT_ENTITY = 'input_entity'
CONF_USE_SHOPPING_LIST = 'shopping_list'
CONF_REMOVE_HOLIDAYS = 'remove_holidays'

DEFAULT_WORKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
DEFAULT_EXCLUDES = ['sat', 'sun', 'holiday']
DEFAULT_NAME = 'Korean Workday'
DEFAULT_INPUT_ENTITY = 'input_text.holiday'
DEFAULT_OFFSET = 0

SHOPPING_LIST_JSON = '.shopping_list.json'
SERVICE_URL = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey={0}&solYear={1}&solMonth={2}'
GITHUB_URL = 'https://raw.githubusercontent.com/GrecHouse/api/master/holiday.json'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SERVICE_KEY): cv.string,
    vol.Optional(CONF_INPUT_ENTITY, default=DEFAULT_INPUT_ENTITY): cv.entity_id,
    vol.Optional(CONF_USE_SHOPPING_LIST, default=False): cv.boolean,
    vol.Optional(CONF_EXCLUDES, default=DEFAULT_EXCLUDES):
        vol.All(cv.ensure_list, [vol.In(ALLOWED_DAYS)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_OFFSET, default=DEFAULT_OFFSET): vol.Coerce(int),
    vol.Optional(CONF_WORKDAYS, default=DEFAULT_WORKDAYS):
        vol.All(cv.ensure_list, [vol.In(ALLOWED_DAYS)]),
    vol.Optional(CONF_ADD_HOLIDAYS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_REMOVE_HOLIDAYS, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Workday sensor."""
    sensor_name = config.get(CONF_NAME)
    service_key = config.get(CONF_SERVICE_KEY)
    workdays = config.get(CONF_WORKDAYS)
    excludes = config.get(CONF_EXCLUDES)
    days_offset = config.get(CONF_OFFSET)
    add_holidays = config.get(CONF_ADD_HOLIDAYS)
    remove_holidays = config.get(CONF_REMOVE_HOLIDAYS)
    input_entity = config.get(CONF_INPUT_ENTITY)
    shopping_list = config.get(CONF_USE_SHOPPING_LIST)

    device = IsWorkdaySensor(
        hass, add_holidays, remove_holidays, workdays, excludes, days_offset, sensor_name, service_key, input_entity, shopping_list)

    async_track_point_in_time(
        hass, device.point_in_time_listener, device.get_next_interval())

    async_add_entities([device], True)

def day_to_string(day):
    """Convert day index 0 - 7 to string."""
    try:
        return ALLOWED_DAYS[day]
    except IndexError:
        return None

class IsWorkdaySensor(BinarySensorEntity):
    """Implementation of a Workday sensor."""

    def __init__(self, hass, add_holidays, remove_holidays, workdays, excludes, days_offset, name, service_key, input_entity, shopping_list):
        """Initialize the Workday sensor."""
        self._name = name
        self._hass = hass
        self._service_key = service_key
        self._input_entity = input_entity
        self._add_holidays = add_holidays
        self._remove_holidays = remove_holidays

        self._workdays = workdays
        self._excludes = excludes
        self._days_offset = days_offset
        self._shopping_list = shopping_list
        self._obj_holidays = []
        self._state = None
        self._holiday_name = None
        self._session = async_get_clientsession(self._hass)

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        async def sensor_state_listener(entity, old_state, new_state):
            """Handle input_text.holiday state changes."""
            #self.async_schedule_update_ha_state(True)
            await self._update_internal_state()

        @callback
        async def sensor_startup(event):
            """Update template on startup."""
            async_track_state_change(self._hass, [self._input_entity], sensor_state_listener)
            #self.async_schedule_update_ha_state(True)
            await self._update_internal_state()

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, sensor_startup)

    @callback
    async def point_in_time_listener(self, time_date):
        """Get the latest data and update state."""
        await self._update_internal_state()
        self.async_schedule_update_ha_state()
        async_track_point_in_time(
            self.hass, self.point_in_time_listener, self.get_next_interval())

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the device."""
        return self._state

    @property
    def state_attributes(self):
        """Return the attributes of the entity."""
        return {
            CONF_WORKDAYS: self._workdays,
            CONF_EXCLUDES: self._excludes,
            CONF_OFFSET: self._days_offset,
            CONF_HOLIDAY_NAME: self._holiday_name
        }

    def is_include(self, day, now):
        if day in self._workdays:
            return True
        if 'holiday' in self._workdays and now in self._obj_holidays:
            return True
        return False

    def is_exclude(self, day, now):
        """Check if given day is in the excludes list."""
        if now in self._remove_holidays:
            return False
        if day in self._excludes:
            return True
        if 'holiday' in self._excludes and now in self._obj_holidays:
            return True
        return False

    async def add_holiday_from_api(self, now):
        """Check for korean holiday API results."""
        yy = str(now.year)
        mm = str('{:02d}'.format(now.month))
        req_url = SERVICE_URL.format(self._service_key, yy, mm)
        try:
            with async_timeout.timeout(10):
                response = await self._session.get(req_url)
            result = await response.read()
            xml = result.decode('utf8')
            dic = xmltodict.parse(xml)
            if '00' == dic['response']['header']['resultCode'] and '0' != dic['response']['body']['totalCount']:
                hlist = dic['response']['body']['items']['item']
                if isinstance(hlist, list):
                    for holiday in hlist:
                        self._obj_holidays.append(holiday['locdate'])
                        self._obj_holidays.append("#"+holiday['dateName'])
                        _LOGGER.debug("Add API holiday : %s", holiday['locdate'])
                elif len(hlist) > 0:
                    self._obj_holidays.append(hlist['locdate'])
                    self._obj_holidays.append("#"+hlist['dateName'])
                    _LOGGER.debug("Add API holiday : %s", hlist['locdate'])
        except Exception as ex:
            _LOGGER.error('Failed to get data.go.kr API Error: %s', ex)

    async def add_holiday_from_gh(self):
        """Check for korean holiday JSON results."""
        try:
            with async_timeout.timeout(10):
                response = await self._session.get(GITHUB_URL)
            result = await response.read()
            result = json.loads(result)

            hlist = result['item']
            if isinstance(hlist, list):
                for holiday in hlist:
                    self._obj_holidays.append(holiday['locdate'])
                    self._obj_holidays.append("#"+holiday['dateName'])
                    _LOGGER.debug("Add GH holiday : %s", holiday['locdate'])
            elif len(hlist) > 0:
                self._obj_holidays.append(hlist['locdate'])
                self._obj_holidays.append("#"+hlist['dateName'])
                _LOGGER.debug("Add GH holiday : %s", hlist['locdate'])
        except Exception as ex:
            _LOGGER.error('Failed to get Github JSON Error: %s', ex)

    def add_holiday_from_input(self, now):
        add_input = self._hass.states.get(self._input_entity)
        if add_input:
            holis = add_input.state.splitlines()
            for item in holis:
                name = ''
                if "#" in item:
                    ii = item.split("#")
                    name = ii[1]
                    item = ii[0]
                if len(item) == 4:
                    item = str(now.year) + item
                try:
                    datetime.strptime(item, '%Y%m%d')
                    self._obj_holidays.append(item)
                    if '' != name:
                        self._obj_holidays.append("#"+name)
                    _LOGGER.debug("Add InputText holiday : %s", item)
                except ValueError:
                    _LOGGER.debug("Not date : %s", item)

    def add_holiday_from_shopping_list(self):
        """Check for user added holiday."""
        shopping_list = load_json(self.hass.config.path(SHOPPING_LIST_JSON), default=[])
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

    def get_next_interval(self, now=None):
        """Compute next time an update should occur."""
        now = datetime.now(timezone('Asia/Seoul'))
        today = datetime(now.year, now.month, now.day)
        return today + timedelta(days=1)

    async def _update_internal_state(self):
        """Get date and look whether it is a holiday."""
        # Default is no workday
        self._state = False
        self._obj_holidays.clear()

        # Add custom holidays
        try:
            for dateStr in self._add_holidays:
                self._obj_holidays.append(dateStr)
                _LOGGER.debug("Add custom holiday : %s", dateStr)
        except TypeError:
            _LOGGER.debug("No custom holidays or invalid holidays")

        # Get iso day of the week (1 = Monday, 7 = Sunday)
        date = datetime.today() + timedelta(days=self._days_offset)
        day = date.isoweekday() - 1
        day_of_week = day_to_string(day)
        today = date.strftime('%Y%m%d')

        self.add_holiday_from_input(date)

        if self._shopping_list:
            self.add_holiday_from_shopping_list()

        if self._service_key:
            await self.add_holiday_from_api(date)
        else:
            await self.add_holiday_from_gh()

        # Remove holidays
        try:
            for remove_holiday in self._remove_holidays:
                try:
                    removed = self._obj_holidays.pop(remove_holiday)
                    _LOGGER.debug("Removed %s", remove_holiday)
                except KeyError as unmatched:
                    _LOGGER.warning("No holiday found matching %s", unmatched)
        except TypeError:
            _LOGGER.debug("No holidays to remove or invalid holidays")

        holidays = self._obj_holidays

        try:
            name = holidays[holidays.index(today)+1]
            if name and name.startswith("#"):
                self._holiday_name = name[1:]
        except Exception as ex:
            self._holiday_name = None
            #_LOGGER.debug(ex)

        if self.is_include(day_of_week, today):
            self._state = True

        if self.is_exclude(day_of_week, today):
            self._state = False

        _LOGGER.debug('Holiday List : %s', holidays)
        _LOGGER.info('Korean Workday Updated : %s', datetime.today())
