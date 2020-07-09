from enum import Enum
from typing import Optional

from monfrontend.components.config import MEASUREMENTS_META, PARAMETERS_META, ALARMS_META

MetaType = Enum("MetaType", "MEASUREMENT, PARAMETER, ALARM")


def get_metainfo(meta_type: MetaType, identifier: str, key: str) -> Optional[str]:
    """
    Retrieve metainfo `key` (e.g. "display_name" for the measurement identified
    by `identifer` (e.g. "dpFLOW")
    """
    try:
        if meta_type == MetaType.MEASUREMENT:
            return MEASUREMENTS_META[identifier][key]
        if meta_type == MetaType.PARAMETER:
            return PARAMETERS_META[identifier][key]
        if meta_type == MetaType.ALARM:
            return ALARMS_META[identifier][key]
    except KeyError:
        pass
    return None