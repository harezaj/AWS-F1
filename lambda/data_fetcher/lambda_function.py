import boto3
import json
import os
from datetime import datetime
import requests

# Base API URL for OpenF1
BASE_URL = 'https://api.openf1.org/v1'

# S3 bucket for storing raw data
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

def get_session_key(race_date=None, country=None, year=None):
    print(f"Fetching session key for race: date={race_date}, country={country}, year={year}")
    
    params = {}
    if race_date:
        # Use the direct date_start parameter for the API
        params['date_start'] = race_date
        
    if country:
        params['country_name'] = country
        
    if year:
        params['year'] = year
        
    # Only interested in the race session
    params['session_type'] = 'Race'
    
    print(f"Querying sessions API with params: {params}")
    
    try:
        response = requests.get(f"{BASE_URL}/sessions", params=params)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Get the first matching session (should be just one race per date)
                session = data[0]
                print(f"Found session: {session}")
                return session
            else:
                print(f"No session found with params: {params}")
        else:
            print(f"Error fetching session: {response.status_code}")
    except Exception as e:
        print(f"Exception fetching session: {str(e)}")
    
    return None

def fetch_data(endpoint, session_key):
    print(f"Fetching data from /{endpoint} for session {session_key}")
    
    params = {'session_key': session_key}
    
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"Retrieved {len(data)} records from /{endpoint}")
            return data
        else:
            print(f"Error fetching {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"Exception fetching {endpoint}: {str(e)}")
    
    return []

def save_to_s3(data, s3_key):
    if not data:
        print(f"No data to save")
        return
    
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        print(f"Saved {len(data)} records to s3://{BUCKET_NAME}/{s3_key}")
        return True
    except Exception as e:
        print(f"Failed to save to S3: {str(e)}")
        return False

def lambda_handler(event, context):
    # Validate event input
    if not isinstance(event, dict):
        print(f"Invalid event format: {event}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid event format'})
        }
    
    # Extract race date from the event
    race_date = None
    if 'race_date' in event:
        race_date = event['race_date']
        # Validate date format
        if not isinstance(race_date, str):
            print(f"Invalid race_date format: {race_date}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid race_date format'})
            }
        # Check if race_date is a timestamp (from EventBridge)
        if race_date.startswith('20') and 'T' in race_date:
            # Convert timestamp to date only
            race_date = race_date.split('T')[0]
    elif 'detail' in event and isinstance(event['detail'], dict) and 'race_date' in event['detail']:
        race_date = event['detail']['race_date']
        if not isinstance(race_date, str):
            print(f"Invalid race_date in detail: {race_date}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid race_date in detail'})
            }
    
    # If no race date provided, use previous day's date
    if not race_date:
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        race_date = yesterday.isoformat()
        print(f"No race date provided, using previous day's date: {race_date}")
    
    # Validate optional parameters
    country = event.get('country', None)
    if country is not None and not isinstance(country, str):
        print(f"Invalid country format: {country}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid country format'})
        }
    
    year = event.get('year', None)
    if year is not None:
        try:
            year = int(year)
        except (ValueError, TypeError):
            print(f"Invalid year format: {year}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid year format'})
            }
    
    print(f"Looking for race data on date: {race_date}")
    
    # Get the session key for the race
    session_info = get_session_key(race_date, country, year)
    if not session_info:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'No race session found for date {race_date}'})
        }
    
    session_key = session_info['session_key']
    
    # Save the session data itself - using simpler folder structure
    session_data = [session_info]  # Wrap in list as our save function expects an array
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_s3_key = f"raw/{race_date}/sessions_{timestamp}.json"
    save_to_s3(session_data, session_s3_key)
    
    # Define endpoints to fetch data from
    endpoints = ['drivers', 'pit', 'stints', 'weather', 'laps']
    endpoints_processed = []
    
    for endpoint in endpoints:
        try:
            data = fetch_data(endpoint, session_key)
            if data:
                # Create a unique filename with timestamp - simpler folder structure
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_key = f"raw/{race_date}/{endpoint}_{timestamp}.json"
                
                save_to_s3(data, s3_key)
                endpoints_processed.append(endpoint)
        except Exception as e:
            print(f"Error fetching {endpoint} data: {str(e)}")
    
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'F1 race data fetched and saved',
            'race_date': race_date,
            'country': session_info['country_name'],
            'circuit': session_info['circuit_short_name'],
            'session_name': session_info['session_name'],
            'session_key': session_key,
            'endpoints_processed': endpoints_processed
        })
    }
    
    return response 