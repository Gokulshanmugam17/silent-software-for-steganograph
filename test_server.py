"""
Simple Flask server test - run this to test if Flask works
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Flask server is working!"})

@app.route('/test')
def test():
    return "Test successful!"

if __name__ == '__main__':
    print("=" * 50)
    print("Starting minimal Flask server on http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
