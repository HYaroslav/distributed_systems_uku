import os
import logging
from flask import Flask, request, redirect, render_template, flash

from replicator import Replicator
import utils

PORT = os.environ["PORT"]
SECONDARY_START_PORT = int(os.environ["SECONDARY_START_PORT"])
SECONDARY_NUMBER = int(os.environ["SECONDARY_NUMBER"])
SECONDARY_LISTENER_IP_LIST = utils.get_secondaries_listner_ip_list(SECONDARY_NUMBER, SECONDARY_START_PORT)
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

replicator = Replicator(SECONDARY_LISTENER_IP_LIST)


@app.route("/")
def home_page():
    return redirect("/get_message")


@app.route("/append_message", methods=["GET", "POST"])
def append_message():
    if request.method == "POST":
        global MSG_LIST
        data = request.form['content']
        
        if not data:
            flash("Content is required", category="error")
        else:
            MSG_LIST.append(data)
            replicator.replicate(data)
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


if __name__ == "__main__":    
    app.run(host="0.0.0.0", port=PORT)