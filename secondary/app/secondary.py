import os
from flask import Flask, request, jsonify

from time import sleep
import random


PORT = os.environ["PORT"]
MSG_LIST = []

app = Flask(__name__)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.route("/replicate_message", methods=["POST"])
def replication_listener():
    global MSG_LIST

    rand_int = random.randint(2, 5)
    app.logger.info("Data will be replicated in %s seconds.", rand_int)
    sleep(rand_int)

    data = request.json["data"]
    MSG_LIST.append(data)

    return jsonify(f"Replication to http://localhost:{PORT} was done successfuly!")


@app.route("/get_message", methods=["GET"])
def get_message():
    global MSG_LIST
    return jsonify(MSG_LIST)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)