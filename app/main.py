# main.py
from flask import Flask, jsonify
from routes import init_routes  # we'll define this in routes.py

app = Flask(__name__)

# --- CORS setup ---
from flask_cors import CORS
CORS(app)  # allow all origins

# Register API routes
init_routes(app)

# Health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=8000, debug=True)
