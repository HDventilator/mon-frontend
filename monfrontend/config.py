"""
Main configuration file for UI

Notes:
    alarms:
    if attached to measurement: color field
    if not attached to measurement: show somewhere else

    identifier: 6 chars total: two chars type, 4 chars id
    type:
      - 'Pv####' = "parameter,value"
      - 'P^####' = "parameter,maximum"
      - 'P_####' = "parameter,minimum"
      - 'DM####' = "DiagnosticMeasurement" -> messwert
      - 'AM####' = (alarm)?
      - ??       = (breathing mode)?

    open questions:
     - stick with .py file, or use YAML?
        - our mapping are quite simple, mostly lists and a dict or two - would be a good fit for YAML
     - do we need instant feedback in the UI when changing parameters (during value
       setting) or is it enough to show the new value when it is confirmed?
     - min/max values for user setting parameters and alarm limits: how to store
       permanently (in influx?)
     - config validation (type check)?
"""

##################
# DISPLAY VALUES
##################

# measurements to show live time-series plots
# List[str]
PLOT_MEASUREMENTS = ["DMpres"]

# measurements to show in box column on right side
# List[str]
SIDE_BAR_MEASUREMENTS = ["DMpres"]

# measurements to show in bottom bar, depending on the current mode
# key = mode identifier
# Dict[str, List[str]]
BOTTOM_BAR_MEASUREMENTS = {"debug": ["DMpres"]}

##################
# METAINFO MAPPINGS
##################

# metainformation for diagnostic measurements
# Dict[str, Dict[str, str]]
MEASUREMENTS_META = {"DMpres": {"display_name": "Pressure", "unit": "mBar"}}

# metainformation for user-set parameters
# Dict[str, Dict[str, str]]
PARAMETERS_META = {"Pv####": {"display_name": "My pressure setpoint", "unit": "mBar"}}

# metainformation for alarms
# Dict[str, Dict[str, str]]
# value_assoc = optional association to a measurement value identifier, to color the appropriate display box green/red
#               set to None for no association
ALARMS_META = {
    "AM####": {
        "display_name": "Program Alarm",
        "message": "The sky is falling!",
        "value_assoc": "DMpres",
    },
    "AMasdf": {
        "display_name": "Alarm 2",
        "message": "The sky is falling again!",
        "value_assoc": None,
    },
}
