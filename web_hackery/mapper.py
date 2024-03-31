# -*-coding:Utf-8 -*
"""
This is a mapper for wordpress from BHP book

improvement done:

improvement to do:
- manage script args with argparse
- modify default path
- modify some variables names
- Add count for found entries
- add % of done with a tread
"""

import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = [".jpg", ".gif", ".png", ".css"]
TARGET = "http://boodelyboo.com/"
THREADS = 10

answers = queue.Queue()
web_paths = queue.Queue()


def gather_paths():
    i = 0
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
            print(path)
            web_paths.put(path)
            i += 1
    print(f'Found {i} path!')


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


def manageArgs():
    pass


def run():
    myThreads = list()
    for i in range(THREADS):
        print(f'Spawning thread {i}')
        t = threading.Thread(target=test_remote)
        myThreads.append(t)
        t.start()
    for thread in myThreads:
        thread.join()


def test_remote():
    while not web_paths.empty():
        path = web_paths.get()
        url = f'{TARGET}{path}'
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('-')
        sys.stdout.flush()


def main():
    with chdir("/tmp/BHP/wp/wordpress"):
        gather_paths()
    input('Press return to continue.')
    run()
    with open('/tmp/BHP/myanswer.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
    print('Done!')


if __name__ == '__main__':
    main()
