# -*-coding:Utf-8 -*
"""
This is a mapper for wordpress from BHP book

improvement done:
- manage script args with argparse
- modify default path
- modify some variables names

improvement to do:
- Add count for found entries
- add % of done with a tread
- check if it's a wordpress
"""

import argparse
import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = [".jpg", ".gif", ".png", ".css"]
# TARGET = "http://boodelyboo.com/"
# THREADS = 10

answers = queue.Queue()
web_paths = queue.Queue()


def gather_paths():
    i = 0
    for root, _, files in os.walk('.'):
        for fileName in files:
            if os.path.splitext(fileName)[1] in FILTERED:
                continue
            path = os.path.join(root, fileName)
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


def manageArgs() -> argparse.Namespace:
    if os.name == 'nt':
        sourcePath = os.path.join(os.environ["TEMP"], "BHP")
    else:
        sourcePath = '/tmp/BHP'
    if not os.path.exists(sourcePath):
        os.mkdir(sourcePath)
    defaultFile = os.path.join(sourcePath, 'myanswer.txt')
    descTxt = "BHP Word Press (wp) Mapper.\n"
    descTxt += f"You need to download and extract wp source file in working dir (default:{sourcePath})*.\n"
    descTxt += f"Default output root is {sourcePath}"
    parser = argparse.ArgumentParser(
        description=descTxt,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python3 mapper.py -t 10 -w /tmp -o /tmp/toto.txt <targetUrl>\n')
    parser.add_argument('targetUrl', required=True, help='The target URL.')
    parser.add_argument('-t', '--threads', type=int, default=10, help='The number of threads (request in "same" time.')
    parser.add_argument('-w', '--workingDir', default=sourcePath, help=f'The working dir. Default is {sourcePath}')
    parser.add_argument(
        '-o',
        '--output',
        default=defaultFile,
        help=f'The file where URI will be write. Default is {defaultFile}'
    )
    return parser.parse_args()


def run(target, threads):
    myThreads = list()
    for i in range(threads):
        print(f'Spawning thread {i}')
        t = threading.Thread(target=test_remote, args=[target,])
        myThreads.append(t)
        t.start()
    for thread in myThreads:
        thread.join()


def test_remote(target):
    while not web_paths.empty():
        path = web_paths.get()
        url = f'{target}{path}'
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('-')
        sys.stdout.flush()


def main():
    myArgs = manageArgs()
    with chdir(os.path.join(myArgs.workingDir, "wp/wordpress")):
        gather_paths()
    input('Press return to continue.')
    run(myArgs.targetUrl, myArgs.threads)
    with open(myArgs.output, 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
    print('Done!')


if __name__ == '__main__':
    main()
