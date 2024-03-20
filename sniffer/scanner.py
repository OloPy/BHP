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
- add messages

Improvement to do:
- add parameters to manage subnet and message
- get current subnet as default
- MESSAGE and SUBNET are global var. I want to modify them to be init in scanner object

"""

import ipaddress
import os
import socket
import struct
import sys
import threading
import time


# Target subnet
SUBNET = "10.66.20.0/24"
# magic string we'll check ICMP response for
MESSAGE = "Python3Rules!"


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


def udpSender():
    """
    this sprays out UDP datagrams with our magic message
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        for ip in ipaddress.ip_network(SUBNET).hosts():
            sender.sendto(bytes(MESSAGE, 'utf-8'), (str(ip), 65212))


class Scanner:
    def __init__(self, host):
        self.host = host
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
                        if ipaddress.ip_address(ip_header.src_address) in ipaddress.IPv4Network(SUBNET):
                            # make sure it as our magic message
                            if raw_buffer[len(raw_buffer) - len(MESSAGE):] == bytes(MESSAGE, 'utf-8'):
                                tgt = str(ip_header.src_address)
                                if tgt != self.host and tgt not in hosts_up:
                                    hosts_up.add(str(ip_header.src_address))
                                    print(f'Host Up: {tgt}')
        # handle Ctrl+c
        except KeyboardInterrupt:
            # stopping capture with Ctrl+c
            # if we're on windows, turn off promiscuous mode
            if os.name == 'nt':
                self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            print('\n User interrupted.')
            if hosts_up:
                print(f'\n\nSummary: Hosts up in {SUBNET}:')
                for host in sorted(hosts_up):
                    print(f'\t- {host}')
            print('')
            exit(0)


def main() -> None:
    # Host to listen on
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = socket.gethostbyname(socket.gethostname())
    print(f'[+] Using {host} as source host.')
    s = Scanner(host)
    print(f'[!] Waiting 5 sec.')
    time.sleep(5)
    print(f'[!] Starting UDP send.')
    t = threading.Thread(target=udpSender)
    t.start()
    print(f'[!] Starting sniffer.')
    s.sniff()


if __name__ == '__main__':
    main()
