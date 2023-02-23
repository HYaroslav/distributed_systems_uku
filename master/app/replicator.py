import json
import logging
import threading
from typing import List
import time
import socket
import backoff

import heartbeats


global_heartbeater: heartbeats.HeartBeater = None
BARRIER_TIMEOUT = 600


def retry_prepare(back_off_context):
    logger = logging.getLogger(__name__)
    endpoint_url = back_off_context['kwargs']['endpoint_url']

    host, port = endpoint_url.split(":")
    # `endpoint_url` has listener port (i.e. secondary port + 1)
    secondary_endpoint = f"{host}:{int(port)-1}"

    global_heartbeater.downgrade_health_status(secondary_endpoint)
    
    health_status = global_heartbeater.get_health_status(secondary_endpoint)

    if health_status == heartbeats.HealthStatus.SUSPECTED:
        sleep_time = 5
    elif health_status == heartbeats.HealthStatus.UNHEALTHY:
        sleep_time = heartbeats.HEARTBEAT_INTERVAL

    logger.info(f"Retrying in {sleep_time} seconds.")
    time.sleep(sleep_time)


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

    def _enter(self):
        while self._state in (-1, 1):
            # It is draining or resetting, wait until done
            self._cond.wait()
        #see if the barrier is in a broken state
        if self._state < 0:
            raise threading.BrokenBarrierError
        assert self._state in [0, 4] 


class Replicator():

    secondary_endpoints_list: List[str] = []
    logger: logging.Logger
    message_id: int

    def __init__(self, secondary_endpoints_list, heartbeater: heartbeats.HeartBeater) -> None:
        self.logger = logging.getLogger(__name__)
        self.secondary_endpoints_list = secondary_endpoints_list
        global global_heartbeater
        global_heartbeater = heartbeater
        self.heartbeater = heartbeater

        self.message_id = 1


    def replicate(self, data: str, write_concern: int):
        message_id = self.message_id
        self.message_id += 1

        thread_barrier = ExtendedBarrier(write_concern, timeout=60)

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

    
    @backoff.on_exception(
        backoff.expo, 
        Exception,
        on_backoff=lambda back_off_context: retry_prepare(back_off_context),
        on_success=lambda back_off_context: global_heartbeater.set_health_status(
            endpoint_url=f"{back_off_context['kwargs']['endpoint_url'].split(':')[0]}:{int(back_off_context['kwargs']['endpoint_url'].split(':')[1])-1}",
            status=heartbeats.HealthStatus.HEALTHY
        )
    )
    def _replicate(self, message_id: int, data: str, endpoint_url: str, thread_barrier: ExtendedBarrier):
        host, port = endpoint_url.split(":")
        self.logger.info(f"Trying to replicate massage to {host}.")

        message = json.dumps({
            "message_id": message_id,
            "message": data
        })

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((host, int(port)))
            s.sendall(message.encode(encoding="utf-8"))

            response_data = s.recv(1024).decode("utf-8")
            self.logger.info(response_data)

            if response_data.startswith("Error"):
                raise RuntimeError

            s.close()

        try:
            thread_barrier.wait()
        except threading.BrokenBarrierError:
            return
