import json
import os
import time
from datetime import datetime, timedelta
import requests
import boto3
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client('s3')

def get_race_data(race_date):
    """
    Fetch F1 race data from OpenF1 API for a specific date.
    Returns a dictionary containing all available data points.
    """
    base_url = "https://api.openf1.org/v1"
    
    # Define endpoints to fetch
    endpoints = {
        'drivers': '/drivers',
        'teams': '/teams',
        'races': '/races',
        'results': '/results',
        'laps': '/laps',
        'car_data': '/car_data',
        'weather': '/weather',
        'team_radio': '/team_radio',
        'race_control': '/race_control'
    }
    
    data = {}
    
    for endpoint, path in endpoints.items():
        try:
            # Add delay to respect API rate limits
            time.sleep(1)
            
            # Construct query parameters
            params = {
                'date': race_date,
                'format': 'json'
            }
            
            # Make API request
            response = requests.get(f"{base_url}{path}", params=params)
            response.raise_for_status()
            
            # Store the data
            data[endpoint] = response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"failed to fetch {endpoint}: {str(e)}")
            data[endpoint] = []
            
    return data

def save_to_s3(data, race_date):
    """
    Save the fetched data to S3 bucket.
    """
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    # Create a timestamp for the file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save each data type as a separate file
    for data_type, content in data.items():
        if content:  # Only save if we have data
            file_name = f"raw/{race_date}/{data_type}_{timestamp}.json"
            
            try:
                # Convert data to JSON string
                json_data = json.dumps(content)
                
                # Upload to S3
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=file_name,
                    Body=json_data,
                    ContentType='application/json'
                )
                
                print(f"saved {file_name}")
                
            except ClientError as e:
                print(f"failed to save {file_name}: {str(e)}")
                raise

def lambda_handler(event, context):
    """
    Main Lambda handler function.
    """
    try:
        # Get yesterday's date (assuming race was yesterday)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Fetch race data
        print(f"fetching data for {yesterday}")
        race_data = get_race_data(yesterday)
        
        # Save to S3
        print("Saving data to S3")
        save_to_s3(race_data, yesterday)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'data fetched and saved',
                'date': yesterday
            })
        }
        
    except Exception as e:
        print(f"error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 