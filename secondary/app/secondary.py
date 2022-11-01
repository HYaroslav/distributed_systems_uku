import logging
import os
from flask import Flask, redirect, render_template
from werkzeug.serving import run_simple

from replications_listener import ReplicationListener


PORT = int(os.environ["PORT"])
CURRENT_IP = os.environ["LISTENER_IP"]
CURRENT_NODE_ID = PORT - int(os.environ["SECONDARY_START_PORT"]) + 1
MSG_LIST = []

logging.basicConfig(
    filename="logs.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger().addHandler(logging.StreamHandler())

app = Flask(__name__)
replication_listener = ReplicationListener(ip=CURRENT_IP, port=PORT)


@app.route("/")
def home_page():
    return redirect("/get_message")


@app.route("/get_message", methods=["GET"])
def get_message():
    global MSG_LIST

    msg_list = []
    for msg_index, msg in enumerate(reversed(MSG_LIST)):
        msg_list.append({
            "title": f"Message {len(MSG_LIST)-msg_index}",
            "content": msg
        })

    return render_template("index.html", node_id=CURRENT_NODE_ID, messages=msg_list)


@app.route("/get_logs", methods=["GET"])
def get_logs():
    with open("logs.log", encoding="utf-8") as f:
        logs = f.readlines()

    return render_template("logs.html", node_id=CURRENT_NODE_ID, logs=logs)


if __name__ == "__main__":
    replication_listener.listen(MSG_LIST)
    run_simple("0.0.0.0", PORT, app, use_reloader=False)
