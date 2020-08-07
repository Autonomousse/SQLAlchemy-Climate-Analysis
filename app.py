'''---------------------'''
''' Import dependencies '''
'''---------------------'''
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

from flask import Flask, jsonify

'''----------------'''
''' Database Setup '''
'''----------------'''
engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

# Reflect the existing database and tables into new models
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create and save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

# First get the most current date in the data by querying date column in the Measurement table
most_current = session.query(func.max(Measurement.date)).first()

# Split the date into a list of strings in the following format: [yyyy,mm,dd]
last_date = most_current[0].split('-')

# Calculate the date 1 year ago by subtracting 365 days from the most current date
one_year = dt.date(int(last_date[0]), int(last_date[1]), int(last_date[2])) - dt.timedelta(days=365)

# Close the session
session.close()

'''-------------'''
''' Flask Setup '''
'''-------------'''
app = Flask(__name__)

# Create Flask Routes

'''------'''
''' HOME '''
'''------'''

# Main page or Home page, describes the different routes
@app.route("/")
def home():
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Home' page...")
    return (
        f"<br><h3>Available Routes and Usage Instructions Below:</h3>"
        f"<ul><li><strong>/api/v1.0/precipitation</strong> - List of Dates and Precipitation (inches) values.</li><br>"
        f"<li><strong>/api/v1.0/stations</strong> - List of Stations.</li><br>"
        f"<li><strong>/api/v1.0/tobs</strong> - List of Dates and Temperature (F) from the last year for the most active station</li><br>"
        f"<li><strong>/api/v1.0/<code>&lt;start&gt;</code></strong> - List of minimum, average, and maximum Temperature (F) for all dates greater than and equal to the start date provided. <em>Date must be in the format YYYY-MM-DD</em></li><br>"
        f"<li><strong>/api/v1.0/<code>&lt;start&gt;/&lt;end&gt;</code></strong> - List of minimum, average, and maximum Temperature (F) for dates between the start and end date provided (inclusive). <em>Date must be in the format YYYY-MM-DD</em></li>"
    )

'''---------------'''
''' PRECIPITATION '''
'''---------------'''

# Precipitation page. Queries and displays all the dates and precipitation for the last year in a dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Precipitation' page...")

    # Create a session (link) from Python to the DB
    session = Session(engine)

    # Create a query to return the date and precipitation for the last year
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year).all()

    # Close the session after we retreive the data
    session.close()

    # Create a dictionary from the row data
    precipitation_dict = {}
    for date, prcp in results:
        precipitation_dict.update({date:prcp})

    # jsonify the dictionary and return it
    return jsonify(precipitation_dict)

'''----------'''
''' STATIONS '''
'''----------'''

# Stations page. Queries and displays a list of all the stations.
@app.route("/api/v1.0/stations")
def stations():
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Station' page...")

     # Create a session (link) from Python to the DB
    session = Session(engine)

    # Create a query to return all of the stations in the database
    results = session.query(Station.station)

    # Close the session after we retreive the data
    session.close()

    # Create a list from the row data
    stations_list = [station[0] for station in results]

    # jsonify the list and return it
    return jsonify(stations_list)

'''------'''
''' TOBS '''
'''------'''

# TOBS page. Queries and displays a list of temperature observations, including the date.
@app.route("/api/v1.0/tobs")
def tobs():
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Station' page...")

     # Create a session (link) from Python to the DB
    session = Session(engine)

    # List the stations and the counts in descending order.
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()

    # Create a query to return all of the dates and temperature observations during the last year in the database
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == active_stations[0][0]).\
        filter(Measurement.date >= one_year)

    tobs_list = [date_tobs[0] for date_tobs in results]

    return jsonify(tobs_list)

# This code will allow the app to run and show debug errors
if __name__ == "__main__":
    app.run(debug=True)


