#!/bin/bash

# Install dependencies
pip install -r requirements.txt -t ./package

# Copy Lambda function code to package
cp lambda_function.py ./package/

# Create zip file
cd package
zip -r ../function.zip .
cd ..

# Clean up
rm -rf package 