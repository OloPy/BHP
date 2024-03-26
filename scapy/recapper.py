# -*-coding:Utf-8 -*

"""
Recapper.py from BHP book

this program search in pcap file images sent and save them to disk.
A nice test:
- generate a pcap file
    tcpdump -i wlo1 -s 65535 -w packet.pcap
- site to visit: http://www.josephwcarrillo.com/

improvement done:
- display modified to see errors as _ when packet is not tcp, - when packet header cant be found and F when we found
an image. We can uncomment line to add X when we don't have error.
- argparse to select file source and dest

improvement to do:

"""

from scapy.all import TCP, rdpcap
import argparse
import collections
import os
import re
import sys
import zlib

Response = collections.namedtuple('response', ['header', 'payload'])


def manageArguments() -> argparse.Namespace:
    """
    Function to parse arguments
    :return: a parse_args object
    """
    if os.name == 'nt':
        sourcePath = os.path.join(os.environ["TEMP"], "BHP")
    else:
        sourcePath = '/tmp/BHP'
    if not os.path.exists(sourcePath):
        os.mkdir(sourcePath)
    defaultFile = os.path.join(sourcePath, 'packet.pcap')
    outputDir = os.path.join(sourcePath, 'output')
    parser = argparse.ArgumentParser(
        description='BHP recapper. this script is used to recover data from pcap file.\n Need root or administrator '
                    'right.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python3 proxy.py -s /tmp/BHP/packet.pcap -o /tmp/BHP/outPut \n')
    parser.add_argument(
        '-s',
        '--sourceFile',
        default=defaultFile,
        help=f'The pcap file with datas. default is {defaultFile}'
    )
    parser.add_argument('-o', '--outputDir', default=outputDir, help='The folder where datas are saved.')
    return parser.parse_args()


def get_header(payload):
    try:
        header_raw = payload[:payload.index(b'\r\n\r\n')+2]
    except ValueError:
        sys.stdout.write('-')
        sys.stdout.flush()
        return None
    header = dict(re.findall(r'(?P<name>.*?): (?P<value>.*?)\r\n', header_raw.decode()))
    if 'Content-Type' not in header:
        return None
    return header


def extract_content(Response: collections.namedtuple, content_name='image'):
    content, content_type = None, None
    if content_name in Response.header['Content-Type']:
        content_type = Response.header['Content-Type'].split('/')[1]
        content = Response.payload[Response.payload.index(b'\r\n\r\n')+4:]
        if 'Content-Encoding' in Response.header:
            if Response.header['Content-Encoding'] == 'gzip':
                content = zlib.decompress(Response.payload, zlib.MAX_WBITS | 32)
            elif Response.header['Content-Encoding'] == 'deflate':
                content = zlib.decompress(Response.payload)
    return content, content_type


class Recapper:
    def __init__(self, fname):
        pcap = rdpcap(fname)
        self.sessions = pcap.sessions()
        self.responses = list()

    def get_responses(self):
        print(f'We have {len(self.sessions)} sessions.')
        for session in self.sessions:
            payload = b''
            for packet in self.sessions[session]:
                try:
                    if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                        payload += bytes(packet[TCP].payload)
                except IndexError:
                    print('_', end='')
                #else:
                    #print('X', end='')
            if payload:
                header = get_header(payload)
                if header is None:
                    continue
                self.responses.append(Response(header=header, payload=payload))
                print('F', end='')
        print('\n')

    def write(self, content_name, outputDir):
        if not os.path.exists(outputDir):
            os.mkdir(outputDir)
        for i, response in enumerate(self.responses):
            content, content_type = extract_content(response, content_name)
            if content and content_type:
                ofname = os.path.join(outputDir, f'ex_{i}.{content_type}')
                print(f'Writing {ofname} on disk.')
                with open(ofname, 'wb') as f:
                    f.write(content)


def main():
    myArgs = manageArguments()
    print(f"Extracting data from {myArgs.sourceFile}")
    pcapfile = myArgs.sourceFile
    recapper = Recapper(pcapfile)
    recapper.get_responses()
    print(f"Saving data to {myArgs.outputDir}")
    recapper.write('image', myArgs.outputDir)


if __name__ == '__main__':
    main()
