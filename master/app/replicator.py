import json
import logging
import threading
from typing import List
import socket


class ExtendedBarrier(threading.Barrier):
    """Class for supporting extra Threads over the Barrier parties.

    `_state` variable can also have value 4 now - released state
    """

    def wait(self, timeout=None):
        """Wait for the barrier.

        When the specified number of threads have started waiting, they are all
        simultaneously awoken. If an 'action' was provided for the barrier, one
        of the threads will have executed that callback prior to returning.
        Returns an individual index number from 0 to 'parties-1'.

        """
        # if Barrier has already been released then return
        if self._state == 4:
            return self._count

        if timeout is None:
            timeout = self._timeout
        with self._cond:
            self._enter() # Block while the barrier drains.
            index = self._count
            self._count += 1
            try:
                if index + 1 == self._parties:
                    # We release the barrier
                    self._release()
                else:
                    # We wait until someone releases us
                    self._wait(timeout)
                return index
            finally:
                self._count -= 1
                # Wake up any threads waiting for barrier to drain.
                self._exit()

    def _exit(self):
        if self._count == 0:
            if self._state in (-1, 1):
                # Mark barrier as released
                self._state = 4
                self._cond.notify_all()    


class Replicator():

    secondary_endpoints_list: List[str] = []
    logger: logging.Logger
    message_id: int

    def __init__(self, secondary_endpoints_list) -> None:
        self.logger = logging.getLogger(__name__)
        self.secondary_endpoints_list = secondary_endpoints_list

        self.message_id = 1


    def replicate(self, data: str, write_concern: int):
        message_id = self.message_id
        self.message_id += 1

        thread_barrier = ExtendedBarrier(write_concern, timeout=20)

        for replica_url in self.secondary_endpoints_list:
            thread = threading.Thread(
                target=self._replicate,
                kwargs={
                    "message_id": message_id,
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
        
        self.logger.info("Replication of msg='%s' to 1 master and %s nodes was done successfuly!", data, write_concern-1)

    
    def _replicate(self, message_id: int, data: str, endpoint_url: str, thread_barrier: ExtendedBarrier):
        host, port = endpoint_url.split(":")

        message = json.dumps({
            "message_id": message_id,
            "message": data
        })
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, int(port)))
            s.sendall(message.encode(encoding="utf-8"))

            response_data = s.recv(1024).decode("utf-8")
            self.logger.info(response_data)

            if response_data.startswith("Error"):
                thread_barrier.abort()
                s.close()
                return

            s.close()

        thread_barrier.wait()
