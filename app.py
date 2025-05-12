import fastf1
import pandas as pd
from flask import Flask, request, jsonify, Response, send_file, url_for, send_file, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_race_telemetry', methods=['GET'])
def get_telemetry_data():
    
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
    
    # Get list of drivers in the particular session (We get the number of driver)
    list_of_drivers = session.drivers
    print(list_of_drivers)
    
    return list_of_drivers

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001,debug=True)
