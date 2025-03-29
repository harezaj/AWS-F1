#!/bin/bash

cd f1_data_fetcher
pip install -r requirements.txt -t ./package
cp lambda_function.py ./package/
cd package
zip -r ../function.zip .
cd ..
rm -rf package 