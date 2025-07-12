#!/bin/bash
# Start the Flask backend server
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
python run.py
