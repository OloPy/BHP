# -*-coding:Utf-8 -*

"""
This is a network scanner from BHP book.
on linux, with wi-fi:
root@xflyer2:~ # ip link set wlo1 down
root@xflyer2:~ # iw wlo1 set monitor none
root@xflyer2:~ # ip link set wlo1 up

To reactivate:
root@xflyer2:~ # ip link set wlo1 down
root@xflyer2:~ # iw wlo1 set type managed
root@xflyer2:~ # ip link set wlo1 up

Improvement done:
- default address is the first found
- add parameters to manage subnet, message and source IP

Improvement to do:
- search ARP of found IP
"""

import argparse
import ipaddress
import os
import socket
import struct
import threading
import time


def manageArguments() -> argparse.Namespace:
    """
    Function to parse arguments
    :return: a parse_args object
    """
    parser = argparse.ArgumentParser(
        description='BHP Network Scanner.\n Need root or administrator right.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python3 proxy.py -s 192.168.0.1 -m "toto" 192.168.0.0/24\n')
    parser.add_argument('subnet', help='The subnet to scan.')
    parser.add_argument(
        '-s',
        '--host',
        default=socket.gethostbyname(socket.gethostname()),
        help='The source of the scann. Use IP assigned to hostname in hosts file or first IP if not.'
    )
    parser.add_argument('-m', '--message', default="Python3Rules!", help='The message to validate it\'s our scan.')
    return parser.parse_args()


class IP:
    def __init__(self, buff=None):
        header = struct.unpack('<BBHHHBBH4s4s', buff)
        self.ver = header[0] >> 4
        self.ihl = header[0] & 0xF
        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]
        # Human-readable IP Address
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)
        # map protocol constants to their names
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except KeyError as err:
            print(f'Protocol number not recognized: {self.protocol_num}, {err}')
            self.protocol = str(self.protocol_num)


class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]


def udpSender(subnet: str, message: str) -> None:
    """
    this sprays out UDP datagrams with our magic message
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        for ip in ipaddress.ip_network(subnet).hosts():
            sender.sendto(bytes(message, 'utf-8'), (str(ip), 65212))


class Scanner:
    def __init__(self, host, subnet, message):
        self.host = host
        self.subnet = subnet
        self.message = message
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IP
        else:
            socket_protocol = socket.IPPROTO_ICMP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
        self.socket.bind((host, 0))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        if os.name == 'nt':
            self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    def sniff(self):
        hosts_up = {f'{str(self.host)} *'}
        try:
            while True:
                # read packet
                raw_buffer = self.socket.recvfrom(65535)[0]
                # create an IP header from first 20 bytes
                ip_header = IP(raw_buffer[:20])
                if ip_header.protocol == 'ICMP':
                    # Calculate where our ICMP packet starts
                    offset = ip_header.ihl * 4
                    buf = raw_buffer[offset:offset + 8]
                    # create our ICMP structure
                    icmp_header = ICMP(buf)
                    if icmp_header.code == 3 and icmp_header.type == 3:
                        if ipaddress.ip_address(ip_header.src_address) in ipaddress.IPv4Network(self.subnet):
                            # make sure it as our magic message
                            if raw_buffer[len(raw_buffer) - len(self.message):] == bytes(self.message, 'utf-8'):
                                tgt = str(ip_header.src_address)
                                if tgt != self.host and tgt not in hosts_up:
                                    hosts_up.add(str(ip_header.src_address))
                                    print(f'\tHost Up: {tgt}')
        except KeyboardInterrupt:
            # stopping capture with Ctrl+c
            # if we're on windows, turn off promiscuous mode
            if os.name == 'nt':
                self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            print('\nUser interrupted.')
            if hosts_up:
                print(f'Summary: Hosts up in {self.subnet}:')
                for host in sorted(hosts_up):
                    print(f'\t{host}')
            print('')
            exit(0)


def main() -> None:
    # Host to listen on
    myArgs = manageArguments()
    print(f'Using {myArgs.host} as source host.')
    print(f'network to scan is {myArgs.subnet}.')
    try:
        s = Scanner(myArgs.host, myArgs.subnet, myArgs.message)
    except PermissionError as err:
        print(f'We need root or administrator account on local machine to run this script!')
        exit(1)
    print(f'Waiting 5 sec.')
    time.sleep(5)
    print(f'Starting UDP send.')
    t = threading.Thread(target=udpSender, args=(myArgs.subnet, myArgs.message))
    t.start()
    print(f'Starting sniffer.')
    s.sniff()


if __name__ == '__main__':
    main()
