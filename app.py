# Import the dependencies.
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct

import datetime as dt

from flask import Flask, jsonify

import numpy as np
#################################################
# Database Setup
#################################################
# Create Engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
# session = Session(engine)
# Shouldn't I create each session under each app route?

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def _index():
    """List all available api routes."""
    return (
        f"Available Routes for Hawaii Weather Data:"
        f"-- Query Daily Precipitation for the past 12 Months: --"
        f"/api/v1.0/precipitation"
        f"-- Query All Available Weather Stations: --"
        f"/api/v1.0/stations"
        f"-- Query Daily Temperature Observations for USC00519281 for the past 12 Months: -- "
        f"/api/v1.0/tobs"
        f"-- Query Min, Average & Max Temperatures for Date Range: --"
        f"/api/v1.0/<start>"
        f"/api/v1.0/<start>/<end>"
        f"If no end-date is provided, the trip api calculates stats through 08/23/17"
    )

@app.route('/api/v1.0/precipitation')
def get_precipitation():
    # Create DT object referencing date 1 year ago
    date_start = '2017-08-23'
    # Initialize Session, terminate Session
    session = Session(bind=engine)
    sel = [Measurement.date,
           func.sum(Measurement.prcp)]
    query = session.query(*sel). \
        filter(Measurement.date > date_start). \
        group_by(Measurement.date).\
        order_by(Measurement.date.desc()).all()
    session.close()

    # Prepare payload
    payload = []
    for date, precipitation in query:
        data = {}
        data['date'] = date
        data['prcp'] = precipitation
        payload.append(data)

    return jsonify(payload)
@app.route('/api/v1.0/stations')
def get_stations():
    # Initialize session, terminate session
    session = Session(bind=engine)
    sel = [Measurement.station]
    query = session.query(*sel).distinct().\
        order_by(Measurement.station)
    session.close()

    # Prepare payload
    payload = []
    for station in query:
        data = {}
        data['station'] = station
        payload.append(data)

    return jsonify(payload)
@app.route('/api/v1.0/tobs')
def get_tobs():
    # Initialize session, terminate session
    session = Session(bind=engine)
    # Get most active station
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station)). \
        group_by(Measurement.station). \
        order_by(func.count(Measurement.station).desc()).first()[0][0]
    # Filter by most active station
    sel = [Measurement.station,
           Measurement.date,
           Measurement.tobs]
    top_weather_station = session.query(*sel). \
        filter(func.strftime((Measurement.date) > date_12_months_ago),
               (Measurement.station == most_active_stations[0][0])).all()
    session.close()
# Prepare payload
    payload = []
    for station, date, tobs in query:
        data = {}
        data['station'] = station
        data['date'] = date
        data['tobs'] = tobs
        payload.append(data)

    return jsonify(payload)

@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def get_temps_range(date_start, date_end='2017-08-23'):
    # Initialize session, terminate session
    session = Session(bind=engine)
    sel = [Measurement.station,
           func.min(Measurement.date),
           func.max(Measurement.date),
           func.min(Measurement.tobs),
           func.max(Measurement.tobs),
           func.round(func.avg(Measurement.tobs), 2)]
    top_weather_station_summary= session.query(*sel). \
        filter(func.strftime(Measurement.date) > date_start, ). \
        group_by(Measurement.station).all()

    session.close()

# Specified port for MacOS Sonoma on ARM
if __name__ == '__main__':
    app.run(debug=True, port=5002)