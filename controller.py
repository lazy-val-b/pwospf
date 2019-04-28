#!/usr/bin/env python

from threading import Thread, Event
from scapy.all import sendp
from scapy.all import Packet, Ether, IP, ARP
from async_sniff import sniff
from pwospf_protocoll import PWOSPFMetadata
import time

PWOSPF_OP_HELLO   = 0x0001
PWOSPF_OP_LSU = 0x0004

ALLSPFRouters = 0xe0000005 # "224.0.0.5"

class PWOSPFController(Thread):
    def __init__(self, sw, start_wait=0.3):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.start_wait = start_wait # time to wait for the controller to be listenning
        self.iface = sw.intfs[0].name
        self.port_for_mac = {}
        self.stop_event = Event()

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
        # pkt.show2()
        assert PWOSPFMetadata in pkt, "Should only receive packets from switch with special header"

        # Ignore packets that the CPU sends:
        # if pkt[PWOSPFMetadata].fromCpu == 1: return

        # if ARP in pkt:
        #     if pkt[ARP].op == ARP_OP_REQ:
        #         self.handleArpRequest(pkt)
        #     elif pkt[ARP].op == ARP_OP_REPLY:
        #         self.handleArpReply(pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        # assert PWOSPFMetadata in pkt, "Controller must send packets with special header"
        print pkt[PWOSPFMetadata]
        # pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        sniff(iface=self.iface, prn=self.handlePkt, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(PWOSPFController, self).start(*args, **kwargs)
        time.sleep(self.start_wait)
        self.testpacket()

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)

    def testpacket(self):
        f = Ether(dst="00:00:00:00:00:03")/IP(dst="10.0.0.3")
        e = f/PWOSPFMetadata()
        print "show newly creat4ed packet"
        e.show2()
        self.send(e)