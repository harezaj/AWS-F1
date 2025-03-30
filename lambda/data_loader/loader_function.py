import boto3
import json
import os
from datetime import datetime
import requests
import base64

# Secret name for Supabase credentials
SECRET_NAME = os.environ.get('SUPABASE_SECRET_NAME', 'f1-data-supabase-credentials')

# Initialize the Secrets Manager client
secrets_client = boto3.client('secretsmanager')

# Initialize with empty values, will be loaded from secrets manager
SUPABASE_URL = None
SUPABASE_KEY = None

def get_supabase_credentials():
    global SUPABASE_URL, SUPABASE_KEY
    
    try:
        # Get the secret
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        
        # Parse the secret JSON
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            SUPABASE_URL = secret.get('SUPABASE_URL')
            SUPABASE_KEY = secret.get('SUPABASE_KEY')
        else:
            # If binary, decode it
            decoded_binary = base64.b64decode(response['SecretBinary'])
            secret = json.loads(decoded_binary)
            SUPABASE_URL = secret.get('SUPABASE_URL')
            SUPABASE_KEY = secret.get('SUPABASE_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in secret")
            
    except Exception as e:
        print(f"Error retrieving Supabase credentials: {str(e)}")
        raise

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

def insert_data(table_name, data):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Inserted {len(data)} rows into {table_name}: {response.status_code}")
        
        if response.status_code == 409:
            print(f"Data already exists in {table_name} (conflict). Response: {response.text[:100]}...")
        elif response.status_code >= 400:
            print(f"Error inserting into {table_name}. Status: {response.status_code}, Response: {response.text[:200]}...")
            # Print first item of data for debugging
            if data and len(data) > 0:
                print(f"Sample data item: {json.dumps(data[0], indent=2)}")
        
        return response.status_code == 201 or response.status_code == 200 or response.status_code == 409
    except Exception as e:
        print(f"Exception while inserting into {table_name}: {str(e)}")
        return False

def process_session(session_data):
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

def list_s3_files(prefix='raw/'):
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                files.append(obj['Key'])
    return files

def process_s3_file(s3_key):
    try:
        # Get the file from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Extract file info from the key
        parts = s3_key.split('/')
        filename = parts[-1]
        data_type = filename.split('_')[0]  # e.g., 'drivers', 'weather', 'sessions'
        
        print(f"Processing file {s3_key}, data_type: {data_type}")
        
        # Process the data based on type
        if data_type == 'sessions':
            # This is session data, handle differently
            process_session(data[0])  # Assuming session data is an array with one item
            session_key = data[0]['session_key']
            return True
        else:
            # For other data types, we need the session_key from the data
            if data and len(data) > 0:
                session_key = data[0].get('session_key')
                
                if session_key:
                    if data_type == 'drivers':
                        process_drivers(data, session_key)
                    elif data_type == 'pit':
                        process_pit_stops(data, session_key)
                    elif data_type == 'stints':
                        process_stints(data, session_key)
                    elif data_type == 'weather':
                        process_weather(data, session_key)
                    
                    print(f"Processed {s3_key}")
                    return True
                else:
                    print(f"No session_key found in {s3_key}")
            else:
                print(f"No data found in {s3_key}")
        
        return False
    except Exception as e:
        print(f"Error processing {s3_key}: {str(e)}")
        return False

def process_all_files():
    # List S3 files
    files = list_s3_files()
    print(f"Found {len(files)} files in S3")
    
    # Sort files to process sessions first
    files.sort(key=lambda x: 0 if 'sessions_' in x else 1)
    
    # Process each file
    processed = 0
    for file in files:
        if file.endswith('.json'):
            if process_s3_file(file):
                processed += 1
    
    print(f"Processed {processed} files")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Processed {processed} files'})
    }

def lambda_handler(event, context):
    try:
        # Validate event input
        if not isinstance(event, dict):
            print(f"Invalid event format: {event}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid event format'})
            }
        
        # Get Supabase credentials from Secrets Manager
        get_supabase_credentials()
        
        # Check for specific file to process
        if 'file_key' in event:
            file_key = event['file_key']
            # Validate file_key
            if not isinstance(file_key, str) or not file_key.strip():
                print(f"Invalid file_key: {file_key}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid file_key'})
                }
            
            # Sanitize file_key to prevent path traversal
            if '..' in file_key or file_key.startswith('/'):
                print(f"Potential path traversal in file_key: {file_key}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid file path'})
                }
            
            success = process_s3_file(file_key)
            if success:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': f'Processed file {file_key}'})
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f'Failed to process file {file_key}'})
                }
        
        # Process all files by default
        return process_all_files()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# For local testing
if __name__ == "__main__":
    process_all_files() 