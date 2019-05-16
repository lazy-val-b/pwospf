#!/usr/bin/env python

from threading import Thread, Event, Timer
from scapy.all import sendp
from scapy.all import Packet, Ether, IP, ARP
from async_sniff import sniff
from pwospf_protocoll import *
from cpu_metadata import *
import time
import pdb


PWOSPF_OP_HELLO   = 0x0001
PWOSPF_OP_LSU = 0x0004

class PWOSPFController(Thread):
    def __init__(self, sw, chost, helloint, mask, areaID, net, rid=0, start_wait=0.3 ):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.start_wait = start_wait # time to wait for the controller to be listenning
        self.iface = sw.intfs[1].name
        self.port_for_mac = {}
        self.stop_event = Event()
        self.ifaces = {}
        self.chost = chost
        self.db = {
            'myNodes': [],
            'neighbours': [],
            'helloInt': helloint,
            'routerID': rid,
            'areaID': areaID,
            'mask': mask,
            'lsuInt': 30
        }
        prev_dict = self.dijkstra(net.topo.nodes(), net.topo.links(), self.sw.name)
        self.setupTopo(prev_dict, net, self.sw.name)
        self.setupMulticast(10)


    def dijkstra(self, V, E, me):
        D = {}
        p = {}
        for node in V:
            D[node] = float('inf')
            p[node] = None
            for edge in E:
                if me in edge:
                    if node in edge:
                        D[node] = 1
                        p[node] = me
        D[me] = 0
        checked_nodes = set()
        checked_nodes.add(me)

        while checked_nodes != set(V):
            min_distance_node = None
            min_distance = float('inf')
            for key in V:
                if key not in checked_nodes:
                    if (D[key] <= min_distance):
                        min_distance_node = key
                        min_distance = D[key]
            checked_nodes.add(min_distance_node)
            for edge in E:
                if min_distance_node in edge:
                    neighbour = edge[0] if edge[0] != min_distance_node else edge[1]
                    if neighbour not in checked_nodes:
                        if (D[min_distance_node] + 1 < D[neighbour]):
                            D[neighbour] = D[min_distance_node] + 1
                            p[neighbour] = min_distance_node

        return p

    def setupTopo(self, prev_dict, net, me):
        for key in prev_dict:
            if key != me:
                prev_node_name = prev_dict[key]
                node = net.get(key)
                if prev_node_name != me:
                    if not ('isSwitch' in net.topo.nodeInfo(key) or 'isSwitch' in net.topo.nodeInfo(prev_node_name)):
                        self.addMacAddr(node.MAC(), node.IP(), net.topo.linkInfo(prev_node_name, key)['port2'])
                else:
                    if not 'isSwitch' in net.topo.nodeInfo(key):
                        self.addMacAddr(node.MAC(), node.IP(), net.topo.linkInfo(me, key)['port2'])



    def addMacAddr(self, mac, ip, port):
        # Don't re-add the mac-port mapping if we already have it:
        if mac in self.port_for_mac: return

        self.sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [ip, 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': mac,
                                        'port': port})
        self.port_for_mac[mac] = port

    def setupMulticast(self, mgid):
        self.sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                            match_fields={'hdr.ipv4.dstAddr': [ALLSPFRouters, 32]},
                            action_name='MyIngress.set_mgid',
                            action_params={'mgid': mgid})

        # controller is at port 1, so we can skip that port
        self.sw.addMulticastGroup(mgid=mgid, ports=range(2, 6))

    def handleHello(self, pkt):
        pkt.show2()

    def handleLSU(self, pkt):
        pkt.show2()

    def handlePkt(self, pkt):
        if PWOSPFHeader in pkt:
            # ignore my own packets
            if not (pkt['PWOSPFHeader'].routerID == self.db['routerID']):
                # check Area ID, needs to be the same
                if (pkt['PWOSPFHeader'].areaID == self.db['areaID']):
                    if (pkt['PWOSPFHeader'].Type == 1): # we got a hello
                        self.handleHello(pkt)
                    elif (pkt['PWOSPFHeader'].Type == 4): # we got a LSU
                        self.handleLSU(pkt)
                    else:
                        print 'Invalid type, dropperino'
        else:
            assert PWOSPFHeader in pkt, "Should only receive packets from switch with special header"

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        assert PWOSPFHeader in pkt, "Controller must send packets with special header"
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        Thread(target=self.runSniff).start()
        Thread(target=self.sendRegularlyHello).start()
        Thread(target=self.sendRegularlyLSU).start()

    def runSniff(self):
        sniff(iface=self.iface, prn=self.handlePkt, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(PWOSPFController, self).start(*args, **kwargs)
        time.sleep(self.start_wait)

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)

    def sendRegularlyHello(self):
        self.helloPacket()
        Timer(self.db['helloInt'], self.sendRegularlyHello).start()

    def sendRegularlyLSU(self):
        self.LSUPacket()
        Timer(self.db['lsuInt'], self.sendRegularlyLSU).start()
    

    def helloPacket(self):
        f = Ether(dst='ff:ff:ff:ff:ff:ff')/ CPUMetadata()/IP(src=self.chost.IP(), dst=ALLSPFRouters)

        g = f/PWOSPFHeader(routerID=self.db['routerID'], areaID=self.db['areaID'])

        h = g/PWOSPFHello(HelloInt=self.db['helloInt'])
        self.send(h)

    def LSUPacket(self):
        f = Ether(dst='ff:ff:ff:ff:ff:ff')/ CPUMetadata()/IP(src=self.chost.IP(), dst=ALLSPFRouters)

        g = f/PWOSPFHeader(routerID=self.db['routerID'], areaID=self.db['areaID'])

        h = g/PWOSPFLSU()
        self.send(h)

