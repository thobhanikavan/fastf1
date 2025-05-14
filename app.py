import fastf1
import pandas as pd
from flask import Flask, request, jsonify, Response, send_file, url_for, send_file, url_for
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

def get_driver_lap_data(driver_lap_data):
    # Get all the x, y and z coordinates of the driver during the entire race
    x = driver_lap_data.telemetry['X']
    y = driver_lap_data.telemetry['Y']
    z = driver_lap_data.telemetry['Z']
    
    # Get session time
    session_time = driver_lap_data.telemetry['SessionTime']
    
    # Get car data for all the coordinates
    speed = driver_lap_data.telemetry['Speed']
    gear = driver_lap_data.telemetry['nGear']
    rpm = driver_lap_data.telemetry['RPM']
    throttle = driver_lap_data.telemetry['Throttle']
    brake = driver_lap_data.telemetry['Brake']
    drs = driver_lap_data.telemetry['DRS']

    lap_data = pd.DataFrame({
        'x': x,
        'y': y,
        'z': z,
        'speed': speed,
        'gear': gear,
        'rpm': rpm,
        'throttle': throttle,
        'brake': brake,
        'drs': drs,
        'position': driver_lap_data['Position'],
        'session time': session_time
    })
    
    lap_data['session time'] = lap_data['session time'].astype(str)
    
    return lap_data

@app.route('/get_racer_data', methods=['GET'])
def get_racer_data():
    """
    API to return lap data for all drivers with detailed telemetry
    """
    try:
        # Fetch and validate query params
        race_year = request.args.get('year')
        race_location = request.args.get('location')
        race_type = request.args.get('type')

        if not race_year:
            return jsonify({"error": "Race year is required"}), 400
        if not race_location:
            return jsonify({"error": "Race location is required"}), 400
        if not race_type:
            return jsonify({"error": "Kindly provide race session type"}), 400
        if race_type not in ["Q", "R"]:
            return jsonify({"error": "Invalid race session type. Should be 'Q' or 'R'."}), 400

        # Cast parameters
        race_year = int(race_year)
        race_location = str(race_location)
        race_type = str(race_type)

        # Load session
        session = fastf1.get_session(race_year, race_location, race_type)
        session.load()

        # Get lap data
        laps_data = session.laps

        # If DriverNumber is missing, return available columns to debug
        if 'DriverNumber' not in laps_data.columns:
            return jsonify({"error": "'DriverNumber' column not found", "columns": list(laps_data.columns)}), 500

        # Get all drivers in the session
        list_of_drivers = session.drivers
        all_driver_data = {}

        for driver in list_of_drivers:
            driver_laps = laps_data[laps_data['DriverNumber'] == driver].copy()

            if driver_laps.empty:
                continue  # skip driver if no data available

            selected_columns = [
                'Driver', 'LapTime', 'LapNumber',
                'PitOutTime', 'PitInTime', 
                'Sector1Time', 'Sector2Time', 'Sector3Time',
                'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 'IsPersonalBest',
                'TyreLife', 'Team', 'LapStartTime'
            ]

            # Filter only available columns to avoid KeyErrors
            available_cols = [col for col in selected_columns if col in driver_laps.columns]
            driver_laps = driver_laps[available_cols]

            # Convert timedelta columns to string
            timedelta_cols = [
                'LapTime', 'PitOutTime', 'PitInTime',
                'Sector1Time', 'Sector2Time', 'Sector3Time',
                'LapStartTime'
            ]
            for col in timedelta_cols:
                if col in driver_laps.columns:
                    driver_laps[col] = driver_laps[col].astype(str)

            all_driver_data[driver] = driver_laps.to_dict(orient='records')

        return jsonify(all_driver_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_race_position_and_car_data', methods=['GET'])
def get_race_position_and_car_data():
    
    # Fetch data from frontend
    race_year = request.args.get('year')
    race_location = request.args.get('location')
    race_type = request.args.get('type')
    
    # Validate received data from frontend
    if not race_year:
        return jsonify({"error": "Race year is required"}), 400
    if not race_location:
        return jsonify({"error": "Race location is required"}), 400
    if not race_type:
        return jsonify({"error": "Kindly provide race session type"}), 400
    if race_type not in ["Q", "R"]:
        return jsonify({"error": "Invalid race session type is provided, please note that session type should be from 'Q' or 'R'"}), 400
    
    # Typecast the parameters
    race_year = int(race_year)
    race_location = str(race_location)
    race_type = str(race_type)
    
    # Load session
    session = fastf1.get_session(race_year, race_location, race_type)
    session.load()
    
    # Get lap data
    laps_data = session.laps

    # If DriverNumber is missing, return available columns to debug
    if 'DriverNumber' not in laps_data.columns:
        return jsonify({"error": "'DriverNumber' column not found", "columns": list(laps_data.columns)}), 500

    # Get all drivers in the session
    list_of_drivers = session.drivers
    all_driver_data = {}

    for driver in list_of_drivers:
        driver_laps = laps_data[laps_data['DriverNumber'] == driver].copy()

        if driver_laps.empty:
            continue  # skip driver if no data available
        
        # Get driver Abbreviation
        driver_abb = driver_laps['Driver'].iloc[0]
        
        # Get all the details of the driver during the race
        lap_details = laps_data.pick_drivers(driver_abb)
        driver_lap_data = get_driver_lap_data(lap_details)
        
        # Update all the details for the specific driver in all_driver_data
        all_driver_data[driver] = driver_lap_data.to_dict(orient='records')
    
    # Use this to check transmission data since data size is too large to handle for Postman 
    # with open("data.json", "w") as json_file:
    #     json.dump(all_driver_data, json_file, indent=4)
    
    return jsonify(all_driver_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001,debug=True)
