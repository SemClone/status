#!/bin/bash
# Simple local server to test the dashboard

echo "Starting local server at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

cd docs && python3 -m http.server 8000
