from threading import Thread, Event
from scapy.all import sendp
from scapy.all import Packet, Ether, IP, ARP
from async_sniff import sniff
from cpu_metadata import CPUMetadata
from pwospf_protocol import PWOSPF_HEADER, PWOSPF_HELLO, PWOSPF_LSU
import time

import pdb

OSPF_HELLO = 1
OSPF_LSU = 4
INFINITE = 1000


class PWOSPFController(Thread):
    def __init__(self, sw, rid, area_id, fr, network, start_wait=0.3):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.start_wait = start_wait  # time to wait for the controller to be listenning
        self.iface = sw.intfs[0].name  # is this interface 0 or 1?
        self.network = network
        self.routingTable = {sw.name: []}
        self.stop_event = Event()
        self.addForwardingRules(fr)
        self.initialise_routing_table()
        self.computeDijkstra(network)

    def initialise_routing_table(self):
        me = self.sw.name

        links = self.network.topo.links()
        nodes = self.network.topo.nodes()
        for node in nodes:
            self.routingTable[node] = {}

        # for the future

        # for node in nodes:
        #     for node2 in nodes:
        #         if node != node2:
        #             self.routingTable[node][node2] = INFINITE
        #         else:
        #             self.routingTable[node][node] = 0

        # for node in nodes:
        #     if (me, node) in links or (node, me) in links:
        #         self.routingTable[me][node] = 1

        for node in nodes:
            self.routingTable[node][node] = 0

        for link in links:
            self.routingTable[link[0]][link[1]] = 1
            self.routingTable[link[1]][link[0]] = 1

        print(self.routingTable)

    def computeDijkstra(self, network):

        me = self.sw.name
        links = self.network.topo.links()
        nodes = self.network.topo.nodes()
        unvisited = set()
        dist = {}
        prev = {}

        for node in nodes:
            unvisited.add(node)
            if (node, me) in links or (me, node) in links:
                dist[node] = 1
                prev[node] = me
            else:
                dist[node] = INFINITE
                prev[node] = None

        dist[me] = 0

        while len(unvisited) > 0:
            mininum = INFINITE
            checking = None
            for node in unvisited:
                if dist[node] <= mininum:
                    checking = node
                    mininum = dist[node]

            unvisited.remove(checking)
            # node[0] is the name
            # node[1] is the distance
            for node, distance in self.routingTable[checking].items():
                print(node, distance)
                if node in unvisited:
                    new_route = dist[checking] + distance
                    if new_route < dist[node]:
                        print("we in it:", node, new_route, dist[node])
                        dist[node] = new_route
                        prev[node] = checking

        print(dist)
        print(prev)

        # me = self.sw.name
        # links = network.topo.links()
        # nodes = network.topo.nodes()

        # distance_dic = {}
        # distance_dic[me] = 0
        # prev_hop = {}
        # for node in nodes:
        #     if (node, me) in links or (me, node) in links:
        #         distance_dic[node] = 1
        #         prev_hop[node] = me
        #     else:
        #         distance_dic[node] = INFINITE
        #         prev_hop[node] = None

        # checked_nodes = set()
        # checked_nodes.add(me)

        # while checked_nodes != set(nodes):
        #     min_distance_node = None
        #     for key in distance_dic:
        #         if key not in checked_nodes:
        #             # find the minimum one, how?
        #             if (
        #                 min_distance_node is None
        #                 or distance_dic[key] < distance_dic[min_distance_node]
        #             ):
        #                 min_distance_node = key
        #     checked_nodes.add(min_distance_node)
        #     for edge in links:
        #         if min_distance_node in edge:
        #             neighbour = edge[0] if edge[0] != min_distance_node else edge[1]
        #             if neighbour not in checked_nodes:
        #                 if (
        #                     distance_dic[neighbour] + 1
        #                     < distance_dic[min_distance_node]
        #                 ):
        #                     distance_dic[min_distance_node] = distance_dic[
        #                         neighbour + 1
        #                     ]
        #                     prev_hop[min_distance_node] = neighbour

        # print(distance_dic)
        # print(prev_hop)
        # return prev_hop

    def addForwardingRules(self, fr):
        for entry in fr:
            self.sw.insertTableEntry(
                table_name="MyIngress.ipv4_lpm",
                match_fields={"hdr.ipv4.dstAddr": entry[0]},
                action_name="MyIngress.ipv4_forward",
                action_params={"dstAddr": entry[1], "port": entry[2]},
            )

    def handlePWOSPFHello(self, pkt):
        # pkt.show2()
        # self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)  # why send?

    def handlePWOSPFLSU(self, pkt):
        # self.addMacAddr(pkt[ARP].hwsrc, pkt[CPUMetadata].srcPort)
        self.send(pkt)

    def handlePkt(self, pkt):
        # pkt.show2()
        assert (
            CPUMetadata in pkt
        ), "Should only receive packets from switch with special header"

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

        hello = (
            Ether()
            / CPUMetadata()
            / IP(dst="10.0.0.2")
            / PWOSPF_HEADER()
            / PWOSPF_HELLO()
        )
        # self.send(hello)
        # hello.show2()

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)
