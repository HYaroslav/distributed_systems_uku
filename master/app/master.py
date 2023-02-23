import os
import logging
from flask import Flask, request, redirect, render_template, flash

from replicator import Replicator
from heartbeats import HeartBeater
import utils

PORT = os.environ["PORT"]
SECONDARY_START_PORT = int(os.environ["SECONDARY_START_PORT"])
SECONDARY_NUMBER = int(os.environ["SECONDARY_NUMBER"])
SECONDARY_IP_LIST = utils.get_secondaries_ip_list(SECONDARY_NUMBER, SECONDARY_START_PORT)
SECONDARY_LISTENER_IP_LIST = utils.get_secondaries_listener_ip_list(SECONDARY_NUMBER, SECONDARY_START_PORT)
SECONDARY_LOCAL_IP_LIST = utils.get_secondaries_local_ip_list(SECONDARY_NUMBER, SECONDARY_START_PORT)

MSG_LIST = []

logging.basicConfig(
    filename="logs.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger().addHandler(logging.StreamHandler())

app = Flask("app")
app.config['SECRET_KEY'] = os.urandom(24).hex()

heartbeater = HeartBeater(SECONDARY_IP_LIST)
replicator = Replicator(SECONDARY_LISTENER_IP_LIST, heartbeater)


@app.route("/")
def home_page():
    return redirect("/get_message")


@app.route("/append_message", methods=["GET", "POST"])
def append_message():
    if request.method == "POST":
        global MSG_LIST
        if request.form:
            data = request.form['content']
            write_concern = int(request.form['write_concern'])
        elif request.json:
            data = request.json['content']
            write_concern = int(request.json['write_concern'])
        
        if not data:
            flash("Content is required", category="error")
        else:
            MSG_LIST.append(data)
            replicator.replicate(data, write_concern)
            flash("Content is replicated", category="success")

    return render_template("append_form.html", node_ip_list=SECONDARY_LOCAL_IP_LIST)


@app.route("/get_message", methods=["GET"])
def get_message():
    global MSG_LIST

    msg_list = []
    for msg_index, msg in enumerate(reversed(MSG_LIST)):
        msg_list.append({
            "title": f"Message {len(MSG_LIST)-msg_index}",
            "content": msg
        })

    return render_template("index.html", messages=msg_list, node_ip_list=SECONDARY_LOCAL_IP_LIST)


@app.route("/get_logs", methods=["GET"])
def get_logs():
    with open("logs.log", encoding="utf-8") as f:
        logs = f.readlines()

    return render_template("logs.html", logs=logs, node_ip_list=SECONDARY_LOCAL_IP_LIST)


@app.route("/get_health", methods=["GET"])
def get_health():
    status_dict = heartbeater.get_all_health_statuses()

    status_dict = {f"http://localhost:{int(url.split(':')[-1])}/": [status.name, status.value] for url, status in status_dict.items()}

    return render_template("health.html", status_dict=status_dict, node_ip_list=SECONDARY_LOCAL_IP_LIST)


if __name__ == "__main__":    
    app.run(host="0.0.0.0", port=PORT)