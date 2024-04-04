# -*-coding:Utf-8 -*
"""
This is a mapper for wordpress from BHP book

improvement done:
- manage script args with argparse
- modify default path
- modify some variables names
- Add count for found entries
- add % of done with a tread
- check if it's a wordpress
- allow ctrl-c to stop process

improvement to do:
- add filter arg to reduce numbers of paths
"""

import argparse
import contextlib
import os
import queue
import requests
import threading
import time

from pyPYPM import utils

FILTERED = [".jpg", ".gif", ".png", ".css"]
PROGRESS = 0
URIFOUND = 0

answers = queue.Queue()
web_paths = queue.Queue()


@contextlib.contextmanager
def chdir(path: str):
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


def checkIfTargetIsWordpress(url: str) -> int:
    """
    Check if URL can be joined and if it's a wordpress. Return 0 if all is ok, 1 if cant be joined and 2 if not a wp
    """
    try:
        answer = requests.get(url)
    except requests.exceptions.ConnectionError:
        return 1
    if answer.status_code != 200:
        return 1
    if answer.text.find('WordPress') == -1:
        return 2
    return 0


def gather_paths() -> int:
    i = 0
    for root, _, files in os.walk('.'):
        for fileName in files:
            if os.path.splitext(fileName)[1] in FILTERED:
                continue
            path = os.path.join(root, fileName)
            if path.startswith('.'):
                path = path[1:]
            web_paths.put(path)
            i += 1
    print(f'Found {i} possible path!')
    return i


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
    parser.add_argument('targetUrl', help='The target URL.')
    parser.add_argument('-t', '--threads', type=int, default=10, help='The number of threads (request in "same" time.')
    parser.add_argument('-w', '--workingDir', default=sourcePath, help=f'The working dir. Default is {sourcePath}')
    parser.add_argument(
        '-o',
        '--output',
        default=defaultFile,
        help=f'The file where URI will be write. Default is {defaultFile}'
    )
    return parser.parse_args()


def printStatus(maximum: int, threads: int) -> None:
    global PROGRESS
    global URIFOUND
    checkUrlProgress = utils.ProgressBar(maximum, afterStr=f'of {maximum} ')
    while not web_paths.empty():
        checkUrlProgress.updateStateValue(PROGRESS)
        print(f'{checkUrlProgress}', end='')
    checkUrlProgress.updateStateValue(PROGRESS+threads)
    print(f'{checkUrlProgress}', end='')
    print(f'- Found {URIFOUND} uri.')


def run(target: str, threads: int, maximum: int) -> None:
    myThreads = list()
    print(f'Spawning thread: ', end=" ")
    try:
        for i in range(threads):
            print(i, end=" ")
            t = threading.Thread(target=test_remote, args=[target,])
            myThreads.append(t)
            t.start()
        progressThread = threading.Thread(target=printStatus, args=[maximum, threads])
        myThreads.append(progressThread)
        progressThread.start()
        for thread in myThreads:
            thread.join()
    except KeyboardInterrupt:
        print("User stop process!")
        web_paths.queue.clear()


def test_remote(target: str) -> None:
    global PROGRESS
    global URIFOUND
    while not web_paths.empty():
        path = web_paths.get()
        url = f'{target}{path}'
        time.sleep(2)
        r = requests.get(url)
        PROGRESS += 1
        if r.status_code == 200:
            answers.put(url)
            URIFOUND += 1


def main() -> None:
    myArgs = manageArgs()
    urlStatus = checkIfTargetIsWordpress(myArgs.targetUrl)
    if urlStatus == 1:
        print(f"{myArgs.targetUrl} cant be joined!")
        exit(2)
    elif urlStatus == 2:
        print(f"{myArgs.targetUrl} is not a wordPress!")
        exit(2)
    wpPath = os.path.join(myArgs.workingDir, "wp/wordpress")
    if not os.path.exists(wpPath):
        print(f'{wpPath} does not exist!')
        exit(1)
    with chdir(wpPath):
        numberOfPath = gather_paths()
    try:
        input('Press return to continue or CTR-C to stop.')
    except KeyboardInterrupt:
        exit(0)
    run(myArgs.targetUrl, myArgs.threads, numberOfPath)
    with open(myArgs.output, 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
    print(f'Done!\nresults saved in {myArgs.output}.')


if __name__ == '__main__':
    main()
