'''---------------------'''
''' Import dependencies '''
'''---------------------'''
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
import dateutil.parser as dp

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

# Find the earliest date available
oldest = session.query(func.min(Measurement.date)).first()

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
        f"<ul><li><strong>/api/v1.0/precipitation</strong> - List of Dates and Precipitation values (inches).</li><br>"
        f"<li><strong>/api/v1.0/stations</strong> - List of Stations.</li><br>"
        f"<li><strong>/api/v1.0/tobs</strong> - List of Dates and Temperature (F) from the last year for the most active station.</li><br>"
        f"<li><strong>/api/v1.0/<code>&lt;start&gt;</code></strong> - List of minimum, average, and maximum Temperature (F) for dates greater than and equal to the start date provided. <em>Date must be in the format YYYY-MM-DD and between {oldest[0]} and {most_current[0]}.</em></li><br>"
        f"<li><strong>/api/v1.0/<code>&lt;start&gt;/&lt;end&gt;</code></strong> - List of minimum, average, and maximum Temperature (F) for dates between the start and end date provided (inclusive). <em>Date must be in the format YYYY-MM-DD and between {oldest[0]} and {most_current[0]}.</em></li>"
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
        filter(Measurement.date >= one_year).\
            order_by(Measurement.date).all()

    # Insert an extra fake day to the query to make sure we loop through and collect data for the last day below
    one_more_day = (dt.datetime.strptime(most_current[0], '%Y-%m-%d') + dt.timedelta(days=1)).strftime('%Y-%m-%d')

    # Append the fake day we created in a list with a fake prcp value
    results.append([one_more_day,0.0])

    # Close the session after we retreive the data
    session.close()

    # Create a a list with a dictionary from the row data using dictionary comprehension
    #precipitation_list = [{date:prcp for (date,prcp) in results}]

    # Create a list with dictionaries that have the date as the key and a list of values where the values are the prcp amounts from each station.
    # The list is only for the last year of data. This method produces a cleaner output than a massive list.

    # Create lists an a dictionary, format the starting date to string format
    precipitation_list = []
    value_list = []
    rain_dict = {}
    starting = one_year.strftime('%Y-%m-%d')

    # Loop through the unpacked query results
    for date, prcp in results: 

        # If the current date is the same as the previous date, append the prcp amount to the list for the previous date      
        if date == starting:
            value_list.append(prcp)

        # If the current date is different...
        elif date != starting:

            # create a dictionary with the date as the key and the list of prcp amounts as the value
            rain_dict[starting] = value_list

            # Add the dictionary to the list we will return
            precipitation_list.append(rain_dict)

            # Clear the list holding the prcp amounts so we can start adding the next dates prcp amounts to it
            value_list = []

            # Since we are on the next date already, we have to append the prcp amount before moving on
            value_list.append(prcp)

            # Set the starting date to be the current date
            starting = date

            # Create a new dictionary for the next date and prcp amounts key:value pair
            rain_dict = {}

    # jsonify the dictionary and return it
    return jsonify(precipitation_list)

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
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == active_stations[0][0]).\
        filter(Measurement.date >= one_year)
    
    # Close the session after we retreive the data
    session.close()

    # Create a a list with a dictionary from the row data using dictionary comprehension
    tobs_list = [{date:tobs for (date,tobs) in results}]
    
    # jsonify the list and return it
    return jsonify(tobs_list)

'''------------'''
''' START DATE '''
'''------------'''

# Start Date page. Queries and displays a list of min, avg, and max temperatures for all dates greater than and equal to the start date.
@app.route("/api/v1.0/<start>")
def start_date(start):
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Start Date' page...")

    # The date util parser will automatically detect the date format entered then we convert it to YYYY-MM-DD
    entered_date = dp.parse(start)
    date_object = dt.datetime.strptime(str(entered_date), "%Y-%m-%d %H:%M:%S")
    cleaned_date = date_object.strftime("%Y-%m-%d")
    
     # Create a session (link) from Python to the DB
    session = Session(engine)

    # First create a list of all the dates we have data for
    search_start = session.query(Measurement.date)
    search_list = [np.ravel(value) for value in search_start]
  
    # Loop through the data
    for search_date in search_list:

        # Check to see if the date the user is searching for exists in the data
        if search_date == cleaned_date:

            # Create a selection to pass into the query containing all search parameters
            min_avg_max = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

            # Write out the query, unpack the selection from above, and filter for the start date
            results = session.query(*min_avg_max).\
                filter(Measurement.date >= cleaned_date)
            
            # Close the session after we retreive the data
            session.close()

            # Create a list of dictionaries to hold all the data and return it as a jsonified object
            temp_list = []
            for min_temp, avg_temp, max_temp in results:
                date_temps = {}
                #date_temps["date"] = date
                date_temps["start date"] = cleaned_date
                date_temps["end date"] = most_current[0]
                date_temps["min temp"] = min_temp
                date_temps["avg temp"] = round(avg_temp,2)
                date_temps["max temp"] = max_temp
                temp_list.append(date_temps)
            
            return jsonify(temp_list)

    # If the date the user is searching for doesn't exist, respond with an error message
    return jsonify({"error": "Start date not found within the database."}), 404
        
'''--------------------'''
''' START and END DATE '''
'''--------------------'''

# Start and End Date page. Queries and displays a list of min, avg, and max temperatures for all dates between the start and end dates (inclusive).
@app.route("/api/v1.0/<start>/<end>")
def end_date(start, end):
    # Message sent to the terminal to let developer know that a request to access the page was received
    print("Server received request for 'Start and End Date' page...")

    # The date util parser will automatically detect the date format entered then we convert it to YYYY-MM-DD
    entered_start_date = dp.parse(start)
    date_object = dt.datetime.strptime(str(entered_start_date), "%Y-%m-%d %H:%M:%S")
    cleaned_start_date = date_object.strftime("%Y-%m-%d")

    entered_end_date = dp.parse(end)
    date_object = dt.datetime.strptime(str(entered_end_date), "%Y-%m-%d %H:%M:%S")
    cleaned_end_date = date_object.strftime("%Y-%m-%d")

    # If the user enters the end date first, correct it here
    if cleaned_end_date < cleaned_start_date:
        new_start = cleaned_end_date
        new_end = cleaned_start_date
        cleaned_end_date = new_end
        cleaned_start_date = new_start

     # Create a session (link) from Python to the DB
    session = Session(engine)

    # First create a list of all the dates we have data for
    search = session.query(Measurement.date)
    search_list = [np.ravel(value) for value in search]
  
    # Loop through the data
    for start_date in search_list:

        # Check to see if the start date the user is searching for exists in the data
        if start_date == cleaned_start_date:

            for end_date in search_list:


                if end_date == cleaned_end_date:

                    # Create a selection to pass into the query containing all search parameters
                    min_avg_max = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

                    # Write out the query, unpack the selection from above, and filter for the start date
                    results = session.query(*min_avg_max).\
                        filter(Measurement.date >= cleaned_start_date).\
                        filter(Measurement.date <= cleaned_end_date)
            
                    # Close the session after we retreive the data
                    session.close()

                    # Create a list of dictionaries to hold all the data and return it as a jsonified object
                    temp_list = []
                    for min_temp, avg_temp, max_temp in results:
                        date_temps = {}
                        date_temps["start date"] = cleaned_start_date
                        date_temps["end date"] = cleaned_end_date
                        date_temps["min temp"] = min_temp
                        date_temps["avg temp"] = round(avg_temp,2)
                        date_temps["max temp"] = max_temp
                        temp_list.append(date_temps)
            
                    return jsonify(temp_list)

            # If the date the user is searching for doesn't exist, respond with an error message
            return jsonify({"error": "End date not found within the database."}), 404

    # If the date the user is searching for doesn't exist, respond with an error message
    return jsonify({"error": "Start date not found within the database."}), 404

# This code will allow the app to run and show debug errors
if __name__ == "__main__":
    app.run(debug=True)