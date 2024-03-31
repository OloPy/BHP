# -*-coding:Utf-8 -*
"""
This is a mapper for wordpress from BHP book

improvement done:

improvement to do:
- manage script args with argparse
- modify default path
- modify some variables names
"""

import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = [".jpg", ".gif", ".png", ".css"]
TARGET = "http://boodelyboo.com:8080/"
THREAD = 10

answers = queue.Queue()
web_paths = queue.Queue()


def gather_paths():
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
            print(path)
            web_paths.put(path)


@contextlib.contextmanager
def chdir(path):
    """
    On enter, change directory to specified path
    On exit, change directory back to original
    """
    this_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(this_dir)


def main():
    with chdir("/tmp/BHP/wp/wordpress"):
        gather_paths()
    input('Press return to continue.')


if __name__ == '__main__':
    main()
