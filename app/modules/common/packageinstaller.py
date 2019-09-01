import subprocess
import sys

def install(package):
    if "=" in package:
        subprocess.call([sys.executable, "-m", "pip", "install", package])
    else:
        subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", package])