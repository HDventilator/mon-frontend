# HDvent Frontend

[![Build Status](https://travis-ci.org/HDventilator/mon-frontend.svg?branch=master)](https://travis-ci.org/HDventilator/mon-frontend)

This is a front end for displaying data from an InfluxDB database, tailored to be used as a monitor for a ventilator. It is based on Plotly/Dash with a primary goal being easy extension and modification.

![Screenshot](/screenshot.png)

## Configuration

### Application Configuration

Basic configuration is through environment variables:

```shell
# database host
INFLUXDB_HOST=localhost
# database port
INFLUXDB_PORT=8086
# influxdb database name
INFLUXDB_DATABASE=default
# data update interval in seconds
GRAPH_UPDATE_INTERVAL_SECONDS=1.0
```

### UI Configuration

TODO

## Starting UI in Development Mode

```shell
# setup virtual env
python3 -m venv venv
pip install --upgrade pip wheel

# install dependencies
pip install -r requirements-dev.txt

# load venv and start app
source ./venv/bin/activate
python3 -m monfrontend
```

## Installing / Starting in Production Mode

```shell
# install dependencies
pip install -r requirements.txt
# install monfrontend package
pip install .
# run with gunicorn
gunicorn -b 0.0.0.0:8050 "monfrontend:get_server()"
```
