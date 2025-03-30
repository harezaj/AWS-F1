#!/bin/bash

# Install dependencies
pip install -r requirements.txt -t ./package

# Copy Lambda function code to package
cp loader_function.py ./package/

# Create zip file
cd package
zip -r ../function.zip .
cd ..

# Clean up
rm -rf package

echo "Deployment package created at function.zip"
echo "Use this command to create/update the Lambda function:"
echo "aws lambda create-function --function-name data-loader --zip-file fileb://function.zip --handler loader_function.lambda_handler --runtime python3.9 --role arn:aws:iam::794431322648:role/f1-data-lambda-role --timeout 300 --memory-size 256"
echo ""
echo "Or update an existing function with:"
echo "aws lambda update-function-code --function-name data-loader --zip-file fileb://function.zip" 