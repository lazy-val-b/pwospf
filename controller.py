#!/usr/bin/env python

from threading import Thread, Event
from scapy.all import sendp
from scapy.all import Packet, Ether, IP, ARP
from async_sniff import sniff
from pwospf_protocoll import *
import time

PWOSPF_OP_HELLO   = 0x0001
PWOSPF_OP_LSU = 0x0004

class PWOSPFController(Thread):
    def __init__(self, sw, chost, helloint, mask, areaID, start_wait=0.3):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.start_wait = start_wait # time to wait for the controller to be listenning
        self.iface = sw.intfs[1].name
        self.port_for_mac = {}
        self.stop_event = Event()
        self.ifaces = {}
        self.chost = chost
        self.db = {
            'neighbours': [],
            'helloInt': helloint,
            'routerID': sw.intfs[0].IP(),
            'areaID': areaID,
            'mask': mask
        }



    def addMacAddr(self, mac, port):
        # Don't re-add the mac-port mapping if we already have it:
        if mac in self.port_for_mac: return

        self.sw.insertTableEntry(table_name='MyIngress.fwd_l2',
                match_fields={'hdr.ethernet.dstAddr': [mac]},
                action_name='MyIngress.set_egr',
                action_params={'port': port})
        self.port_for_mac[mac] = port

    def handleArpReply(self, pkt):
        # self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)

    def handleArpRequest(self, pkt):
        self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)

    def handlePkt(self, pkt):
        pkt.show2()
        assert PWOSPFHeader in pkt, "Should only receive packets from switch with special header"

        # Ignore packets that the CPU sends:
        # if pkt[PWOSPFHeader].fromCpu == 1: return

        # if ARP in pkt:
        #     if pkt[ARP].op == ARP_OP_REQ:
        #         self.handleArpRequest(pkt)
        #     elif pkt[ARP].op == ARP_OP_REPLY:
        #         self.handleArpReply(pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        assert PWOSPFHeader in pkt, "Controller must send packets with special header"
        # pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        sniff(iface=self.iface, prn=self.handlePkt, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(PWOSPFController, self).start(*args, **kwargs)
        time.sleep(self.start_wait)
        self.helloPacket()

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)

    def helloPacket(self):
        f = Ether()/IP(dst=ALLSPFRouters)

        # convert ip to hex representation
        splitIP = self.db['routerID'].split('.')
        routerID = '{:02X}{:02X}{:02X}{:02X}'.format(*map(int, splitIP))

        g = f/PWOSPFHeader(areaID=self.db['areaID'])

        h = g/PWOSPFHello(HelloInt=self.db['helloInt'])
        self.send(h)
