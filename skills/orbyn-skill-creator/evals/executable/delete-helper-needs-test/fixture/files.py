"""Small file helpers."""
import os


def list_files(directory):
    return sorted(n for n in os.listdir(directory) if os.path.isfile(os.path.join(directory, n)))
