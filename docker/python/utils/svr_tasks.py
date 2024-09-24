import multiprocessing
import time
from datetime import datetime, timedelta, timezone

import utils.registered_funcs as reg_funcs

from .db_utils import DBHelper, ServerTasks
from .log_utils import log


class TaskQueue:
    def __init__(self, db_url):
        self.dbh = DBHelper(db_url)

    async def add_task(self, func, args, interval_seconds, is_oneshot=False):
        """Add a task to the queue and save it to the database."""
        next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
        task = ServerTasks(
            func_name=func.__name__,
            args=str(args),
            interval_s=interval_seconds,
            next_run_time=next_run_time,
            is_complete=False,
            is_oneshot=is_oneshot
        )
        await self.dbh.add_record(task)

    async def remove_task(self, task_id):
        """Remove a task from the queue and the database."""
        # Check if the task exists
        task = await self.dbh.query_with_filter(ServerTasks, ServerTasks.id ==
                                                task_id)

        if len(task) > 0:
            task = task[0]
            await self.dbh.delete_record(ServerTasks, ServerTasks.id ==
                                         task_id)
            log(f"Task [{task.id}] '{task.func_name}' removed from the queue",
                'success')
        else:
            log(f"Task with ID {task_id} not found", 'error')

    async def get_tasks(self):
        """Fetch the tasks from the database."""
        tasks = await self.dbh.list_records(ServerTasks)
        return tasks

    async def look_for_pending_tasks(self):
        """Check for pending tasks and run them."""
        tasks = await self.dbh.query_with_filter(ServerTasks,
                                                 ServerTasks.is_complete ==
                                                 False)
        log(f"Found {len(tasks)} pending tasks", 'info')
        for task in tasks:
            if datetime.now(timezone.utc) >= task.next_run_time:
                func = globals().get(task.func_name)
                if func:
                    args_tuple = eval(task.args)
                    func(*args_tuple)
                    task.next_run_time = datetime.now() + timedelta(
                        seconds=task.interval_s)
                    task.is_complete = True
                    await self.dbh.update_record(ServerTasks, task,
                                                 ServerTasks.id == task.id)

    async def run_tasks(self):
        """Run tasks at their scheduled intervals."""
        # At start, look for pending tasks that may have been missed
        log("Looking for pending tasks...", 'info')
        await self.look_for_pending_tasks()
        log("Starting task queue...", 'info')
        while True:
            tasks = await self.get_tasks()
            for task in tasks:
                if datetime.now(timezone.utc) >= task.next_run_time:
                    func = getattr(reg_funcs, task.func_name, None)
                    if callable(func):
                        log(f"QUEUED_TASK[{task.id}]: '{task.func_name}'", )
                        args_tuple = [task.args]
                        func(*args_tuple)  # Execute the task
                        task.is_complete = True
                        if task.is_oneshot:
                            await self.remove_task(task.id)
                        else:
                            # Reschedule the task
                            task.next_run_time = datetime.now() + timedelta(
                                seconds=task.interval_s)
                            task.is_complete = True
                            await self.dbh.update_record(ServerTasks, task,
                                                         ServerTasks.id == task.id)
                    else:
                        log(f"Task gloabal function: '{task.func_name}' not "
                            f"found", 'error')
            time.sleep(5)  # Check every 5 second

    async def clear_tasks(self):
        """Clear all tasks from the queue."""
        await self.dbh.clear_table(ServerTasks)

    def start(self):
        """Start the task queue as a subprocess."""
        process = multiprocessing.Process(target=self.run_tasks)
        process.start()
        return process
