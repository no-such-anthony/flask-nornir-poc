from concurrent.futures import ThreadPoolExecutor, as_completed
from nornir.core.task import AggregatedResult, Task
from nornir.core.inventory import Host
from typing import List


# custom runner using as_completed 
class runner_helper:
    """
    ThreadedRunner runs the task over each host using threads
    Arguments:
        num_workers: number of threads to use
    """

    def __init__(self, num_workers: int = 20, progress_queue=None) -> None:
        self.num_workers = num_workers
        self._q = progress_queue

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        """
        This is where the magic happens
        """
        # we instantiate the aggregated result
        result = AggregatedResult(task.name)
        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {pool.submit(task.copy().start, host): host for host in hosts}
            for future in as_completed(futures):
                worker_result = future.result() 
                result[worker_result.host.name] = worker_result
                if task.name != "close_connections_task":
                    if worker_result.failed:
                        if self._q is not None:
                            self._q.put(f'{worker_result.host.name} - fail')
                        print(f'{worker_result.host.name} - fail')
                    else:
                        if self._q is not None:
                            self._q.put(f'{worker_result.host.name} - success')
                        print(f'{worker_result.host.name} - success')

        return result




