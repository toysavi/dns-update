from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder="frontend/build")

@app.route("/")
def serve_react():
    return send_from_directory("frontend/build", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend/build", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
