import logging
import threading
from typing import List
import socket
import queue


class Replicator():

    secondary_endpoints_list: List[str] = []
    logger: logging.Logger
    replication_queue: queue.Queue

    def __init__(self, secondary_endpoints_list) -> None:
        self.logger = logging.getLogger(__name__)
        self.secondary_endpoints_list = secondary_endpoints_list


    def replicate(self, data: str):
        secondaries_number = len(self.secondary_endpoints_list)
        thread_barrier = threading.Barrier(secondaries_number+1, timeout=20)

        for replica_url in self.secondary_endpoints_list:
            thread = threading.Thread(
                target=self._replicate,
                kwargs={
                    "data": data,
                    "endpoint_url": replica_url,
                    "thread_barrier": thread_barrier
                }
            )
            thread.start()

        try:
            thread_barrier.wait()
        except threading.BrokenBarrierError:
            self.logger.error("Some nodes take too long time to process.")
            return
        
        self.logger.info("Replication of msg='%s' to %s nodes was done successfuly!", data, secondaries_number)

    
    def _replicate(self, data: str, endpoint_url: str, thread_barrier: threading.Barrier):
        host, port = endpoint_url.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, int(port)))
            s.sendall(bytes(data, encoding="utf8"))

            response_data = s.recv(1024).decode("utf-8")
            self.logger.info(response_data)
            s.close()

        thread_barrier.wait()
