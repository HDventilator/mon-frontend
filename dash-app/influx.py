"""
InfluxDB connector
Todos:
- use continious query to downsample data?
- call client.close() on exit
"""
# pylint: disable=bad-continuation

import os
import logging
import copy
from datetime import datetime, timezone

from typing import Optional, Iterable, Dict

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))


def _convert_timestr(datapt):
    """
    Convert the `time` value of the given influx data point from a timestamp
    string to a python datetime object with timezone information.
    """
    time_string = datapt["time"]
    if "." not in time_string:
        influx_ts_format = "%Y-%m-%dT%H:%M:%SZ"
    else:
        influx_ts_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    datapt_mod = copy.copy(datapt)
    try:
        timestamp = datetime.strptime(datapt["time"], influx_ts_format)
    except KeyError:
        # no time field in datapt
        pass
    except ValueError:
        # error parsing, return as is
        logger.warning(
            "Error converting string timestamp to datetime, passing on as-is."
        )
        return datapt

    # add UTC timezone information
    datapt_mod["time"] = timestamp.astimezone(timezone.utc)

    # replace y-data with relative time
    now = datetime.now(timezone.utc)
    datapt_mod["time"] = (datapt_mod["time"] - now).total_seconds()

    return datapt_mod


class Influx:
    """
    InfluxDB connector class
    """

    def __init__(self, host: str, database: str, port=8086):
        self._host: str = host
        self._database: str = database
        self._port: int = port
        self._client: Optional[InfluxDBClient] = None

    def _get_client(self) -> InfluxDBClient:
        """
        Returns InfluxDB client object
        """
        if self._client is not None:
            return self._client

        try:
            client = InfluxDBClient(
                host=self._host, port=self._port, database=self._database,
            )
        except InfluxDBClientError:
            logger.exception("InfluxDB client error")
        self._client = client
        return client

    def get_measurements(self) -> Iterable[str]:
        """
        Get available measurements
        """
        client = self._get_client()
        return [m["name"] for m in client.get_list_measurements()]

    def get_data(
        self, measurement: str, duration: str = "30s", fields: Optional[str] = None
    ) -> Iterable[Dict]:
        """
        Get data for the given measurement from InfluxDB. By default, gets all
        fields and tags.  Converts string timestamps to UTC datetimes on the
        fly.  Pass in a value for `field` to get only certain fields, e.g.
        `field="value,type"` (`time` is always included).
        """
        if not fields:
            fields = "*"
        query_str = f"SELECT {fields} FROM {measurement} WHERE time > now()-{duration}"
        # logger.debug("query: %s", query_str)
        client = self._get_client()
        query_result = client.query(query_str)
        yield from map(_convert_timestr, query_result.get_points())
