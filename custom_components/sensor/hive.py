"""
Hive Integration - sensor

"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, CONF_USERNAME, CONF_PASSWORD, ATTR_TEMPERATURE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform
import custom_components.hive as hive
from homeassistant.loader import get_component

DEPENDENCIES = ['hive']

_LOGGER = logging.getLogger(__name__)

        
def setup_platform(hass, config, add_devices, DeviceList, discovery_info=None):
    """Setup Hive sensor devices"""
    HiveComponent = get_component('hive')
       
    if len(DeviceList) > 0:
        if "Hive_Device_Heating_CurrentTemperature" in DeviceList:
            add_devices([Hive_Device_Heating_CurrentTemperature(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_Heating_TargetTemperature" in DeviceList:    
            add_devices([Hive_Device_Heating_TargetTemperature(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_Heating_State" in DeviceList:
            add_devices([Hive_Device_Heating_State(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_Heating_Mode" in DeviceList:
            add_devices([Hive_Device_Heating_Mode(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_Heating_Boost" in DeviceList:
            add_devices([Hive_Device_Heating_Boost(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_HotWater_State" in DeviceList:
            add_devices([Hive_Device_HotWater_State(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_HotWater_Mode" in DeviceList:
            add_devices([Hive_Device_HotWater_Mode(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_HotWater_Boost" in DeviceList:
            add_devices([Hive_Device_HotWater_Boost(HiveComponent.HiveObjects_Global)])
        if "Hive_Device_Thermostat_BatteryLevel" in DeviceList:
            add_devices([Hive_Device_Thermostat_BatteryLevel(HiveComponent.HiveObjects_Global)])
        
class Hive_Device_Heating_CurrentTemperature(Entity):
    """Hive Heating current temperature Sensor"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Current Temperature'

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_CurrentTemp()
        
    @property
    def state_attributes(self):
        """Return the state attributes"""
        return self.HiveObjects.Get_Heating_CurrentTemp_State_Attributes()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_Heating_TargetTemperature(Entity):
    """Hive Heating target temperature Sensor"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Target Temperature'

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return True
        
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_TargetTemp()
        
    @property
    def state_attributes(self):
        """Return the state attributes"""
        return self.HiveObjects.Get_Heating_TargetTemperature_State_Attributes()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement to display."""
        return TEMP_CELSIUS
        
#    @property
#    def temperature_unit(self):
#        """The unit of measurement used by the platform."""
#        return TEMP_FAHRENHEIT

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_Heating_State(Entity):
    """Hive Heating current state (On / Off)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Heating State'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_State()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_State_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_Heating_Mode(Entity):
    """Hive Heating current Mode (SCHEDULE / MANUAL / OFF)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Heating Mode'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_Mode()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_Mode_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_Heating_Boost(Entity):
    """Hive Heating current Boost (ON / OFF)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Heating Boost'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_Heating_Boost()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_Heating_Boost_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:radiator'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()
 
            
class Hive_Device_HotWater_State(Entity):
    """Hive Hot water current state (On / Off)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Hot Water State'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_State()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_State_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_HotWater_Mode(Entity):
    """Hive HotWater current Mode (SCHEDULE / ON / OFF)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Hot Water Mode'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_Mode()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_Mode_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()

class Hive_Device_HotWater_Boost(Entity):
    """Hive HotWater current Boost (ON / OFF)"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Hot Water Boost'
        
    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.HiveObjects.Get_HotWater_Boost()
        
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return self.HiveObjects.Get_HotWater_Boost_State_Attributes()
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:water-pump'

        return DeviceIcon

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()
        
class Hive_Device_Thermostat_BatteryLevel(Entity):
    """Hive Thermostat device current battery level sensor"""

    def __init__(self, HiveComponent_HiveObjects):
        """Initialize the sensor."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.BatteryLevel = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hive Thermostat Battery Level'

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return True

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement which this thermostat uses."""
        return "%"

    @property
    def state(self):
        """Return the state of the sensor."""
        self.BatteryLevel = self.HiveObjects.Get_Thermostat_BatteryLevel()
        return self.BatteryLevel
        
    @property
    def icon(self):
        """Return the icon to use."""
        DeviceIcon = 'mdi:battery'
        
        if self.BatteryLevel >= 95 and self.BatteryLevel <= 100:
            DeviceIcon = 'mdi:battery'
        elif self.BatteryLevel >= 85 and self.BatteryLevel < 95:
            DeviceIcon = 'mdi:battery-90'
        elif self.BatteryLevel >= 75 and self.BatteryLevel < 85:
            DeviceIcon = 'mdi:battery-80'
        elif self.BatteryLevel >= 65 and self.BatteryLevel < 75:
            DeviceIcon = 'mdi:battery-70'
        elif self.BatteryLevel >= 55 and self.BatteryLevel < 65:
            DeviceIcon = 'mdi:battery-60'
        elif self.BatteryLevel >= 45 and self.BatteryLevel < 55:
            DeviceIcon = 'mdi:battery-50'
        elif self.BatteryLevel >= 35 and self.BatteryLevel < 45:
            DeviceIcon = 'mdi:battery-40'
        elif self.BatteryLevel >= 25 and self.BatteryLevel < 35:
            DeviceIcon = 'mdi:battery-30'
        elif self.BatteryLevel >= 15 and self.BatteryLevel < 25:
            DeviceIcon = 'mdi:battery-20'
        elif self.BatteryLevel > 5 and self.BatteryLevel < 15:
            DeviceIcon = 'mdi:battery-10'
        elif self.BatteryLevel <= 5:
            DeviceIcon = 'mdi:battery-outline'
        
        return DeviceIcon
        
    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.HiveObjects.UpdateData()