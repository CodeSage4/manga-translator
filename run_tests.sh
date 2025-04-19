#!/bin/bash

# Run backend tests
cd backend
python -m unittest discover tests

# Run frontend tests
cd ../frontend
npm test 