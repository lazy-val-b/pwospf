from threading import Thread, Event
from scapy.all import sendp
from scapy.all import Packet, Ether, IP, ARP
from async_sniff import sniff
from cpu_metadata import CPUMetadata
from pwospf_protocol import PWOSPF_HEADER, PWOSPF_HELLO, PWOSPF_LSU
import time

OSPF_HELLO = 1
OSPF_LSU = 4


class PWOSPFController(Thread):
    def __init__(self, sw, start_wait=0.3):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.start_wait = start_wait # time to wait for the controller to be listenning
        self.iface = sw.intfs[0].name #is this interface 0 or 1?
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

    def handlePWOSPFHello(self, pkt):
        # pkt.show2()
        # self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt) # why send?

    def handlePWOSPFLSU(self, pkt):
        # self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)

    def handlePkt(self, pkt):
        # pkt.show2()
        assert CPUMetadata in pkt, "Should only receive packets from switch with special header"

        # Ignore packets that the CPU sends:
        # if pkt[CPUMetadata].fromCpu == 1: return

        if PWOSPF_HEADER in pkt:
            # print(pkt[PWOSPF_HEADER].type)
            
            if pkt[PWOSPF_HEADER].type == OSPF_HELLO:
                self.handlePWOSPFHello(pkt)
            elif pkt[PWOSPF_HEADER].type == OSPF_LSU:
                self.handlePWOSPFLSU(pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        assert CPUMetadata in pkt, "Controller must send packets with special header"
        pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        sniff(iface=self.iface, prn=self.handlePkt, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(PWOSPFController, self).start(*args, **kwargs)
        time.sleep(self.start_wait)

        hello = Ether()/CPUMetadata()/IP(dst='10.0.0.2')/PWOSPF_HEADER()/PWOSPF_HELLO()
        # self.send(hello)
        # hello.show2()

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)
