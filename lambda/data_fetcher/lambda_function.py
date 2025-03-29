import json
import os
import requests
import boto3
from datetime import datetime

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.environ['S3_BUCKET_NAME']

# OpenF1 API base URL
BASE_URL = 'https://api.openf1.org/v1'

# Define endpoints to fetch
endpoints = {
    'drivers': '/drivers',
    'pit': '/pit',
    'stints': '/stints',
    'weather': '/weather'
}

def get_session_key(race_date=None, country_name=None, year=None):
    """Get the session key for a race based on date, country or year."""
    print(f"Fetching session key for race: date={race_date}, country={country_name}, year={year}")
    
    params = {}
    if race_date:
        # Use the direct date_start parameter for the API
        params['date_start'] = race_date
    
    if country_name:
        params['country_name'] = country_name
    
    if year:
        params['year'] = year
    
    if 'session_type' not in params:
        params['session_type'] = 'Race'
    
    print(f"Querying sessions API with params: {params}")
    response = requests.get(f"{BASE_URL}/sessions", params=params)
    if response.status_code == 200:
        sessions = response.json()
        if sessions:
            session = sessions[0]
            print(f"Found session: {session}")
            return session
    
    print(f"No session found with parameters: {params}")
    return None

def fetch_data(endpoint, session_key):
    """Fetch data from a specific endpoint for a given session."""
    print(f"Fetching data from {endpoint} for session {session_key}")
    
    params = {'session_key': session_key}
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"Retrieved {len(data)} records from {endpoint}")
            return data
        else:
            print(f"Error fetching {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"Exception fetching {endpoint}: {str(e)}")
    
    return []

def save_to_s3(data, race_date, data_type, session_info):
    """Save data to S3."""
    if not data:
        print(f"No {data_type} data to save")
        return
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    circuit_name = session_info.get('circuit_short_name', 'unknown')
    s3_key = f'raw/{race_date}/{circuit_name}/{data_type}_{timestamp}.json'
    
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        print(f"Saved {len(data)} {data_type} records to s3://{BUCKET_NAME}/{s3_key}")
        return True
    except Exception as e:
        print(f"Failed to save {data_type} to S3: {str(e)}")
        return False

def lambda_handler(event, context):
    """Main Lambda handler function."""
    try:
        # Get parameters from event
        race_date = event.get('race_date')
        country_name = event.get('country_name')
        year = event.get('year')
        
        # At least one parameter is required
        if not any([race_date, country_name, year]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'At least one of race_date, country_name, or year is required'})
            }

        # Get session info for the race
        session_info = get_session_key(race_date, country_name, year)
        if not session_info:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'No race session found for the provided parameters'})
            }
        
        # Extract session key from the session info
        session_key = session_info['session_key']

        # Fetch and save data for each endpoint
        processed_endpoints = []
        for endpoint_name, endpoint_path in endpoints.items():
            data = fetch_data(endpoint_path, session_key)
            if data:
                save_to_s3(data, race_date, endpoint_name, session_info)
                processed_endpoints.append(endpoint_name)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'F1 race data fetched and saved',
                'race_date': race_date,
                'country': session_info.get('country_name'),
                'circuit': session_info.get('circuit_short_name'),
                'session_name': session_info.get('session_name'),
                'session_key': session_key,
                'endpoints_processed': processed_endpoints
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 