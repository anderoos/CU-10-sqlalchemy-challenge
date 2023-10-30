# Import the dependencies.
# import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

from flask import Flask, jsonify

# import numpy as np
#################################################
# Database Setup
#################################################
# Create Engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()


# reflect the tables
# Reflect param in prepare is depreciated in SQLAlchemy 2.0
# Base.prepare(autoload_with=engine, reflect=True)
Base.prepare(autoload_with=engine)

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
def index():
    """List all available api routes."""
    return (
        f"Available Routes for Hawaii Weather Data:\n"
        f"-- Query Daily Precipitation for the past 12 Months: --\n"
        f"/api/v1.0/precipitation\n"
        f"-- Query All Available Weather Stations: --\n"
        f"/api/v1.0/stations\n"    # Corrected inconsistent formatting 
        f"-- Query Daily Temperature Observations for USC00519281 for the past 12 Months: -- \n"
        f"/api/v1.0/tobs\n"    # Corrected inconsistent formatting 
        f"-- Query Min, Average & Max Temperatures for Date Range: -- \n"
        f"/api/v1.0/<start> \n"
        f"/api/v1.0/<start>/<end> \n"
        f"NOTE: <start> and <end> accepts dates formatted as YYYY-MM-DD or YYYY/MM/DD \n" # Added instructions on how to format dynamic endpoints.
        f"If no end-date is provided, the trip api calculates stats through 2017-08-23 \n" # Corrected formatting issues
    )


@app.route('/api/v1.0/precipitation')
def get_precipitation():
    # Create DT object referencing date 1 year ago
    date_start = '2017-08-23'
    date_12_months_ago = dt.datetime.strptime(date_start, "%Y-%m-%d") - dt.timedelta(days=365)
    # Initialize Session, terminate Session
    session = Session(bind=engine)
    sel = [Measurement.date,
           func.sum(Measurement.prcp)]
    query = session.query(*sel). \
        filter(Measurement.date > date_12_months_ago). \     # Changed date_start to date_12_months_ago
        group_by(Measurement.date).\
        order_by(Measurement.date.desc()).all()
    session.close()

    # Prepare payload
    payload = []
    for date, precipitation in query:
        data = {'date': date, 'prcp': precipitation}
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
        data = {'station': station[0]}
        payload.append(data)

    return jsonify(payload)


@app.route('/api/v1.0/tobs')
def get_tobs():
    # Initialize session, terminate session
    session = Session(bind=engine)
    # Get most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)). \
        group_by(Measurement.station). \
        order_by(func.count(Measurement.station).desc()).first()[0]
    date_start = '2017-08-23'
    date_12_months_ago = dt.datetime.strptime(date_start, "%Y-%m-%d") - dt.timedelta(days=365)
    # Filter by most active station
    sel = [Measurement.station,
           Measurement.date,
           Measurement.tobs]
    query = session.query(*sel). \
        filter(Measurement.date > date_12_months_ago,
               Measurement.station == most_active_station).all()
    session.close()
# Prepare payload
    payload = []
    for station, date, tobs in query:
        data = {'station': station, 'date': date, 'tobs': tobs}
        payload.append(data)

    return jsonify(payload)


@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def get_temps_range(start, end='2017-08-23'):
    # Added try and except clauses.
    # Initialize session, terminate session
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")     # Convert to datetime object
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")     # Convert to datetime object
    except ValueError:
        print("Date formatted incorrectly. Check that your date is formatted as YYYY-MM-DD")

    # Continue if no exception raised
        session = Session(bind=engine)
        sel = [Measurement.station,
               func.min(Measurement.date),
               func.max(Measurement.date),
               func.min(Measurement.tobs),
               func.max(Measurement.tobs),
               func.round(func.avg(Measurement.tobs), 2)]
        query = session.query(*sel). \
            filter(Measurement.date) >= start_date),     # Removed redundant func.strftime function
                   (Measurement.date) <= end_date)).\     # Removed redundant func.strftime function
            group_by(Measurement.station).all()
        session.close()
    
        # Prepare payload
        payload = []
        for station, date_min, date_max, tob_min, tob_max, tob_avg in query:
            data = {'station': station,
                    'date_start': date_min,
                    'date_end': date_max,
                    'min_percip': tob_min,
                    'max_percip': tob_max,
                    'avg_percip': tob_avg
                    }
            payload.append(data)
        return jsonify(payload)

# Specified port for MacOSX Sonoma on ARM
if __name__ == '__main__':
    app.run(debug=True, port=5007)



