"""
Hive Integration - light

"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta

# Import the device class from the component that you want to support
from homeassistant.components.light import (Light, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, SUPPORT_BRIGHTNESS,  SUPPORT_COLOR_TEMP, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform
import custom_components.hive as hive
from homeassistant.loader import get_component

# Home Assistant depends on 3rd party packages for API specific code.
DEPENDENCIES = ['hive']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, DeviceList, discovery_info=None):
    """Setup Hive light devices"""
    HiveComponent = get_component('hive')

    if len(DeviceList) > 0:
        for aDevice in DeviceList:
            if "HA_DeviceType" in aDevice and "Hive_NodeID" in aDevice and "Hive_NodeName" in aDevice and "Hive_Light_DeviceType" in aDevice:
                if aDevice["HA_DeviceType"] == "Hive_Device_Light":
                    add_devices([Hive_Device_Light(HiveComponent.HiveObjects_Global, aDevice["Hive_NodeID"], aDevice["Hive_Light_DeviceType"], aDevice["Hive_NodeName"])])
                    
class Hive_Device_Light(Light):
    """Hive Active Light Device"""

    def __init__(self, HiveComponent_HiveObjects, NodeID, NodeDeviceType, NodeName):
        """Initialize the Light device."""
        self.HiveObjects = HiveComponent_HiveObjects
        self.NodeID = NodeID
        self.NodeName = NodeName
        self.NodeDeviceType = NodeDeviceType

    @property
    def name(self):
        """Return the display name of this light."""
        return self.NodeName

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        if self.NodeDeviceType == "Dimmable":
            MINCOLORTEMP = None
        elif self.NodeDeviceType == "CoolToWarmWhite":
            MINCOLORTEMP = self.HiveObjects.Get_Light_Min_Color_Temp(self.NodeID)
        elif self.NodeDeviceType == "ColourChanging":
            MINCOLORTEMP = self.HiveObjects.Get_Light_Min_Color_Temp(self.NodeID)

        return MINCOLORTEMP

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        if self.NodeDeviceType == "Dimmable":
            MAXCOLORTEMP = None
        elif self.NodeDeviceType == "CoolToWarmWhite":
            MAXCOLORTEMP = self.HiveObjects.Get_Light_Max_Color_Temp(self.NodeID)
        elif self.NodeDeviceType == "ColourChanging":
            MAXCOLORTEMP = self.HiveObjects.Get_Light_Max_Color_Temp(self.NodeID)

        return MAXCOLORTEMP

    @property
    def color_temp(self):
        """Return the CT color value in mireds."""
        if self.NodeDeviceType == "Dimmable":
            COLORTEMP = None
        elif self.NodeDeviceType == "CoolToWarmWhite":
            COLORTEMP = self.HiveObjects.Get_Light_Color_Temp(self.NodeID)
        elif self.NodeDeviceType == "ColourChanging":
            COLORTEMP = self.HiveObjects.Get_Light_Color_Temp(self.NodeID)

        return COLORTEMP

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255)."""

        return self.HiveObjects.Get_Light_Brightness(self.NodeID)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.HiveObjects.Get_Light_State(self.NodeID)

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""

        NewBrightness = None
        NewColorTemp = None
        if ATTR_BRIGHTNESS in kwargs:
            TmpNewBrightness = kwargs.get(ATTR_BRIGHTNESS)
            PercentageBrightness = ((TmpNewBrightness / 255) * 100)
            NewBrightness = int(round(PercentageBrightness / 5.0) * 5.0)
            if NewBrightness == 0:
                NewBrightness = 5
        if ATTR_COLOR_TEMP in kwargs:
            TmpNewColorTemp = kwargs.get(ATTR_COLOR_TEMP)
            NewColorTemp = round(1000000 / TmpNewColorTemp)

        self.HiveObjects.Set_Light_TurnON(self.NodeID, NewBrightness, NewColorTemp)

    def turn_off(self):
        """Instruct the light to turn off."""
        self.HiveObjects.Set_Light_TurnOFF(self.NodeID)

    def update(self):
        """Update all Node data frome Hive"""
        self.HiveObjects.UpdateData()

    @property
    def supported_features(self):
        """Flag supported features."""
        SUPPORTFEATURES = None
        if self.NodeDeviceType == "Dimmable":
            SUPPORTFEATURES = (SUPPORT_BRIGHTNESS)
        elif self.NodeDeviceType == "CoolToWarmWhite":
            SUPPORTFEATURES = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP)
        elif self.NodeDeviceType == "ColourChanging":
            SUPPORTFEATURES = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_RGB_COLOR)

        return SUPPORTFEATURES