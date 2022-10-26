import logging
import threading
from typing import List
import socket
import queue

SECONDARY_LISTENER_ADDRESS = "172.20.0.{host_address}:{port}"

class Replicator():

    secondary_endpoints_list: List[str] = []
    logger: logging.Logger
    replication_queue: queue.Queue

    def __init__(self, start_port: int, secondaries_number: int) -> None:
        self.logger = logging.getLogger(__name__)

        self.logger.info("hello")
        
        for i in range(secondaries_number):
            # IPv4 for secondaries will start from 172.20.0.3
            endpoint = SECONDARY_LISTENER_ADDRESS.format(host_address=i+3, port=start_port+i+1)
            self.secondary_endpoints_list.append(endpoint)

        self.replication_queue = queue.Queue()
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def replicate(self, data: str):
        secondaries_number = len(self.secondary_endpoints_list)
        thread_barrier = threading.Barrier(secondaries_number+2, timeout=20)

        thread_list: List[threading.Thread] = []
        for replica_url in self.secondary_endpoints_list:
            thread = threading.Thread(
                target=self._replicate,
                kwargs={
                    "data": data,
                    "endpoint_url": replica_url,
                    "thread_barrier": thread_barrier
                }
            )
            thread_list.append(thread)

        self.replication_queue.put([thread_list, thread_barrier])

        try:
            thread_barrier.wait()
        except threading.BrokenBarrierError:
            self.logger.error("Some nodes take too long time to process.")
            return
        
        self.logger.info("Replication of msg='%s' to %s nodes was done successfuly!", data, secondaries_number)


    def _queue_worker(self):
        while True:
            queue_item = self.replication_queue.get()
            thread_list: List[threading.Thread] = queue_item[0]
            thread_barrier: threading.Barrier = queue_item[1]

            for replica_thread in thread_list:
                replica_thread.start()
            
            thread_barrier.wait()

            self.replication_queue.task_done()
            self.logger.info("Queue - task done.")
    
    def _replicate(self, data: str, endpoint_url: str, thread_barrier: threading.Barrier):
        host, port = endpoint_url.split(":")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, int(port)))
            s.sendall(bytes(data, encoding="utf8"))

            response_data = s.recv(1024).decode("utf-8")
            self.logger.info(response_data)
            s.close()

        thread_barrier.wait()
