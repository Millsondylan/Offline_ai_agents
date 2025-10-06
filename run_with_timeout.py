import subprocess
import sys

if __name__ == "__main__":
    try:
        subprocess.run(sys.argv[1:], timeout=30)
    except subprocess.TimeoutExpired:
        print("Command timed out")
