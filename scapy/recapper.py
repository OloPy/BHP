# -*-coding:Utf-8 -*

"""
Recapper.py from BHP book

this program search in pcap file images sent and save them to disk.

improvement done:

improvement to do:
- argparse to select file source and dest
"""

from scapy.all import TCP, rdpcap
import collections
import os
import re
import sys
import zlib

OUTDIR = '/tmp/BHP/collectedPict'
PCAPS = '/tmp/BHP'

Response = collections.namedtuple('response', ['header', 'payload'])


def get_header(payload):
    try:
        header_raw = payload[:payload.index(b'\r\n\r\n')+2]
    except ValueError:
        sys.stdout.write('-')
        sys.stdout.flush()
        return None
    header = dict(re.findall(r'(?P<name>.*?): (?P<value>.*?)\n\r', header_raw.decode()))
    if 'Content-Type' not in header:
        return None
    return header


def extract_content(Response, content_name='image'):
    pass


class Recapper:
    def __init__(self, fname):
        pass

    def get_responses(self):
        pass

    def write(self, content_name):
        pass


def main():
    pfile = os.path.join(PCAPS, 'packet.pcap')
    recapper = Recapper(pfile)
    recapper.get_responses()
    recapper.write('image')


if __name__ == '__main__':
    main()
