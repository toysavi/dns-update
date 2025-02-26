import sys
import threading
import os
import webbrowser
from flask import Flask, send_from_directory, jsonify
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Initialize Flask
app = Flask(__name__, static_folder="frontend/build", static_url_path="")

@app.route("/")
def serve_react():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/dns_records")
def get_dns_records():
    return jsonify([
        {"name": "example.com", "type": "A", "ip": "192.168.1.1"},
        {"name": "api.example.com", "type": "CNAME", "point_to": "example.com"}
    ])

# Start Flask server in a separate thread
def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

# Create a PyQt5 Window to Show React App
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DNS Manager")
        self.setGeometry(100, 100, 800, 600)

        self.browser = QWebEngineView()
        self.browser.setUrl("http://127.0.0.1:5000/")

        layout = QVBoxLayout()
        layout.addWidget(self.browser)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

# Run the App
if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start the PyQt GUI
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
