#!/bin/bash

# Create a clean package directory
rm -rf package
mkdir package

# Install only the required dependencies
pip install requests -t ./package

# Copy the Lambda function code
cp lambda_function.py ./package/

# Create the deployment package
cd package
zip -r ../function.zip .
cd ..

# Clean up
rm -rf package 