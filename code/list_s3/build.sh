#!/usr/bin/env bash

# This script will be run when Terraform pack your code

# Install dependencies
cd `dirname $0`
pip install -r requirements.txt -t ./package/
