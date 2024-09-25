import atexit
import os
import signal
import subprocess
from time import sleep

# List to store subprocesses
processes = []


def kill_subprocesses():
    """Forcefully kill all subprocesses using SIGKILL."""
    for proc in processes:
        if proc.poll() is None:  # Check if process is still running
            print(f"Killing process group {proc.pid}")
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


# Register the kill function to be called on exit
atexit.register(kill_subprocesses)


def run_subprocess(command):
    """Run a subprocess and append it to the list of running processes."""
    # Use os.setsid to create a new process group for the subprocess
    proc = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
    processes.append(proc)


if __name__ == '__main__':
    try:
        # Run each script as a subprocess
        run_subprocess("python3 init_db.py")
        run_subprocess("python3 -m streamlit run './main.py'")
        # Wait for the streamlit server to start, ensuring the
        # database is initialized before running the task monitor
        sleep(2)
        run_subprocess("python3 start_task_monitor.py")

        # Wait for subprocesses to finish (block the main thread)
        for proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("KeyboardInterrupt received, killing subprocesses...")
    finally:
        # Ensure all subprocesses are killed on exit
        kill_subprocesses()
