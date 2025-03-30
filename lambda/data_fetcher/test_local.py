import os
import json
os.environ['S3_BUCKET_NAME'] = 'f1-raw-data-794431322648'

from lambda_function import lambda_handler

# Load test event from JSON file
with open('./lambda/data_fetcher/test_event.json', 'r') as f:
    test_event = json.load(f)

# Alternatively, you can define the test event directly:
# test_event = {
#     'race_date': '2025-03-23'
# }

# Run the function
response = lambda_handler(test_event, None)
print('Response:', response) 