from concurrent.futures import ThreadPoolExecutor, as_completed
from nornir.core.task import AggregatedResult, Task
from nornir.core.inventory import Host
from typing import List


# custom runner using as_completed 
class UpdateRunner:
    """
    ThreadedRunner runs the task over each host using threads
    Arguments:
        num_workers: number of threads to use
    """

    def __init__(self, num_workers: int = 20, updater=None) -> None:
        self.num_workers = num_workers
        self._updater = updater

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        """
        This is where the magic happens
        """
        # we instantiate the aggregated result
        result = AggregatedResult(task.name)
        host_count = len(hosts)
        host_idx = 1
        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {pool.submit(task.copy().start, host): host for host in hosts}
            for future in as_completed(futures):
                worker_result = future.result() 
                result[worker_result.host.name] = worker_result
                if task.name != "close_connections_task":
                    msg='completed'
                    if worker_result.failed:
                        msg = 'failed'
                    print(f'{worker_result.host.name} - {msg}.')
                    if self._updater is not None:
                        self._updater(f'{worker_result.host.name} - {msg}.','update')
                        self._updater(f'#{host_idx}/{host_count}.','progress')
                        host_idx += 1
        return result



