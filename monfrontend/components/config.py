"""
Main configuration file for UI

Notes:
    alarms:
    if attached to measurement: color field
    if not attached to measurement: show somewhere else

    identifier: 6 chars total: two chars type, 4 chars id
    type:
      - 'Pv####' = "parameter,value"
      - 'PM####' = "parameter,maximum"
      - 'P_####' = "parameter,minimum"
      - 'DM####' = "DiagnosticMeasurement" -> messwert
      - 'AM####' = (alarm)?
      - 'VM'       = ventilation mode

    open questions:
     - stick with .py file, or use YAML?
        - our mapping are quite simple, mostly lists and a dict or two - would be a good fit for YAML
     - do we need instant feedback in the UI when changing parameters (during value
       setting) or is it enough to show the new value when it is confirmed?
     - min/max values for user setting parameters and alarm limits: how to store
       permanently (in influx?)
     - config validation (type check)?
     - does the sidebar only show measurements, and the bottom bar only parameters?!
"""

##################
# DISPLAY VALUES
##################

# measurements to show live time-series plots
# List[str]
PLOT_MEASUREMENTS = {"DMpins": dict(color='rgb(101, 251, 151)', fillcolor='rgba(101, 251, 151,0.2)'),
                     "DMflow": dict(color='rgb(101, 251, 251)', fillcolor='rgba(101, 251, 251,0.2)'),
                     "DMcvol": dict(color='rgb(176, 101, 251)', fillcolor='rgba(176, 101, 251,0.2)')}

# measurements to show in box column on right side
# List[str]
SIDE_BAR_MEASUREMENTS = ["DMpeep", "DMflow", "DMtvol"]  # , "DMmvol"]

# user-set parameters to show in bottom bar, depending on the current mode
# key = mode identifier
# Dict[str, List[str]]
BOTTOM_BAR_MEASUREMENTS = {"debug": ["PvVolu", "PvT_in", "Pvfreq"]}

##################
# METAINFO MAPPINGS
##################

# metainformation for diagnostic measurements
# Dict[str, Dict[str, str]]
MEASUREMENTS_META = {"DMpins": {"display_name": "Insp. Pressure", "unit": "mBar", "range": [0, 60], "min_key": "Dlpins",
                                "max_key": "Dhpins",
                                "low_alarm_key": "LApins", "high_alarm_key": "HApins", "alarm_set_key": "SApins"},
                     "DMflow": {"display_name": "Flow", "unit": "mL", "range": [-400, 400],
                                "low_alarm_key": "LAflow", "high_alarm_key": "HAflow", "alarm_set_key": "SAflow"},
                     "DMcvol": {"display_name": "Volume", "unit": "mL", "range": [0, 700],
                                "low_alarm_key": "LAcvol", "high_alarm_key": "HAcvol", "alarm_set_key": "SAcvol"},
                     "DMpeep": {"display_name": "PEEP", "unit": "mBar", "range": [0, 60],
                                "low_alarm_key": "LApeep", "high_alarm_key": "HApeep", "alarm_set_key": "SApeep"},
                     "DMmvol": {"display_name": "Minute Volume", "unit": "L", "range": [0, 10],
                                "low_alarm_key": "LAmvol", "high_alarm_key": "HAmvol", "alarm_set_key": "SAmvol"},
                     "DMtvol": {"display_name": "Tidal Volume", "unit": "mL", "range": [0, 800],
                                "low_alarm_key": "LAtvol", "high_alarm_key": "HAtvol", "alarm_set_key": "SAtvol"},
                     "DMfreq": {"display_name": "f", "unit": "/min", "range": [0, 30],
                                "low_alarm_key": "LAfreq", "high_alarm_key": "HAfreq", "alarm_set_key": "SAfreq"},
                     "DMvtid": {"display_name": "Vtidal", "unit": "mL", "range": [0, 60],
                                "low_alarm_key": "LAvtid", "high_alarm_key": "HAvtid", "alarm_set_key": "SAvtid"}
                     }

# metainformation for user-set parameters
# Dict[str, Dict[str, str]]
PARAMETERS_META = {"PvVolu": {"display_name": "Volume", "unit": "%", "total_range": [0, 100], "min_key": "P_Volu",
                              "max_key": "PMVolu"},
                   "PvT_in": {"display_name": "T_in", "unit": "s", "total_range": [0, 5], "min_key": "P_T_in",
                              "max_key": "PMT_in"},
                   "Pvfreq": {"display_name": "f", "unit": "/min", "total_range": [5, 35], "min_key": "P_freq",
                              "max_key": "PMfreq"},
                   }

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
