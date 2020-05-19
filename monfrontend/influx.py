"""
InfluxDB connector
Todos:
- use continious query to downsample data?
- call client.close() on exit
"""
# pylint: disable=bad-continuation

import time
from typing import Dict, Iterable, Optional

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError


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
            print("InfluxDB client error")
        self._client = client
        return client

    def get_measurements(self) -> Iterable[str]:
        """
        Get available measurements
        """
        client = self._get_client()
        return [m["name"] for m in client.get_list_measurements()]

    def get_data(
        self,
        measurement: str,
        duration: str = "30s",
        fields: Optional[str] = None,
        groupby_time: str = "100ms",
    ) -> Iterable[Dict]:
        """
        Get data for the given measurement from InfluxDB. By default, gets all
        fields and tags. Timestamps are returned relative to now() in seconds.
        Pass in a value for `field` to get only certain fields, e.g.
        `field="value,type"` (`time` is always included).
        """
        if not fields:
            fields = "*"
        query_str = f"SELECT MEAN({fields})FROM {measurement} WHERE time > now()-{duration} GROUP BY time({groupby_time}) FILL(none)"  # pylint: disable=line-too-long
        client = self._get_client()
        now = time.time_ns()
        query_result = client.query(query_str, epoch="ns")
        for datapt in query_result.get_points():
            # replace timestamp with relative time in seconds
            datapt["time"] = (datapt["time"] - now) / 1_000_000_000
            yield datapt
