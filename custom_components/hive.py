"""
Hive Integration - Platform

"""
import logging, json
import voluptuous as vol
from datetime import datetime
from datetime import timedelta
import requests

from homeassistant.util import Throttle
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import load_platform

import homeassistant as HASS

REQUIREMENTS = ['requests==2.11.1']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'hive'
HiveComponent = None


Hive_Node_Update_Interval_Default = 120
MINUTES_BETWEEN_LOGONS = 15

Current_Node_Attribute_Values = {"Header" : "HeaderText"}

class Hive_Nodes:
    Hub = []
    Receiver = []
    Thermostat = []
    Heating = []
    HotWater = []
    Light = []
    
class Hive_Session:
    SessionID = ""
    Session_Logon_DateTime = datetime(2017,1,1,12,0,0)
    AccountDetails = ""
    UserName = ""
    Password = ""
    Nodes = Hive_Nodes()
    Update_Interval_Seconds = Hive_Node_Update_Interval_Default
    LastUpdate = datetime(2017,1,1,12,0,0)

class Hive_API_URLS:
    Base = ""
    Login = ""
    Users = ""
    Nodes = ""

class Hive_API_Headers:
    Accept_Key = ""
    Accept_Value = ""
    Client_Key = ""
    Client_Value = ""
    ContentType_Key = ""
    ContentType_Value = ""
    SessionID_Key = ""
    SessionID_Value = ""

class Hive_API_Details:
    URLs = Hive_API_URLS()
    Headers = Hive_API_Headers()
    Caller = ""

    
HiveAPI_Details = Hive_API_Details()
HiveSession_Current = Hive_Session()

        
def Initialise_App():
    HiveAPI_Details.Caller = "Hive Web Dashboard"

    HiveAPI_Details.URLs.Base = "https://api-prod.bgchprod.info:443/omnia"
    HiveAPI_Details.URLs.Login = "/auth/sessions"
    HiveAPI_Details.URLs.Users = "/users"
    HiveAPI_Details.URLs.Nodes = "/nodes"

    HiveAPI_Details.Headers.Accept_Key = "Accept"
    HiveAPI_Details.Headers.Accept_Value_6_5 = "application/vnd.alertme.zoo-6.5+json"
    HiveAPI_Details.Headers.Accept_Value_6_1 = "application/vnd.alertme.zoo-6.1+json"
    HiveAPI_Details.Headers.Client_Key = "X-Omnia-Client"
    HiveAPI_Details.Headers.Client_Value = "Hive Web Dashboard"
    HiveAPI_Details.Headers.ContentType_Key = "content-type"
    HiveAPI_Details.Headers.ContentType_Value_6_5 = "application/vnd.alertme.zoo-6.5+json"
    HiveAPI_Details.Headers.ContentType_Value_6_1 = "application/vnd.alertme.zoo-6.1+json"
    HiveAPI_Details.Headers.SessionID_Key = "X-Omnia-Access-Token"
    HiveAPI_Details.Headers.SessionID_Value = None


def Hive_API_JsonCall (RequestType, RequestURL, APIVersion, JsonStringContent):
    ContentType_Value = HiveAPI_Details.Headers.ContentType_Value_6_5
    Accept_Value = HiveAPI_Details.Headers.Accept_Value_6_5
    
    if APIVersion == "6.5":
        ContentType_Value = HiveAPI_Details.Headers.ContentType_Value_6_5
        Accept_Value = HiveAPI_Details.Headers.Accept_Value_6_5
    elif APIVersion == "6.1":
        ContentType_Value = HiveAPI_Details.Headers.ContentType_Value_6_1
        Accept_Value = HiveAPI_Details.Headers.Accept_Value_6_1
    else:
        ContentType_Value = HiveAPI_Details.Headers.ContentType_Value_6_5
        Accept_Value = HiveAPI_Details.Headers.Accept_Value_6_5
   
    
    API_Headers = {HiveAPI_Details.Headers.ContentType_Key:ContentType_Value,HiveAPI_Details.Headers.Accept_Key:Accept_Value,HiveAPI_Details.Headers.Client_Key:HiveAPI_Details.Headers.Client_Value,HiveAPI_Details.Headers.SessionID_Key:HiveAPI_Details.Headers.SessionID_Value}
    JSON_Response = ""
    
    try:
        if RequestType == "POST":
            JSON_Response = requests.post(HiveAPI_Details.URLs.Base + RequestURL, data=JsonStringContent, headers=API_Headers)
        elif RequestType == "GET":
            JSON_Response = requests.get(HiveAPI_Details.URLs.Base + RequestURL, data=JsonStringContent, headers=API_Headers)
        elif RequestType == "PUT":
            JSON_Response = requests.put(HiveAPI_Details.URLs.Base + RequestURL, data=JsonStringContent, headers=API_Headers)
        else:
            _LOGGER.error("Unknown RequestType : %s", RequestType)
    except:
        JSON_Response = "No response to JSON Hive API request"

    return JSON_Response


def Hive_API_Logon():
    HiveSession_Current.SessionID = None

    JsonStringContent = '{"sessions":[{"username":"' + HiveSession_Current.UserName + '","password":"' + HiveSession_Current.Password + '","caller":"' + HiveAPI_Details.Caller + '"}]}'
    API_Response_Login = Hive_API_JsonCall ("POST", HiveAPI_Details.URLs.Login, "6.5", JsonStringContent)
    API_Response_Login_Parsed = json.loads(API_Response_Login.text)
    
    #API_Response_Login = 400 = logon failure
    #API_Response_Login = 200 = Login success

    if 'sessions' in API_Response_Login.text:
        HiveAPI_Details.Headers.SessionID_Value = API_Response_Login_Parsed["sessions"][0]["sessionId"]
        HiveSession_Current.SessionID = HiveAPI_Details.Headers.SessionID_Value
        HiveSession_Current.Session_Logon_DateTime = datetime.now()
    else:
        HiveSession_Current.SessionID = None
        _LOGGER.error("Hive API login failed with error : %s", API_Response_Login)


def Private_Get_Heating_Min_Temperature():
    Heating_MinTemp_Default = 5
    Heating_MinTemp_Return = 0
    Heating_MinTemp_tmp = 0
    Heating_MinTemp_Found = False
        
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "minHeatTargetTemperature" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["minHeatTargetTemperature"]:
            Heating_MinTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["minHeatTargetTemperature"]["displayValue"]
            Heating_MinTemp_Found = True
            
    if Heating_MinTemp_Found == True:
        Heating_MinTemp_Return = Heating_MinTemp_tmp
    else:
        Heating_MinTemp_Return = Heating_MinTemp_Default

    return Heating_MinTemp_Return

def Private_Get_Heating_Max_Temperature():
    Heating_MaxTemp_Default = 32
    Heating_MaxTemp_Return = 0
    Heating_MaxTemp_tmp = 0
    Heating_MaxTemp_Found = False
        
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "maxHeatTargetTemperature" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["maxHeatTargetTemperature"]:
            Heating_MaxTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["maxHeatTargetTemperature"]["displayValue"]
            Heating_MaxTemp_Found = True
            
    if Heating_MaxTemp_Found == True:
        Heating_MaxTemp_Return = Heating_MaxTemp_tmp
    else:
        Heating_MaxTemp_Return = Heating_MaxTemp_Default

    return Heating_MaxTemp_Return
    
def Private_Get_Heating_CurrentTemp():
    Heating_CurrentTemp_Return = 0
    Heating_CurrentTemp_tmp = 0
    Heating_CurrentTemp_Found = False
        
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "temperature_sensor_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "temperature" in HiveSession_Current.Nodes.Heating[0]["features"]["temperature_sensor_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["temperature_sensor_v1"]["temperature"]:
            Heating_CurrentTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["temperature_sensor_v1"]["temperature"]["displayValue"]
            Heating_CurrentTemp_Found = True
            
    if Heating_CurrentTemp_Found == True:
        Current_Node_Attribute_Values["Heating_CurrentTemp"] = Heating_CurrentTemp_tmp
        Heating_CurrentTemp_Return = Heating_CurrentTemp_tmp
    else:
        if "Heating_CurrentTemp" in Current_Node_Attribute_Values:
            Heating_CurrentTemp_Return = Current_Node_Attribute_Values.get("Heating_CurrentTemp")
        else:
            Heating_CurrentTemp_Return = 0

    return Heating_CurrentTemp_Return
    
def Private_Get_Heating_CurrentTemp_State_Attributes():
    State_Attibutes = {}
    Temperature_Current = 0
    Temperature_Target = 0
    Temperature_Difference = 0
    
    if len(HiveSession_Current.Nodes.Heating) > 0:
        Temperature_Current = Private_Get_Heating_CurrentTemp()
        Temperature_Target = Private_Get_Heating_TargetTemp()
        
        if Temperature_Target > Temperature_Current:
            Temperature_Difference = Temperature_Target - Temperature_Current
        
            State_Attibutes.update({"Current Temperature": Temperature_Current})
            State_Attibutes.update({"Target Temperature": Temperature_Target})
            State_Attibutes.update({"Temperature Difference": Temperature_Difference})
#        State_Attibutes.update({"Time to target": "01:30"})
    return State_Attibutes

def Private_Get_Heating_TargetTemp():
    Heating_TargetTemp_Return = 0
    Heating_TargetTemp_tmp = 0
    Heating_TargetTemp_Found = False
   
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "targetHeatTemperature" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]:
            if "propertyStatus" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]:
                if HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]["propertyStatus"] == "PENDING":
                    Heating_TargetTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]["targetValue"]
                    Heating_TargetTemp_Found = True
                else:
                    Heating_TargetTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]["displayValue"]
                    Heating_TargetTemp_Found = True
            else:
                Heating_TargetTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]["displayValue"]
                Heating_TargetTemp_Found = True
        
        if Heating_TargetTemp_tmp == 1:
            if "features" in HiveSession_Current.Nodes.Heating[0] and "thermostat_frost_protect_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "frostProtectTemperature" in HiveSession_Current.Nodes.Heating[0]["features"]["thermostat_frost_protect_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["thermostat_frost_protect_v1"]["frostProtectTemperature"]:
                Heating_TargetTemp_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["thermostat_frost_protect_v1"]["frostProtectTemperature"]["displayValue"]
                Heating_TargetTemp_Found = True
        
    if Heating_TargetTemp_Found == True:
        Current_Node_Attribute_Values["Heating_TargetTemp"] = Heating_TargetTemp_tmp
        Heating_TargetTemp_Return = Heating_TargetTemp_tmp
    else:
        if "Heating_TargetTemp" in Current_Node_Attribute_Values:
            Heating_TargetTemp_Return = Current_Node_Attribute_Values.get("Heating_TargetTemp")
        else:
            Heating_TargetTemp_Return = 0

    return Heating_TargetTemp_Return
    
def Private_Get_Heating_TargetTemperature_State_Attributes():
    State_Attibutes = {}
    
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "targetHeatTemperature" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]:
            Heating_TargetTempChanged_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["targetHeatTemperature"]["reportChangedTime"]
            Heating_TargetTempChanged_tmp_UTC_DT = Private_Epoch_TimeMilliseconds_To_datetime(Heating_TargetTempChanged_tmp)

            State_Attibutes.update({"Target Temperature changed": Private_Convert_DateTime_StateDisplayString(Heating_TargetTempChanged_tmp_UTC_DT)})
    return State_Attibutes

def Private_Convert_DateTime_StateDisplayString(DateTimeToConvert):
    ReturnString = ""
    SecondsDifference = (datetime.now() - DateTimeToConvert).total_seconds()
        
    if SecondsDifference < 60:
        ReturnString = str(round(SecondsDifference)) + " seconds ago"
    elif SecondsDifference >= 60 and SecondsDifference <= (60 * 60):
        ReturnString = str(round(SecondsDifference / 60)) + " minutes ago"
    elif SecondsDifference > (60 * 60) and SecondsDifference <= (60 * 60 * 24):
        ReturnString = DateTimeToConvert.strftime('%H:%M')
    else:
        ReturnString = DateTimeToConvert.strftime('%H:%M %d-%b-%Y')
    
    return ReturnString

def Private_Epoch_TimeMilliseconds_To_datetime(EpochStringMilliseconds):
    EpochStringseconds = EpochStringMilliseconds / 1000
    DateTimeUTC = datetime.fromtimestamp(EpochStringseconds)
    return DateTimeUTC

def Private_Get_Heating_State():
    Heating_State_Return = "OFF"
    Heating_State_tmp = "OFF"
    Heating_State_Found = False

    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "operatingState" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingState"]:
            Heating_State_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingState"]["displayValue"]
            Heating_State_Found = True
    
    if Heating_State_Found == True:
        Current_Node_Attribute_Values["Heating_State"] = Heating_State_tmp
        Heating_State_Return = Heating_State_tmp
    else:
        if "Heating_State" in Current_Node_Attribute_Values:
            Heating_State_Return = Current_Node_Attribute_Values.get("Heating_State")
        else:
            Heating_State_Return = "UNKNOWN"
                
    return Heating_State_Return
    
def Private_Get_Heating_State_State_Attributes():
    State_Attibutes = {}
    CurrentHeatingState = Private_Get_Heating_State()

    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "operatingState" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingState"]:
            Heating_Heating_State_Changed_tmp = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingState"]["reportChangedTime"]
            Heating_Heating_State_Changed_tmp_UTC_DT = Private_Epoch_TimeMilliseconds_To_datetime(Heating_Heating_State_Changed_tmp)
            
            StateAttributeString = ""
            if CurrentHeatingState == "ON":
                StateAttributeString = "Heating State ON since"
            elif CurrentHeatingState == "OFF":
                StateAttributeString = "Heating State OFF since"
            else:
                StateAttributeString = "Current Heating State since"
            
            State_Attibutes.update({StateAttributeString: Private_Convert_DateTime_StateDisplayString(Heating_Heating_State_Changed_tmp_UTC_DT)})

    return State_Attibutes

def Private_Get_Heating_Mode():
    Heating_Mode_Return = "UNKNOWN"
    Heating_Mode_tmp = "UNKNOWN"
    Heating_Mode_Found = False

    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "on_off_device_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "mode" in HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]:
            if HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]["displayValue"] == "ON":
                if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]:
                    tmp_PropertyStatus = "COMPLETE"
                    if "propertyStatus" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        tmp_PropertyStatus = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["propertyStatus"]
                    if tmp_PropertyStatus == "COMPLETE" and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        if HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "SCHEDULE" and HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "MANUAL":
                            if "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "duration" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["duration"]:
                                if HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["duration"]["displayValue"] != "0":
                                    Heating_Mode_tmp = "SCHEDULE"
                                    Heating_Mode_Found = True
                                else:
                                    Heating_Mode_tmp = "MANUAL"
                                    Heating_Mode_Found = True
                            else:
                                    Heating_Mode_tmp = "MANUAL"
                                    Heating_Mode_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "SCHEDULE":
                            Heating_Mode_tmp = "SCHEDULE"
                            Heating_Mode_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "MANUAL":
                            Heating_Mode_tmp = "MANUAL"
                            Heating_Mode_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "CUSTOM":
                            if "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                Heating_Mode_tmp = "OFF"
                                Heating_Mode_Found = True
                            elif "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                if "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]:
                                    if len(HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                        if "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                            if HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                                Heating_Mode_tmp = "SCHEDULE"
                                                Heating_Mode_Found = True
                                            elif HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                                Heating_Mode_tmp = "MANUAL"
                                                Heating_Mode_Found = True
                    elif tmp_PropertyStatus == "PENDING" and "targetValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        if HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "SCHEDULE":
                            Heating_Mode_tmp = "SCHEDULE"
                            Heating_Mode_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "MANUAL":
                            Heating_Mode_tmp = "MANUAL"
                            Heating_Mode_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "CUSTOM":
                            if "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                Heating_Mode_tmp = "OFF"
                                Heating_Mode_Found = True
                            elif "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                if "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]:
                                    if len(HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                        if "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                            if HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                                Heating_Mode_tmp = "SCHEDULE"
                                                Heating_Mode_Found = True
                                            elif HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                                Heating_Mode_tmp = "MANUAL"
                                                Heating_Mode_Found = True
                    elif tmp_PropertyStatus == "PENDING" and "displayValue" not in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"] and "targetValue" not in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        Heating_Mode_tmp = "OFF"
                        Heating_Mode_Found = True
            elif HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]["displayValue"] == "OFF":
                Heating_Mode_tmp = "OFF"
                Heating_Mode_Found = True
    
    if Heating_Mode_Found == True:
        Heating_Mode_Return = Heating_Mode_tmp
    else:
        Heating_Mode_Return = "UNKNOWN"
        _LOGGER.error("Heating Mode not found")
                
    return Heating_Mode_Return
  
def Private_Get_Heating_Mode_State_Attributes():
    State_Attibutes = {}

    return State_Attibutes

    
def Private_Get_Heating_Operation_Mode_List():
    HiveHeating_operation_list = ["SCHEDULE", "MANUAL", "OFF"]
    return HiveHeating_operation_list
    
def Private_Get_Heating_Boost():
    Heating_Boost_Return = "UNKNOWN"
    Heating_Boost_tmp = "UNKNOWN"
    Heating_Boost_Found = False

    if len(HiveSession_Current.Nodes.Heating) > 0:
        if "features" in HiveSession_Current.Nodes.Heating[0] and "on_off_device_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "mode" in HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"] and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]:
            if HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]["displayValue"] == "ON":
                if "features" in HiveSession_Current.Nodes.Heating[0] and "heating_thermostat_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]:
                    tmp_PropertyStatus = "COMPLETE"
                    if "propertyStatus" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        tmp_PropertyStatus = HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["propertyStatus"]
                    if tmp_PropertyStatus == "COMPLETE" and "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        if HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "SCHEDULE":
                            Heating_Boost_tmp = "OFF"
                            Heating_Boost_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "MANUAL":
                            Heating_Boost_tmp = "OFF"
                            Heating_Boost_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["displayValue"] == "CUSTOM":
                            if "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                Heating_Boost_tmp = "ON"
                                Heating_Boost_Found = True
                            elif "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                if "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]:
                                    if len(HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                        if "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                            if HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                                Heating_Boost_tmp = "ON"
                                                Heating_Boost_Found = True
                                            elif HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                                Heating_Boost_tmp = "ON"
                                                Heating_Boost_Found = True
                    elif tmp_PropertyStatus == "PENDING" and "targetValue" in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        if HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "SCHEDULE":
                            Heating_Boost_tmp = "OFF"
                            Heating_Boost_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "MANUAL":
                            Heating_Boost_tmp = "OFF"
                            Heating_Boost_Found = True
                        elif HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]["targetValue"] == "CUSTOM":
                            if "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                Heating_Boost_tmp = "ON"
                                Heating_Boost_Found = True
                            elif "features" in HiveSession_Current.Nodes.Heating[0] and "transient_mode_v1" in HiveSession_Current.Nodes.Heating[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]:
                                if "displayValue" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]:
                                    if len(HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                        if "operatingMode" in HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                            if HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                                Heating_Boost_tmp = "ON"
                                                Heating_Boost_Found = True
                                            elif HiveSession_Current.Nodes.Heating[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                                Heating_Boost_tmp = "ON"
                                                Heating_Boost_Found = True
                    elif tmp_PropertyStatus == "PENDING" and "displayValue" not in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"] and "targetValue" not in HiveSession_Current.Nodes.Heating[0]["features"]["heating_thermostat_v1"]["operatingMode"]:
                        Heating_Boost_tmp = "OFF"
                        Heating_Boost_Found = True
            elif HiveSession_Current.Nodes.Heating[0]["features"]["on_off_device_v1"]["mode"]["displayValue"] == "OFF":
                Heating_Boost_tmp = "OFF"
                Heating_Boost_Found = True

    if Heating_Boost_Found == True:
        Heating_Boost_Return = Heating_Boost_tmp
    else:
        Heating_Boost_Return = "UNKNOWN"
        _LOGGER.error("Heating Boost not found")
            
    return Heating_Boost_Return

def Private_Get_Heating_Boost_State_Attributes():
    State_Attibutes = {}
    BoostOn = False
    
    if Private_Get_Heating_Boost() == "ON":
        BoostOn = True
    else:
        BoostOn = False
    
    return State_Attibutes    
    
def Private_Get_HotWater_Mode():
    HotWater_Mode_Return = "UNKNOWN"
    HotWater_Mode_tmp = "UNKNOWN"
    HotWater_Mode_Found = False
                
    if len(HiveSession_Current.Nodes.HotWater) > 0:
        if "features" in HiveSession_Current.Nodes.HotWater[0] and "water_heater_v1" in HiveSession_Current.Nodes.HotWater[0]["features"]:
            if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]:
                if "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"] and "targetValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                    tmp_PropertyStatus = "COMPLETE"
                    if "propertyStatus" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                        tmp_PropertyStatus = HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["propertyStatus"]
                    if tmp_PropertyStatus == "COMPLETE":
                        if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "SCHEDULE":
                            HotWater_Mode_tmp = "SCHEDULE"
                            HotWater_Mode_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "ON":
                            HotWater_Mode_tmp = "ON"
                            HotWater_Mode_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "CUSTOM":
                            if "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"] and "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"] and len(HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                    if HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                        HotWater_Mode_tmp = "SCHEDULE"
                                        HotWater_Mode_Found = True
                                    elif HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                        HotWater_Mode_tmp = "ON"
                                        HotWater_Mode_Found = True
                            elif "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]:
                                HotWater_Mode_tmp = "OFF"
                                HotWater_Mode_Found = True
                    elif tmp_PropertyStatus == "PENDING":
                        if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "SCHEDULE":
                            HotWater_Mode_tmp = "SCHEDULE"
                            HotWater_Mode_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "ON":
                            HotWater_Mode_tmp = "ON"
                            HotWater_Mode_Found = True
                    elif (tmp_PropertyStatus == "PENDING" or tmp_PropertyStatus == "COMPLETE") and HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "CUSTOM":
                        if "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"] and "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"] and len(HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                            if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                if HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                    HotWater_Mode_tmp = "SCHEDULE"
                                    HotWater_Mode_Found = True
                                elif HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                    HotWater_Mode_tmp = "ON"
                                    HotWater_Mode_Found = True
                        elif "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]:
                            HotWater_Mode_tmp = "OFF"
                            HotWater_Mode_Found = True
                elif "targetValue" not in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"] and "propertyStatus" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                    if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["propertyStatus"] == "PENDING":
                        HotWater_Mode_tmp = "OFF"
                        HotWater_Mode_Found = True
            else:
                HotWater_Mode_tmp = "OFF"
                HotWater_Mode_Found = True
            
    if HotWater_Mode_Found == True:
         HotWater_Mode_Return = HotWater_Mode_tmp
    else:
        HotWater_Mode_Return = "UNKNOWN"
        _LOGGER.error("HotWater Mode not found")

    return HotWater_Mode_Return
    
def Private_Get_HotWater_Mode_State_Attributes():
    State_Attibutes = {}

    return State_Attibutes
 
def Private_Get_HotWater_Operation_Mode_List():
    HiveHotWater_operation_list = ["SCHEDULE", "ON", "OFF"]
    return HiveHotWater_operation_list
    
def Private_Get_HotWater_Boost():
    HotWater_Boost_Return = "UNKNOWN"
    HotWater_Boost_tmp = "UNKNOWN"
    HotWater_Boost_Found = False

    if len(HiveSession_Current.Nodes.HotWater) > 0:
        if "features" in HiveSession_Current.Nodes.HotWater[0] and "water_heater_v1" in HiveSession_Current.Nodes.HotWater[0]["features"]:
            if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]:
                if "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"] and "targetValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                    tmp_PropertyStatus = "COMPLETE"
                    if "propertyStatus" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                        tmp_PropertyStatus = HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["propertyStatus"]
                    if tmp_PropertyStatus == "COMPLETE":
                        if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "SCHEDULE":
                            HotWater_Boost_tmp = "OFF"
                            HotWater_Boost_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "ON":
                            HotWater_Boost_tmp = "OFF"
                            HotWater_Boost_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["displayValue"] == "CUSTOM":
                            if "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"] and "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"] and len(HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                                if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                    if HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                        HotWater_Boost_tmp = "ON"
                                        HotWater_Boost_Found = True
                                    elif HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                        HotWater_Boost_tmp = "ON"
                                        HotWater_Boost_Found = True
                            elif "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]:
                                HotWater_Boost_tmp = "ON"
                                HotWater_Boost_Found = True
                    elif tmp_PropertyStatus == "PENDING":
                        if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "SCHEDULE":
                            HotWater_Boost_tmp = "OFF"
                            HotWater_Boost_Found = True
                        elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "ON":
                            HotWater_Boost_tmp = "OFF"
                            HotWater_Boost_Found = True
                    elif (tmp_PropertyStatus == "PENDING" or tmp_PropertyStatus == "COMPLETE") and HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["targetValue"] == "CUSTOM":
                        if "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"] and "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"] and len(HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"]) > 0:
                            if "operatingMode" in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]:
                                if HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "SCHEDULE":
                                    HotWater_Boost_tmp = "ON"
                                    HotWater_Boost_Found = True
                                elif HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]["previousConfiguration"]["displayValue"][0]["operatingMode"] == "MANUAL":
                                    HotWater_Boost_tmp = "ON"
                                    HotWater_Boost_Found = True
                        elif "transient_mode_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "previousConfiguration" not in HiveSession_Current.Nodes.HotWater[0]["features"]["transient_mode_v1"]:
                            HotWater_Boost_tmp = "ON"
                            HotWater_Boost_Found = True
                elif "targetValue" not in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"] and "propertyStatus" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]:
                    if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["operatingMode"]["propertyStatus"] == "PENDING":
                        HotWater_Boost_tmp = "OFF"
                        HotWater_Boost_Found = True  
            else:
                HotWater_Boost_tmp = "OFF"
                HotWater_Boost_Found = True
                            
    if HotWater_Boost_Found == True:
        HotWater_Boost_Return = HotWater_Boost_tmp
    else:
        HotWater_Boost_Return = "UNKNOWN"
        _LOGGER.error("HotWater Boost not found")

    return HotWater_Boost_Return
    
def Private_Get_HotWater_Boost_State_Attributes():
    State_Attibutes = {}

    return State_Attibutes   
    
def Private_Get_HotWater_State():
    HotWater_State_Return = "OFF"
    HotWater_State_tmp = "OFF"
    HotWater_State_Found = False

    if len(HiveSession_Current.Nodes.HotWater) > 0:
        if "features" in HiveSession_Current.Nodes.HotWater[0] and "water_heater_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "isOn" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"] and "displayValue" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["isOn"]:
            if HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["isOn"]["displayValue"] == True:
                HotWater_State_tmp = "ON"
                HotWater_State_Found = True
            elif HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["isOn"]["displayValue"] == False:
                HotWater_State_tmp = "OFF"
                HotWater_State_Found = True

    if HotWater_State_Found == True:
        Current_Node_Attribute_Values["HotWater_State"] = HotWater_State_tmp
        HotWater_State_Return = HotWater_State_tmp
    else:
        if "HotWater_State" in Current_Node_Attribute_Values:
            HotWater_State_Return = Current_Node_Attribute_Values.get("HotWater_State")
        else:
            HotWater_State_Return = "UNKNOWN"
            
    return HotWater_State_Return
    
def Private_Get_HotWater_State_State_Attributes():
    State_Attibutes = {}
    CurrentHotWaterState = Private_Get_HotWater_State()

    if len(HiveSession_Current.Nodes.HotWater) > 0:
        if "features" in HiveSession_Current.Nodes.HotWater[0] and "water_heater_v1" in HiveSession_Current.Nodes.HotWater[0]["features"] and "isOn" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"] and "reportChangedTime" in HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["isOn"]:
            Heating_HotWater_State_Changed_tmp = HiveSession_Current.Nodes.HotWater[0]["features"]["water_heater_v1"]["isOn"]["reportChangedTime"]
            Heating_HotWater_State_Changed_tmp_UTC_DT = Private_Epoch_TimeMilliseconds_To_datetime(Heating_HotWater_State_Changed_tmp)
            
            StateAttributeString = ""
            if CurrentHotWaterState == "ON":
                StateAttributeString = "HotWater State ON since"
            elif CurrentHotWaterState == "OFF":
                StateAttributeString = "HotWater State OFF since"
            else:
                StateAttributeString = "Current HotWater State since"
            
            State_Attibutes.update({StateAttributeString: Private_Convert_DateTime_StateDisplayString(Heating_HotWater_State_Changed_tmp_UTC_DT)})

    return State_Attibutes

def Private_Get_Thermostat_BatteryLevel():
    Thermostat_BatteryLevel_Return = 0
    Thermostat_BatteryLevel_tmp = 0
    Thermostat_BatteryLevel_Found = False

    if len(HiveSession_Current.Nodes.Thermostat) > 0:
        if "features" in HiveSession_Current.Nodes.Thermostat[0] and "battery_device_v1" in HiveSession_Current.Nodes.Thermostat[0]["features"] and "batteryLevel" in HiveSession_Current.Nodes.Thermostat[0]["features"]["battery_device_v1"] and "displayValue" in HiveSession_Current.Nodes.Thermostat[0]["features"]["battery_device_v1"]["batteryLevel"]:
            Thermostat_BatteryLevel_tmp = HiveSession_Current.Nodes.Thermostat[0]["features"]["battery_device_v1"]["batteryLevel"]["displayValue"]
            Thermostat_BatteryLevel_Found = True
            
    if Thermostat_BatteryLevel_Found == True:
        Current_Node_Attribute_Values["Thermostat_BatteryLevel"] = Thermostat_BatteryLevel_tmp
        Thermostat_BatteryLevel_Return = Thermostat_BatteryLevel_tmp
    else:
        if "Thermostat_BatteryLevel" in Current_Node_Attribute_Values:
            Thermostat_BatteryLevel_Return = Current_Node_Attribute_Values.get("Thermostat_BatteryLevel")
        else:
            Thermostat_BatteryLevel_Return = 0
            
    return Thermostat_BatteryLevel_Return

def Private_Get_Light_State(NodeID):
    NodeIndex = -1
    
    Light_State_Return = "UNKNOWN"
    Light_State_tmp = "UNKNOWN"
    Light_State_Found = False
    
    if len(HiveSession_Current.Nodes.Light) > 0:
        for x in range(0, len(HiveSession_Current.Nodes.Light)):
            if "id" in HiveSession_Current.Nodes.Light[x]:
                if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "features" in HiveSession_Current.Nodes.Light[NodeIndex] and "on_off_device_v1" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"] and "mode" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"]["on_off_device_v1"]\
                    and "displayValue" in HiveSession_Current.Nodes.Light[NodeIndex]["features"]["on_off_device_v1"]["mode"]:

                Light_State_tmp = HiveSession_Current.Nodes.Light[NodeIndex]["features"]["on_off_device_v1"]["mode"]["displayValue"]
                Light_State_Found = True                    

    if Light_State_Found == True:
        Current_Node_Attribute_Values["Light_State_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]] = Light_State_tmp
        Light_State_Return = Light_State_tmp
    else:
        if ("Light_State_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
            Light_State_Return = Current_Node_Attribute_Values.get("Light_State_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"])
        else:
            Light_State_Return = "UNKNOWN"
            
            
    if Light_State_Return == "ON":
        return True
    else:
        return False

def Private_Get_Light_Brightness(NodeID):
    NodeIndex = -1
    Tmp_Brightness_Return = 0
    Light_Brightness_Return = 0
    Light_Brightness_tmp = 0
    Light_Brightness_Found = False

    if len(HiveSession_Current.Nodes.Light) > 0:
        for x in range(0, len(HiveSession_Current.Nodes.Light)):
            if "id" in HiveSession_Current.Nodes.Light[x]:
                if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break
                
                
        if NodeIndex != -1:
            if "features" in HiveSession_Current.Nodes.Light[NodeIndex] and "dimmable_light_v1" in \
                        HiveSession_Current.Nodes.Light[NodeIndex]["features"] and "brightness" in \
                        HiveSession_Current.Nodes.Light[NodeIndex]["features"]["dimmable_light_v1"]\
                        and "displayValue"in HiveSession_Current.Nodes.Light[NodeIndex]["features"]["dimmable_light_v1"]["brightness"]:
                    Light_Brightness_tmp = HiveSession_Current.Nodes.Light[NodeIndex]["features"]["dimmable_light_v1"]["brightness"]["displayValue"]
                    Light_Brightness_Found = True

            if Light_Brightness_Found == True:
                Current_Node_Attribute_Values["Light_Brightness_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]] = Light_Brightness_tmp
                Tmp_Brightness_Return = Light_Brightness_tmp
                Light_Brightness_Return = ((Tmp_Brightness_Return / 100) * 255)
            else:
                if ("Light_Brightness_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
                    Tmp_Brightness_Return = Current_Node_Attribute_Values.get("Light_Brightness_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"])
                    Light_Brightness_Return = ((Tmp_Brightness_Return / 100) * 255)
                else:
                    Light_Brightness_Return = 0

        return Light_Brightness_Return

def Private_Get_Light_Min_Color_Temp(NodeID):
    NodeIndex = -1
    Light_Min_Color_Temp_Tmp = 0
    Light_Min_Color_Temp_Return = 0
    Light_Min_Color_Temp_Found = False

    if len(HiveSession_Current.Nodes.Light) > 0:
        for x in range(0, len(HiveSession_Current.Nodes.Light)):
            if "id" in HiveSession_Current.Nodes.Light[x]:
                if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "features" in HiveSession_Current.Nodes.Light[NodeIndex] and "temperature_tunable_light_v1" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"] and "maxColourTemperature" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"] \
                    and "displayValue" in HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["maxColourTemperature"]:
                Light_Min_Color_Temp_Tmp = HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["maxColourTemperature"]["displayValue"]
                Light_Min_Color_Temp_Found = True


            if Light_Min_Color_Temp_Found == True:
                Current_Node_Attribute_Values["Light_Min_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]] = Light_Min_Color_Temp_Tmp
                Light_Min_Color_Temp_Return = round((1 / Light_Min_Color_Temp_Tmp) * 1000000)
            else:
                if ("Light_Min_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
                    Light_Min_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Min_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"])
                else:
                    Light_Min_Color_Temp_Return = 0

        return Light_Min_Color_Temp_Return

def Private_Get_Light_Max_Color_Temp(NodeID):
    NodeIndex = -1
    Light_Max_Color_Temp_Tmp = 0
    Light_Max_Color_Temp_Return = 0
    Light_Max_Color_Temp_Found = False

    if len(HiveSession_Current.Nodes.Light) > 0:
        for x in range(0, len(HiveSession_Current.Nodes.Light)):
            if "id" in HiveSession_Current.Nodes.Light[x]:
                if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "features" in HiveSession_Current.Nodes.Light[NodeIndex] and "temperature_tunable_light_v1" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"] and "minColourTemperature" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"] \
                    and "displayValue" in HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["minColourTemperature"]:
                Light_Max_Color_Temp_Tmp = HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["minColourTemperature"]["displayValue"]
                Light_Max_Color_Temp_Found = True

            if Light_Max_Color_Temp_Found == True:
                Current_Node_Attribute_Values["Light_Max_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]] = Light_Max_Color_Temp_Tmp
                Light_Max_Color_Temp_Return = round((1 / Light_Max_Color_Temp_Tmp) * 1000000)
            else:
                if ("Light_Max_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
                    Light_Max_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Max_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"])
                else:
                    Light_Max_Color_Temp_Return = 0

        return Light_Max_Color_Temp_Return

def Private_Get_Light_Color_Temp(NodeID):
    NodeIndex = -1
    Light_Color_Temp_Tmp = 0
    Light_Color_Temp_Return = 0
    Light_Color_Temp_Found = False

    if len(HiveSession_Current.Nodes.Light) > 0:
        for x in range(0, len(HiveSession_Current.Nodes.Light)):
            if "id" in HiveSession_Current.Nodes.Light[x]:
                if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                    NodeIndex = x
                    break

        if NodeIndex != -1:
            if "features" in HiveSession_Current.Nodes.Light[NodeIndex] and "temperature_tunable_light_v1" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"] and "colourTemperature" in \
                    HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"] \
                    and "displayValue" in HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["colourTemperature"]:
                Light_Color_Temp_Tmp = HiveSession_Current.Nodes.Light[NodeIndex]["features"]["temperature_tunable_light_v1"]["colourTemperature"]["displayValue"]
                Light_Color_Temp_Found = True

            if Light_Color_Temp_Found == True:
                Current_Node_Attribute_Values["Light_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]] = Light_Color_Temp_Tmp
                Light_Color_Temp_Return = round((1 / Light_Color_Temp_Tmp) * 1000000)
            else:
                if ("Light_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]) in Current_Node_Attribute_Values:
                    Light_Color_Temp_Return = Current_Node_Attribute_Values.get("Light_Color_Temp_" + HiveSession_Current.Nodes.Light[NodeIndex]["id"])
                else:
                    Light_Color_Temp_Return = 0

        return Light_Color_Temp_Return



def Hive_API_Get_Nodes_RL():
    CurrentTime = datetime.now()
    SecondsSinceLastUpdate = (CurrentTime - HiveSession_Current.LastUpdate).total_seconds()
    if SecondsSinceLastUpdate >= HiveSession_Current.Update_Interval_Seconds:
        HiveSession_Current.LastUpdate = CurrentTime
        Hive_API_Get_Nodes()

def Hive_API_Get_Nodes_NL():
    Hive_API_Get_Nodes()
    
def Hive_API_Get_Nodes():
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()
        
    if HiveSession_Current.SessionID != None:
        tmp_Hub = []
        tmp_Receiver = []
        tmp_Thermostat = []
        tmp_Heating = []
        tmp_HotWater = []
        tmp_Light = []

        API_Response_Nodes = Hive_API_JsonCall ("GET", HiveAPI_Details.URLs.Nodes, "6.5", "")

        try:
            HiveNodes_Parsed = json.loads(API_Response_Nodes.text)["nodes"]

            for aNode in HiveNodes_Parsed:
                if "nodeType" in aNode:
                    if aNode["nodeType"] == "http://alertme.com/schema/json/node.class.hub.json#":
                        tmp_Hub.append(aNode)
                    elif aNode["nodeType"] == "http://alertme.com/schema/json/node.class.thermostatui.json#":
                        if "features" in aNode:
                            if "heating_thermostat_v1" not in aNode["features"] and "water_heater_v1" not in aNode["features"]:
                                tmp_Thermostat.append(aNode)
                    elif aNode["nodeType"] == "http://alertme.com/schema/json/node.class.thermostat.json#":
                        if "features" in aNode:
                            if "heating_thermostat_v1" not in aNode["features"] and "water_heater_v1" not in aNode["features"]:
                                tmp_Receiver.append(aNode)
                            elif "heating_thermostat_v1" in aNode["features"] and "water_heater_v1" not in aNode["features"]:
                                tmp_Heating.append(aNode)
                            elif "heating_thermostat_v1" not in aNode["features"] and "water_heater_v1" in aNode["features"]:
                                tmp_HotWater.append(aNode)
                    elif aNode["nodeType"] == "http://alertme.com/schema/json/node.class.light.json#" or aNode["nodeType"] == "http://alertme.com/schema/json/node.class.tunable.light.json#":
                        tmp_Light.append(aNode)
            
                      
            if len(tmp_Hub) > 0:
                HiveSession_Current.Nodes.Hub = tmp_Hub
            if len(tmp_Receiver) > 0:
                HiveSession_Current.Nodes.Receiver = tmp_Receiver
            if len(tmp_Thermostat) > 0:
                HiveSession_Current.Nodes.Thermostat = tmp_Thermostat
            if len(tmp_Heating) > 0:
                HiveSession_Current.Nodes.Heating = tmp_Heating
            if len(tmp_HotWater) > 0:
                HiveSession_Current.Nodes.HotWater = tmp_HotWater
            if len(tmp_Light) > 0:
                HiveSession_Current.Nodes.Light = tmp_Light

        except:
            _LOGGER.error("Error parsing Hive nodes")
    else:
        _LOGGER.error("No Session ID")
        
        
def Private_Hive_API_Set_Temperature(NewTemperature):
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

    API_Response_SetTemperature = ""
    
    API_Response_SetTemperature_Parsed = None

    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Nodes.Heating) > 0:
            if "id" in HiveSession_Current.Nodes.Heating[0]:
                JsonStringContent = '{"nodes": [{"features": {"heating_thermostat_v1": {"targetHeatTemperature": {"targetValue": ' + str(NewTemperature) + '}}}}]}'
                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/" + HiveSession_Current.Nodes.Heating[0]["id"]
                API_Response_SetTemperature = Hive_API_JsonCall ("PUT", HiveAPI_URL, "6.5", JsonStringContent)
                API_Response_SetTemperature_Parsed = json.loads(API_Response_SetTemperature.text)["nodes"]
                    
    tmp_API_Response_SetTemperature = str(API_Response_SetTemperature)
     
    if tmp_API_Response_SetTemperature == "<Response [200]>":
        if len(HiveSession_Current.Nodes.Heating) > 0:
            HiveSession_Current.Nodes.Heating[0] = API_Response_SetTemperature_Parsed[0]
        return True
    else:
        return False

def Private_Hive_API_Set_Heating_Mode(NewMode):
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

    API_Response_SetMode_Parsed = None
    API_Response_SetMode = ""

    JsonStringContent = None
    
    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Nodes.Heating) > 0:
            if "id" in HiveSession_Current.Nodes.Heating[0]:
                if NewMode == "SCHEDULE":
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "ON"}},"heating_thermostat_v1": {"operatingMode": {"targetValue": "SCHEDULE"}}}}]}'
                elif NewMode == "MANUAL":
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "ON"}},"heating_thermostat_v1": {"operatingMode": {"targetValue": "MANUAL"}}}}]}'
                elif NewMode == "OFF":
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "OFF"}}}}]}'
                
                if NewMode == "SCHEDULE" or NewMode == "MANUAL" or NewMode == "OFF":
                    HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/" + HiveSession_Current.Nodes.Heating[0]["id"]
                    API_Response_SetMode = Hive_API_JsonCall ("PUT", HiveAPI_URL, "6.5", JsonStringContent)
                    if '"nodes"' in API_Response_SetMode.text:
                        API_Response_SetMode_Parsed = json.loads(API_Response_SetMode.text)["nodes"]
                    else:
                        API_Response_SetMode_Parsed = None
     
    tmp_API_Response_SetMode = str(API_Response_SetMode)
    
    if tmp_API_Response_SetMode == "<Response [200]>":
        if len(HiveSession_Current.Nodes.Heating) > 0 and API_Response_SetMode_Parsed != None:
            HiveSession_Current.Nodes.Heating[0] = API_Response_SetMode_Parsed[0]
        return True
    else:
        return False

def Private_Hive_API_Set_HotWater_Mode(NewMode):
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

    API_Response_SetMode_Parsed = None
    API_Response_SetMode = ""

    APIVersion = "6.5"
                    
    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Nodes.HotWater) > 0:
            if "id" in HiveSession_Current.Nodes.HotWater[0]:
                if NewMode == "SCHEDULE":
                    APIVersion = "6.5"
                    JsonStringContent = '{"nodes": [{"features": {"water_heater_v1": {"isOn": {"targetValue": "true"}},"water_heater_v1": {"operatingMode": {"targetValue": "SCHEDULE"}}}}]}'
                elif NewMode == "ON":
                    APIVersion = "6.5"
                    JsonStringContent = '{"nodes": [{"features": {"water_heater_v1": {"isOn": {"targetValue": "true"}},"water_heater_v1": {"operatingMode": {"targetValue": "ON"}}}}]}'
                elif NewMode == "OFF":
                    APIVersion = "6.1"
                    JsonStringContent = '{"nodes": [{"attributes": {"activeHeatCoolMode": {"targetValue": "OFF"},"activeScheduleLock": {"targetValue": false}}}]}'

                if NewMode == "SCHEDULE" or NewMode == "ON" or NewMode == "OFF":
                    HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/" + HiveSession_Current.Nodes.HotWater[0]["id"]
                    API_Response_SetMode = Hive_API_JsonCall ("PUT", HiveAPI_URL, APIVersion, JsonStringContent)
                    if '"nodes"' in API_Response_SetMode.text:
                        API_Response_SetMode_Parsed = json.loads(API_Response_SetMode.text)["nodes"]
                    else:
                        API_Response_SetMode_Parsed = None
     
    tmp_API_Response_SetMode = str(API_Response_SetMode)
    
    if tmp_API_Response_SetMode == "<Response [200]>":
        if APIVersion == "6.5":
            if len(HiveSession_Current.Nodes.HotWater) > 0 and API_Response_SetMode_Parsed != None:
                HiveSession_Current.Nodes.HotWater[0] = API_Response_SetMode_Parsed[0]
        elif APIVersion == "6.1":
            Hive_API_Get_Nodes_NL()
        return True
    else:
        return False
        
def Private_Hive_API_Set_Light_TurnON(NodeID, NewBrightness, NewColorTemp):
    NodeIndex = -1
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

    API_Response_SetMode_Parsed = None
    API_Response_SetMode = ""
    
    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Nodes.Light) > 0:
            for x in range(0, len(HiveSession_Current.Nodes.Light)):
                if "id" in HiveSession_Current.Nodes.Light[x]:
                    if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                if NewBrightness == None and NewColorTemp == None:
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "ON"}}}}]}'
                elif NewBrightness != None and NewColorTemp == None:
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "ON"}},"dimmable_light_v1": {"brightness": {"targetValue": ' + str(NewBrightness) + '}}}}]}'
                elif NewColorTemp != None and NewBrightness == None:
                    JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "ON"}},"temperature_tunable_light_v1": {"colourTemperature": {"targetValue": ' + str(NewColorTemp) + '}}}}]}'
#               elif NewRGBColor != None and NewColorTemp == None and NewBrightness == None:
#                    JsonStringContent = ''

                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]
                API_Response_SetMode = Hive_API_JsonCall("PUT", HiveAPI_URL, "6.5", JsonStringContent)
                API_Response_SetMode_Parsed = json.loads(API_Response_SetMode.text)["nodes"]

    tmp_API_Response_SetMode = str(API_Response_SetMode)

    if tmp_API_Response_SetMode == "<Response [200]>":
        if len(HiveSession_Current.Nodes.Light) > 0:
            HiveSession_Current.Nodes.Light[NodeIndex] = API_Response_SetMode_Parsed[0]

        return True
    else:
        return False

def Private_Hive_API_Set_Light_TurnOFF(NodeID):
    NodeIndex = -1
    CurrentTime = datetime.now()
    SecondsSinceLastLogon = (HiveSession_Current.Session_Logon_DateTime - CurrentTime).total_seconds()
    MinutesSinceLastLogon = int(round(SecondsSinceLastLogon / 60))

    if MinutesSinceLastLogon >= MINUTES_BETWEEN_LOGONS:
        Hive_API_Logon()
    elif HiveSession_Current.SessionID == None:
        Hive_API_Logon()

    API_Response_SetMode_Parsed = None
    API_Response_SetMode = ""

    if HiveSession_Current.SessionID != None:
        if len(HiveSession_Current.Nodes.Light) > 0:
            for x in range(0, len(HiveSession_Current.Nodes.Light)):
                if "id" in HiveSession_Current.Nodes.Light[x]:
                    if HiveSession_Current.Nodes.Light[x]["id"] == NodeID:
                        NodeIndex = x
                        break
            if NodeIndex != -1:
                JsonStringContent = '{"nodes": [{"features": {"on_off_device_v1": {"mode": {"targetValue": "OFF"}}}}]}'
                HiveAPI_URL = HiveAPI_Details.URLs.Nodes + "/" + HiveSession_Current.Nodes.Light[NodeIndex]["id"]
                API_Response_SetMode = Hive_API_JsonCall("PUT", HiveAPI_URL, "6.5", JsonStringContent)
                API_Response_SetMode_Parsed = json.loads(API_Response_SetMode.text)["nodes"]           
            
    tmp_API_Response_SetMode = str(API_Response_SetMode)

    if tmp_API_Response_SetMode == "<Response [200]>":
        if len(HiveSession_Current.Nodes.Light) > 0:
            HiveSession_Current.Nodes.Light[NodeIndex] = API_Response_SetMode_Parsed[0]

        return True
    else:
        return False
        

def setup(hass, config):
    """Setup the Hive platform"""
    HiveSession_Current.UserName = None
    HiveSession_Current.Password = None
    
    hive_config = config[DOMAIN]

    if "username" in hive_config and "password" in hive_config:
        HiveSession_Current.UserName = config[DOMAIN]['username']
        HiveSession_Current.Password = config[DOMAIN]['password']
    else:
        _LOGGER.error("Missing UserName or Password in config")
    
    if "minutes_between_updates" in hive_config:
        tmp_MINUTES_BETWEEN_UPDATES = config[DOMAIN]['minutes_between_updates']
    else:
        tmp_MINUTES_BETWEEN_UPDATES = 2
        
    Hive_Node_Update_Interval = tmp_MINUTES_BETWEEN_UPDATES * 60

    if HiveSession_Current.UserName is None or HiveSession_Current.Password is None:
        _LOGGER.error("Missing UserName or Password in Hive Session details")
    else:
        Initialise_App()
        Hive_API_Logon()
        if HiveSession_Current.SessionID != None:
            HiveSession_Current.Update_Interval_Seconds = Hive_Node_Update_Interval
            Hive_API_Get_Nodes_NL()

    ConfigDevices = []
    
    if "devices" in hive_config:
        ConfigDevices = config[DOMAIN]['devices']

    DEVICECOUNT = 0
        
    DeviceList_Sensor = []
    DeviceList_Climate = []
    DeviceList_Light = []
    
    if len(HiveSession_Current.Nodes.Heating) > 0:
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Climate.append("Hive_Device_Heating")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_currenttemperature" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Heating_CurrentTemperature")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_targettemperature" in ConfigDevices):    
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Heating_TargetTemperature")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_state" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Heating_State")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_mode" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Heating_Mode")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_heating_boost" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Heating_Boost")

    if len(HiveSession_Current.Nodes.HotWater) > 0:
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Climate.append("Hive_Device_HotWater")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_state" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_HotWater_State")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_mode" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_HotWater_Mode")
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_hotwater_boost" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_HotWater_Boost")

    if len(HiveSession_Current.Nodes.Thermostat) > 0:
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_thermostat_batterylevel" in ConfigDevices):
            DEVICECOUNT = DEVICECOUNT + 1
            DeviceList_Sensor.append("Hive_Device_Thermostat_BatteryLevel")
            
    if len(HiveSession_Current.Nodes.Light) > 0:
        if len(ConfigDevices) == 0 or (len(ConfigDevices) > 0 and "hive_active_light" in ConfigDevices):
            for aNode in HiveSession_Current.Nodes.Light:
                if "id" in aNode and "name" in aNode:
                    DEVICECOUNT = DEVICECOUNT + 1
                    if "nodeType" in aNode:
                        if aNode["nodeType"] == "http://alertme.com/schema/json/node.class.light.json#":
                            Hive_Light_DeviceType = "Dimmable"
                        elif aNode["nodeType"] == "http://alertme.com/schema/json/node.class.tunable.light.json#":
                            Hive_Light_DeviceType = "CoolToWarmWhite"
                        elif aNode["nodeType"] == "http://alertme.com/schema/json/node.class.colourchanging.light.json#":
                            ## Update nodeType to real value when known ##
                            Hive_Light_DeviceType = "ColourChanging"
                        else:
                            Hive_Light_DeviceType = "Dimmable"
                        
                    DeviceList_Light.append({'HA_DeviceType': 'Hive_Device_Light', 'Hive_Light_DeviceType': Hive_Light_DeviceType, 'Hive_NodeID': aNode["id"], 'Hive_NodeName': aNode["name"]})


    global HiveObjects_Global

    try:
        HiveObjects_Global = HiveObjects()
    except RuntimeError:
        return False
            
    if len(DeviceList_Sensor) > 0 or len(DeviceList_Climate) > 0 or len(DeviceList_Light) > 0:
        if len(DeviceList_Sensor) > 0:
            load_platform(hass, 'sensor', DOMAIN, DeviceList_Sensor)
        if len(DeviceList_Climate) > 0:
            load_platform(hass, 'climate', DOMAIN, DeviceList_Climate)
        if len(DeviceList_Light) > 0:
            load_platform(hass, 'light', DOMAIN, DeviceList_Light)
        return True


class HiveObjects():
    def __init__(self):
        """Initialize HiveObjects."""

    def UpdateData(self):
        Hive_API_Get_Nodes_RL()

    def Get_Heating_Min_Temperature(self):
        return Private_Get_Heating_Min_Temperature()

    def Get_Heating_Max_Temperature(self):
        return Private_Get_Heating_Max_Temperature()
        
    def Get_Heating_CurrentTemp(self):
        return Private_Get_Heating_CurrentTemp()
        
    def Get_Heating_CurrentTemp_State_Attributes(self):
        return Private_Get_Heating_CurrentTemp_State_Attributes()
        
    def Get_Heating_TargetTemp(self):
        return Private_Get_Heating_TargetTemp()
        
    def Get_Heating_TargetTemperature_State_Attributes(self):
        return Private_Get_Heating_TargetTemperature_State_Attributes()
        
    def Set_Heating_TargetTemp(self, NewTemperature):
        if NewTemperature is not None:
            SetTempResult = Private_Hive_API_Set_Temperature(NewTemperature)
        
    def Get_Heating_State(self):
        return Private_Get_Heating_State()
        
    def Get_Heating_State_State_Attributes(self):
        return Private_Get_Heating_State_State_Attributes()
        
    def Get_Heating_Mode(self):
        return Private_Get_Heating_Mode()
        
    def Set_Heating_Mode(self, NewOperationMode):
        SetModeResult = Private_Hive_API_Set_Heating_Mode(NewOperationMode)
        
    def Get_Heating_Mode_State_Attributes(self):
        return Private_Get_Heating_Mode_State_Attributes()
        
    def Get_Heating_Operation_Mode_List(self):
        return Private_Get_Heating_Operation_Mode_List()

    def Get_Heating_Boost(self):
        return Private_Get_Heating_Boost()
        
    def Get_Heating_Boost_State_Attributes(self):
        return Private_Get_Heating_Boost_State_Attributes()
        
    def Get_HotWater_State(self):
        return Private_Get_HotWater_State()
        
    def Get_HotWater_State_State_Attributes(self):
        return Private_Get_HotWater_State_State_Attributes()
        
    def Get_HotWater_Mode(self):
        return Private_Get_HotWater_Mode()
        
    def Get_HotWater_Mode_State_Attributes(self):
        return Private_Get_HotWater_Mode_State_Attributes()
        
    def Set_HotWater_Mode(self, NewOperationMode):
        SetModeResult = Private_Hive_API_Set_HotWater_Mode(NewOperationMode)
        
    def Get_HotWater_Operation_Mode_List(self):
        return Private_Get_HotWater_Operation_Mode_List()
        
    def Get_HotWater_Boost(self):
        return Private_Get_HotWater_Boost()
        
    def Get_HotWater_Boost_State_Attributes(self):
        return Private_Get_HotWater_Boost_State_Attributes()
        
    def Get_Thermostat_BatteryLevel(self):
        return Private_Get_Thermostat_BatteryLevel()
        
    def Get_Light_State(self, NodeID):
        return Private_Get_Light_State(NodeID)

    def Get_Light_Brightness(self, NodeID):
        return Private_Get_Light_Brightness(NodeID)

    def Get_Light_Color_Temp(self, NodeID):
        return Private_Get_Light_Color_Temp(NodeID)

    def Get_Light_Min_Color_Temp(self, NodeID):
        return Private_Get_Light_Min_Color_Temp(NodeID)

    def Get_Light_Max_Color_Temp(self, NodeID):
        return Private_Get_Light_Max_Color_Temp(NodeID)

    def Set_Light_TurnON(self, NodeID, NewBrightness, NewColorTemp):
        SetModeResult =  Private_Hive_API_Set_Light_TurnON(NodeID, NewBrightness, NewColorTemp)

    def Set_Light_TurnOFF(self, NodeID):
        return Private_Hive_API_Set_Light_TurnOFF(NodeID)
        