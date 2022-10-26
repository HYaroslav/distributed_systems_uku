import os
import logging
from flask import Flask, request, jsonify

from replicator import Replicator

PORT = os.environ["PORT"]
SECONDARY_START_PORT = int(os.environ["SECONDARY_START_PORT"])
SECONDARY_NUMBER = int(os.environ["SECONDARY_NUMBER"])

MSG_LIST = []

logging.basicConfig(level=logging.INFO)
app = Flask("app")

replicator = Replicator(start_port=SECONDARY_START_PORT, secondaries_number=SECONDARY_NUMBER)

@app.route("/append_message", methods=["POST"])
def append_message():
    global MSG_LIST

    data = request.json
    MSG_LIST.append(data)

    replicator.replicate(data)

    return jsonify(data)


@app.route("/get_message", methods=["GET"])
def get_message():
    global MSG_LIST

    return jsonify(MSG_LIST)


if __name__ == "__main__":    
    app.run(host="0.0.0.0", port=PORT)