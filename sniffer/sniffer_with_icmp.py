# -*-coding:Utf-8 -*

"""
This is a basic sniffer from BHP book
on linux, with wifi:
root@xflyer2:~ # ip link set wlo1 down
root@xflyer2:~ # iw wlo1 set monitor none
root@xflyer2:~ # ip link set wlo1 up

To reactivate:
root@xflyer2:~ # ip link set wlo1 down
root@xflyer2:~ # iw wlo1 set type managed
root@xflyer2:~ # ip link set wlo1 up

"""

import ipaddress
import os
import socket
import struct
import sys


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
            print(f'Protocl number not recognized: {self.protocol_num}, {err}')
            self.protocol = str(self.protocol_num)


class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]


def sniff(host):
    # Create a raw socket, bin to public interface
    if os.name == 'nt':
        socket_protocol = socket.IPPROTO_IP
    else:
        socket_protocol = socket.IPPROTO_ICMP
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    sniffer.bind((host, 0))
    # Include IP header in capture
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    # read packet
    try:
        print(f'Starting listen on {host}')
        while True:
            # read packet
            raw_buffer = sniffer.recvfrom(65535)[0]
            # create an IP header from first 20 bytes
            ip_header = IP(raw_buffer[:20])
            if ip_header.protocol == 'ICMP':
                toPrint = f'Protocol: {ip_header.protocol} {ip_header.src_address} -> {ip_header.dst_address}'
                print(toPrint)
                print(f'Version: {ip_header.ver}')
                print(f'Header length: {ip_header.ihl} TTL: {ip_header.ttl}')
                # Calculate where our ICMP packet starts
                offset = ip_header.ihl * 4
                buf = raw_buffer[offset:offset + 8]
                # create our ICMP structure
                icmp_header = ICMP(buf)
                print(f'ICMP -> Type: {icmp_header.type} Code: {icmp_header.code}\n')
    except KeyboardInterrupt:
        # stopping capture with Ctrl+c
        # if we're on windows, turn off promiscious mode
        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        print('End of capture.')
        exit(0)


def main():
    # Host to listen on
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '127.0.0.1'
    sniff(host)


if __name__ == '__main__':
    main()
