from enum import Enum
import logging
import threading
from typing import Dict, List

import subprocess


HEARTBEAT_INTERVAL = 5 # seconds


class HealthStatus(Enum):
    HEALTHY = 'node_healthy'
    SUSPECTED = 'node_suspected'
    UNHEALTHY = 'node_unhealthy'


class HeartBeater:

    secondary_endpoints_list: List[str] = []
    secondary_health_status_dict: Dict[str, HealthStatus] = {}

    def __init__(self, secondary_endpoints_list) -> None:
        self.logger = logging.getLogger(__name__)
        
        self.secondary_endpoints_list = secondary_endpoints_list
        self.secondary_health_status_dict = {url: HealthStatus.HEALTHY for url in self.secondary_endpoints_list}
        self.logger.info(self.secondary_health_status_dict)

        self._start_health_checks()

    def ping(self, host: str):
        response = subprocess.call(['ping', '-c', '2', '-W', '1', host.split(":")[0]], stdout=subprocess.DEVNULL)
        return response == 0


    def get_health_status(self, endpoint_url: str):
        return self.secondary_health_status_dict[endpoint_url]

    
    def set_health_status(self, endpoint_url: str, status: HealthStatus):
        if not isinstance(status, HealthStatus):
            raise TypeError('Status must be a `HealthStatus`')
        if self.secondary_health_status_dict[endpoint_url] != status:
            self.logger.warning(f"Secondary node on {endpoint_url} is {status.name} now!")
        self.secondary_health_status_dict[endpoint_url] = status

    
    def get_all_health_statuses(self):
        return self.secondary_health_status_dict


    def downgrade_health_status(self, endpoint_url: str):
        if self.get_health_status(endpoint_url) == HealthStatus.HEALTHY:
            self.set_health_status(endpoint_url, HealthStatus.SUSPECTED)

        elif self.get_health_status(endpoint_url) == HealthStatus.SUSPECTED:
            self.set_health_status(endpoint_url, HealthStatus.UNHEALTHY)

    
    def _log_health_statuses(self):
        status_dict = self.get_all_health_statuses()
        log = "Current secondaries statuses:"

        for url, status in status_dict.items():
            log += f" {url} - {status.name};"

        self.logger.info(log)


    def _start_health_checks(self):
        health_check_thread = threading.Thread(target=self._health_check, name="Health Checks")
        health_check_thread.start()

        self.logger.info("Health Checks thread has successfuly started.")


    def _health_check(self):
        while True:
            self._log_health_statuses()
            for endpoint_url in self.secondary_endpoints_list:
                is_endpoint_alive = self.ping(endpoint_url)

                if is_endpoint_alive:
                    if self.get_health_status(endpoint_url) in [HealthStatus.SUSPECTED, HealthStatus.UNHEALTHY]:
                        self.logger.info(f"Secondary node on {endpoint_url} is back now!")
                        self.set_health_status(endpoint_url, HealthStatus.HEALTHY)
                    continue

                self.downgrade_health_status(endpoint_url)

            threading.Event().wait(HEARTBEAT_INTERVAL)
