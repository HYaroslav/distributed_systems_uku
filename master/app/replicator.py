import logging
import threading
from typing import List
import requests
import queue

SECONDARY_ENDPOINT = "http://172.20.0.{host_address}:{port}/replicate_message"

class Replicator():

    secondary_endpoints_list: List[str] = []
    logger: logging.Logger
    replication_queue: queue.Queue

    def __init__(self, start_port: int, secondaries_number: int, logger: logging.Logger) -> None:
        self.logger = logger

        self.logger.info("hello")
        
        for i in range(secondaries_number):
            # IPv4 for secondaries will start from 172.20.0.3
            endpoint = SECONDARY_ENDPOINT.format(host_address=i+3, port=start_port+i)
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

        thread_barrier.wait()

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
        response = requests.post(endpoint_url, json={"data":data})
        
        if response.status_code != 200:
            self.logger.error(f"Error in replication: {response.json()}")
        else:
            self.logger.info(str(response.json()))

        thread_barrier.wait()
