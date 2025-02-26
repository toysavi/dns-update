import webbrowser
import os
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder="frontend/build", static_url_path="")

# Serve the React frontend
@app.route("/")
def serve_react():
    return send_from_directory("frontend/build", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend/build", path)

# Sample API route for DNS records
@app.route("/dns_records")
def get_dns_records():
    dns_data = [
        {"name": "example.com", "type": "A", "ip": "192.168.1.1"},
        {"name": "api.example.com", "type": "CNAME", "point_to": "example.com"}
    ]
    return jsonify(dns_data)

if __name__ == "__main__":
    port = 5000
    url = f"http://127.0.0.1:{port}"
    
    # Open the app in the browser
    webbrowser.open(url)
    
    # Start the Flask server
    app.run(host="0.0.0.0", port=port)
