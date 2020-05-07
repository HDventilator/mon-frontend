# -*- coding: utf-8 -*-
"""
Continously writes test data to the specified influxdb database
"""

import os
import random
import time
from datetime import datetime, timezone
from typing import Optional

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError

INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "influxdb")
INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", 8086)

WRITE_INTERVAL = os.environ.get("WRITE_INTERVAL", 20)
DATABASE_NAME = os.environ.get("DATABASE_NAME", "testdata")

# test fields and range for random value generation
MEASUREMENTS = ["pressure", "flow", "volume"]


def writeloop(client):
    """
    Infinite loop to write data to influxdb
    """
    last_value = [1.0 for m in MEASUREMENTS]
    while True:
        time.sleep(float(WRITE_INTERVAL) / 1000)
        data = []

        # timestamp is in milliseconds
        timestamp = datetime.now(timezone.utc).timestamp() * 1000

        for i, measurement_name in enumerate(MEASUREMENTS):
            # randomly generate next value
            value = last_value[i] + last_value[i] * random.uniform(-0.01, 0.01)
            last_value[i] = value
            # add influxdb line protocol line to data
            data.append(
                f"{measurement_name},type=test value={value:.3f} {timestamp:.0f}"
            )

        try:
            client.write_points(
                data,
                database=DATABASE_NAME,
                time_precision="ms",
                batch_size=10,
                protocol="line",
            )
        except InfluxDBServerError as e:
            print(e)


def connect_client(max_tries: int = 30) -> Optional[InfluxDBClient]:
    """
    Connect/retry logic. Returns a working InfluxDBClient if successfull.
    """
    client = None
    tries = 0
    while tries < max_tries:
        try:
            tries += 1
            print(f"Connecting... (attempt {tries}/{max_tries})")
            client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT)
        except ConnectionError:
            print(
                f"Could not connect to influxdb database \
                {DATABASE_NAME} @ {INFLUXDB_HOST}:{INFLUXDB_PORT}..."
            )
            print("Retrying in one second...")
            time.sleep(1.0)
            continue
        break
    return client


if __name__ == "__main__":
    print("Starting...")
    iflx_client = connect_client()  # pylint: disable=invalid-name
    if iflx_client is not None:
        iflx_client.drop_database(DATABASE_NAME)
        iflx_client.create_database(DATABASE_NAME)
        writeloop(iflx_client)
    print("Exited.")
