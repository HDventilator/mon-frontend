"""
InfluxDB connector
Todos:
- use continious query to downsample data?
- call client.close() on exit
"""
# pylint: disable=bad-continuation

import logging
import copy
import os
import time
from typing import Dict, Iterable, Optional

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))


def _convert_timestr(datapt):
    """
    Convert the `time` value of the given influx data point from an absolute timestamp
    in nanoseconds to relative (to now()) time
    """
    datapt_mod = copy.copy(datapt)
    # replace timestamp with relative time in seconds
    now = time.time_ns()
    datapt_mod["time"] = (datapt_mod["time"] - now) / 1_000_000_000
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
        query_result = client.query(query_str, epoch="ns")
        yield from map(_convert_timestr, query_result.get_points())
