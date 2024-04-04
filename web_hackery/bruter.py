# -*-coding:Utf-8 -*
"""
http folder brutter from BHP
initially it use SVNDigger.zip file from https://www.netsparker.com/s/research/SVNDigger.zip (dead today...)
default target from book: http://testphp.vulnweb.com

There is many tool doing that better, so I probably won't improve this one...

improvement done:

to improve:
- add argument parsers...
- make CTRL-X work
- Improve display
- implement recursivity
"""

import queue
import requests
import threading
import sys

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
TARGET = "http://testphp.vulnweb.com"
THREADS = 50
WORDLIST = "/home/wolf/myGit/gitHubTools/SecLists/Discovery/Web-Content/common.txt"


def get_words(resume: str=None) -> queue.Queue:
    def extend_words(aword: str):
        if "." in aword:
            words.put(f'/{aword}')
        else:
            words.put(f'/{aword}/')
        for extension in EXTENSIONS:
            words.put(f'/{aword}{extension}')

    with open(WORDLIST, 'r') as f:
        raw_words = f.read()
    found_resume = False
    words = queue.Queue()
    for word in raw_words.split():
        if resume is not None:
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Resuming wordlist from: {resume}')
        else:
            print(word)
        extend_words(word)
    return words


def dir_bruter(words: queue.Queue):
    headers = {'User-Agent': AGENT}
    while not words.empty():
        url = f'{TARGET}{words.get()}'
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            sys.stderr.write('x')
            sys.stdout.flush()
            continue
        if r.status_code == 200:
            print(f'\nSuccess {r.status_code} => {url}')
        elif r.status_code == 404:
            sys.stderr.write('.');
            sys.stdout.flush()
        else:
            print(f'\n{r.status_code} => {url}')


def main() -> None:
    words = get_words()
    input('Press return to continue.')
    for _ in range(THREADS):
        t = threading.Thread(target=dir_bruter, args=(words,))
        t.start()


if __name__ == '__main__':
    main()