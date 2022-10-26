import logging
import os
from flask import Flask, jsonify
from werkzeug.serving import run_simple

from replications_listener import ReplicationListener


PORT = int(os.environ["PORT"])
CURRENT_IP = os.environ["LISTENER_IP"]
MSG_LIST = []

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
replication_listener = ReplicationListener(ip=CURRENT_IP, port=PORT)


@app.route("/get_message", methods=["GET"])
def get_message():
    global MSG_LIST
    return jsonify(MSG_LIST)


if __name__ == "__main__":
    replication_listener.listen(MSG_LIST)
    run_simple("0.0.0.0", PORT, app, use_reloader=False)
