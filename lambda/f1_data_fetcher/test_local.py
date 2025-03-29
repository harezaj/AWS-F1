import os
os.environ['S3_BUCKET_NAME'] = 'f1-raw-data-794431322648'

from lambda_function import lambda_handler

# Test event
test_event = {
    'race_date': '2025-03-23'
}

# Run the function
response = lambda_handler(test_event, None)
print('Response:', response) 