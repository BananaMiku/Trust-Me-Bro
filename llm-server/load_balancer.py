import os
import time
import psutil
import requests
import multiprocessing as mp
from multiprocessing import Process, Queue, Manager, cpu_count
from typing import Optional, Dict, Any

# tuning
FREE_CPU_THRESHOLD = 10.0
CPU_SAMPLE_INTERVAL = 0.2
WORKER_STARTUP_DELAY = 0.05


def _worker_loop(worker_id: int, tasks_q: Queue, status_dict, wrapper_port: int):
    # try to set affinity on Linux
    try:
        num_cores = os.cpu_count() or 1
        core = worker_id % num_cores
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(0, {core})
            status_dict[worker_id]['core'] = core
        else:
            status_dict[worker_id]['core'] = None
    except Exception:
        status_dict[worker_id]['core'] = None

    wrapper_url = f"http://127.0.0.1:{wrapper_port}/"

    while True:
        task = tasks_q.get()
        if task is None:
            break

        # mark busy
        status_dict[worker_id]['busy'] = True
        status_dict[worker_id]['current_uuid'] = task.get('uuid')
        status_dict[worker_id]['last_start'] = time.time()

        # forward the internal request to the wrapper (blocking)
        try:
            # task is dict already serializable
            requests.post(wrapper_url, json=task, timeout=30)
        except Exception:
            pass

        # done
        status_dict[worker_id]['busy'] = False
        status_dict[worker_id]['current_uuid'] = None
        status_dict[worker_id]['last_end'] = time.time()


class LoadBalancer:
    def __init__(self, num_workers: Optional[int] = None, wrapper_port: int = 3222):
        if num_workers is None:
            num_workers = cpu_count() or 1

        self.manager = Manager()
        self.status = self.manager.dict()
        self.tasks = {}
        self.processes = []
        self.wrapper_port = wrapper_port

        for wid in range(num_workers):
            q = Queue()
            self.tasks[wid] = q
            self.status[wid] = self.manager.dict({
                'busy': False,
                'core': None,
                'current_uuid': None,
                'last_start': None,
                'last_end': None,
            })
            p = Process(target=_worker_loop, args=(wid, q, self.status, self.wrapper_port))
            p.daemon = True
            p.start()
            self.processes.append((wid, p))
            time.sleep(WORKER_STARTUP_DELAY)

    def pick_worker(self) -> int:
        # prefer free worker
        for wid, st in list(self.status.items()):
            if not st['busy']:
                return wid

        # sample per-core cpu and pick worker on least-loaded core
        per_core = psutil.cpu_percent(interval=CPU_SAMPLE_INTERVAL, percpu=True)
        core_to_workers = {}
        for wid, st in list(self.status.items()):
            core = st.get('core')
            core_to_workers.setdefault(core, []).append((wid, st))

        best_core = None
        best_cpu = 1e9
        for core, workers in core_to_workers.items():
            if core is None:
                cpu_val = max(per_core) if per_core else 100.0
            else:
                cpu_val = per_core[core] if core < len(per_core) else 100.0
            if workers and cpu_val < best_cpu:
                best_cpu = cpu_val
                best_core = core

        candidates = core_to_workers.get(best_core) or []
        if candidates:
            # pick earliest last_end
            candidates.sort(key=lambda w: w[1].get('last_end') or 0)
            return candidates[0][0]

        # fallback
        return next(iter(self.tasks.keys()))

    def enqueue(self, task: Dict[str, Any]) -> int:
        wid = self.pick_worker()
        self.tasks[wid].put(task)
        return wid

    def shutdown(self):
        for wid, q in self.tasks.items():
            q.put(None)
        for wid, p in self.processes:
            p.join(timeout=1)
