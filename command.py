import subprocess
import traceback


def run_cmd(cmd, check=True, show_traceback=True):
    """Runs a shell command and returns (success, output)."""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if show_traceback:
            traceback.print_exc()
        return False, e.stderr
