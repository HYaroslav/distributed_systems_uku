import socket
import threading
import logging
from typing import List
from time import sleep
import random

class ReplicationListener():

    server_socket: socket.socket
    logger: logging.Logger

    def __init__(self, ip: str, port: str) -> None:
        self.ip = ip
        self.port = port
        self.listener_port = int(port) + 1
        self.logger = logging.getLogger(__name__)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def listen(self, db_list: List[str]):
        listen_thread = threading.Thread(target=self._listen, kwargs={"db_list":db_list})
        listen_thread.start()
        

    def _listen(self, db_list: List[str]):
        self.server_socket.bind((self.ip, self.listener_port))
        self.server_socket.listen()
        self.logger.info(f"Replication listener started on {self.ip}:{self.listener_port}")

        while(True):
            (clientConnected, clientAddress) = self.server_socket.accept()
            self.logger.info("Accepted a replication request from %s:%s"%(clientAddress[0], clientAddress[1]))

            dataFromClient = clientConnected.recv(1024).decode("utf-8")

            # imitate lagging
            rand_int = random.randint(2, 5)
            self.logger.info("Data will be replicated in %s seconds.", rand_int)
            sleep(rand_int)
            
            db_list.append(dataFromClient)
            self.logger.info("Data is successfully replicated.")
            clientConnected.send(f"Message is successfully replicated on {self.ip}:{self.port}".encode())