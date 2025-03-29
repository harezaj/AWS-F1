import boto3
import json
import os
from datetime import datetime
import requests

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# AWS credentials are loaded from environment or ~/.aws/credentials
s3 = boto3.client('s3')
BUCKET_NAME = 'f1-raw-data-794431322648'

def insert_data(table_name, data):
    """Insert data into a Supabase table."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Inserted {len(data)} rows into {table_name}: {response.status_code}")
    return response.status_code == 201

def process_session(session_data):
    """Process session data and insert into Supabase."""
    # Extract session data
    session = {
        'session_key': session_data['session_key'],
        'session_name': session_data['session_name'],
        'date_start': session_data['date_start'],
        'date_end': session_data['date_end'],
        'session_type': session_data['session_type'],
        'meeting_key': session_data['meeting_key'],
        'location': session_data['location'],
        'country_name': session_data['country_name'],
        'circuit_short_name': session_data['circuit_short_name'],
        'year': session_data['year']
    }
    
    # Insert session
    insert_data('sessions', [session])

def process_drivers(drivers_data, session_key):
    """Process drivers data and insert into Supabase."""
    drivers = []
    for driver in drivers_data:
        drivers.append({
            'session_key': session_key,
            'driver_number': driver['driver_number'],
            'name_acronym': driver.get('name_acronym'),
            'full_name': driver.get('full_name'),
            'team_name': driver.get('team_name'),
            'team_colour': driver.get('team_colour')
        })
    
    if drivers:
        insert_data('drivers', drivers)

def process_weather(weather_data, session_key):
    """Process weather data and insert into Supabase."""
    weather_items = []
    for item in weather_data:
        weather_items.append({
            'session_key': session_key,
            'date': item['date'],
            'air_temperature': item.get('air_temperature'),
            'humidity': item.get('humidity'),
            'track_temperature': item.get('track_temperature'),
            'wind_speed': item.get('wind_speed')
        })
    
    if weather_items:
        insert_data('weather', weather_items)

def process_pit_stops(pit_data, session_key):
    """Process pit stop data and insert into Supabase."""
    pit_stops = []
    for stop in pit_data:
        pit_stops.append({
            'session_key': session_key,
            'driver_number': stop['driver_number'],
            'pit_duration': stop.get('pit_duration'),
            'lap_number': stop.get('lap_number')
        })
    
    if pit_stops:
        insert_data('pit_stops', pit_stops)

def process_stints(stints_data, session_key):
    """Process stint data and insert into Supabase."""
    stints = []
    for stint in stints_data:
        stints.append({
            'session_key': session_key,
            'driver_number': stint['driver_number'],
            'stint_number': stint.get('stint_number'),
            'compound': stint.get('compound'),
            'lap_start': stint.get('lap_start'),
            'lap_end': stint.get('lap_end')
        })
    
    if stints:
        insert_data('stints', stints)

def process_s3_file(s3_key):
    """Process a JSON file from S3 and insert into Supabase."""
    try:
        # Get the file from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Extract file info from the key
        parts = s3_key.split('/')
        data_type = parts[-1].split('_')[0]  # e.g., 'drivers', 'weather'
        session_key = None
        
        # Process the data based on type
        if 'sessions' in s3_key:
            # This is session data, handle differently
            process_session(data[0])  # Assuming session data is an array with one item
            session_key = data[0]['session_key']
        else:
            # Use the session key from the data
            if data and len(data) > 0:
                session_key = data[0].get('session_key')
        
        if session_key:
            if data_type == 'drivers':
                process_drivers(data, session_key)
            elif data_type == 'weather':
                process_weather(data, session_key)
            elif data_type == 'pit':
                process_pit_stops(data, session_key)
            elif data_type == 'stints':
                process_stints(data, session_key)
        
        print(f"Processed {s3_key}")
        return True
    except Exception as e:
        print(f"Error processing {s3_key}: {str(e)}")
        return False

def list_s3_files(prefix='raw/'):
    """List all files in S3 bucket with given prefix."""
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                files.append(obj['Key'])
    return files

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return
    
    # List S3 files
    files = list_s3_files()
    print(f"Found {len(files)} files in S3")
    
    # Process each file
    processed = 0
    for file in files:
        if file.endswith('.json'):
            if process_s3_file(file):
                processed += 1
    
    print(f"Processed {processed} files")

if __name__ == "__main__":
    main() 