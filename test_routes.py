from web_app.app import app
import os
import sys

# Mock session for test
with app.test_request_context('/'):
    try:
        from flask import render_template, session
        # Test index route
        print("Testing index route...")
        # We need to mock session
        with app.test_client() as client:
            response = client.get('/', follow_redirects=True)
            print(f"Status: {response.status_code}")
            if response.status_code == 500:
                print("ERROR: 500 detected!")
                # To see traceback we can use client.get without catching? 
                # Flask test client doesn't usually show traceback unless debug=True
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()
