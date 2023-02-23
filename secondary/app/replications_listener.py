import json
import socket
import threading
import logging
from typing import List, Tuple
from time import sleep
import random

MAX_DELAY = 5
MIN_DELAY = 1

class ReplicationListener():

    server_socket: socket.socket
    logger: logging.Logger

    _postponed_messages_list: List[Tuple[int, str]]

    def __init__(self, ip: str, port: str) -> None:
        self.ip = ip
        self.port = port
        self.listener_port = int(port) + 1
        self.logger = logging.getLogger(__name__)
        self._postponed_messages_list = []

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def listen(self, db_list: List[Tuple[int, str]]):
        listen_thread = threading.Thread(target=self._listen, kwargs={"db_list": db_list})
        listen_thread.start()


    def _process_new_message(self, message_id: int, message: str, db_list: List[Tuple[int, str]]):
        def _is_message_should_be_next():
            if not db_list and message_id != 1:
                return False
            else:
                return message_id == 1 or max(db_list, key=lambda x: x[0])[0] + 1 == message_id

        msg_tuple = (message_id, message)
        
        if _is_message_should_be_next():
            db_list.append(msg_tuple)
            if self._postponed_messages_list:
                post_message_id, post_message = self._postponed_messages_list.pop(0)
                self._process_new_message(post_message_id, post_message, db_list)
            return

        if msg_tuple in self._postponed_messages_list:
            return

        self._postponed_messages_list.append(msg_tuple)
        self._postponed_messages_list = sorted(self._postponed_messages_list, key=lambda x: x[0])
        
        

    def _listen(self, db_list: List[Tuple[int, str]]):
        def listen_on_new_client(client_socket: socket.socket, client_addr):
            self.logger.info("Accepted a replication request from %s:%s"%(client_addr[0], client_addr[1]))
            while True:
                dataFromClient = json.loads(
                    client_socket.recv(1024).decode("utf-8")
                )

                message_id = dataFromClient["message_id"]
                message = dataFromClient["message"]

                # imitate delays
                rand_int = random.randint(MIN_DELAY, MAX_DELAY)
                self.logger.info("Data will be replicated in %s seconds.", rand_int)
                sleep(rand_int)

                try:
                    self._process_new_message(message_id, message, db_list)
                    self.logger.info("Data is successfully replicated.")
                    response = f"Message is successfully replicated on {self.ip}:{self.port}".encode()
                except Exception as e:
                    self.logger.error("An error occured in data replication.")
                    response = f"Error on {self.ip}:{self.port} - {e}".encode()
                finally:
                    client_socket.send(response)
                break

            client_socket.close()


        self.server_socket.bind((self.ip, self.listener_port))
        self.server_socket.listen()
        self.logger.info(f"Replication listener started on {self.ip}:{self.listener_port}")

        while True:
            (client_connected, client_address) = self.server_socket.accept()

            new_client_thread = threading.Thread(target=listen_on_new_client, args=(client_connected, client_address))
            new_client_thread.start()

            