#Camillo Malnati, 16.03.2019

from p4app import P4Mininet
from my_topo import TwoSwitchTopo
import sys
import time
from pwospf_controller import PWOSPFController


topo = TwoSwitchTopo()
net = P4Mininet(program='pwospf.p4', topo=topo)
net.start()

# Populate IPv4 forwarding table
def addForwardingRule(sw, host, port):
    sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.%d" % host, 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('h%d' % host).intfs[0].mac,
                                          'port': port})


s1, s2, h1, h2, c1, c2 = net.get('s1'), net.get('s2'), net.get('h1'), net.get('h2'), net.get('c1'), net.get('c2')

# Topology addresses and ports

#           .1      1 * - *  2                       2 * - * 1          .2
#            cpu------| s1|----------------------------| s2|--------cpu
#                     * - *                            * - *
#                       | 3                              | 3
#                       |                                |
#                       |                                |
#         10.10.10.3    | 3                            3 |  10.10.10.4
#                     * - *                            * - *
#                     | h1|                            | h2|
#                     * - *                            * - *      

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.3", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('h1').intfs[0].mac,
                                          'port': 3})

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.4", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('h2').intfs[0].mac,
                                          'port': 2})

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.1", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('c1').intfs[0].mac,
                                          'port': 1})


s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.3", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('h1').intfs[0].mac,
                                          'port': 2})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.4", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('h2').intfs[0].mac,
                                          'port': 3})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.2", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('c2').intfs[0].mac,
                                          'port': 1})


# this let the controller see each others, try to delete this at the end
s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.2", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('c2').intfs[0].mac,
                                          'port': 2})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.1", 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': net.get('c1').intfs[0].mac,
                                          'port': 2})

# Start the pwospf controller
controller1 = PWOSPFController(s1)
controller1.start()

controller2 = PWOSPFController(s2)
controller2.start()

# addForwardingRule(s1, 1, 1)
# addForwardingRule(s1, 3, 3)
# addForwardingRule(s1, 4, 2)

# addForwardingRule(s2, 3, 2)
# addForwardingRule(s2, 4, 3)
# addForwardingRule(s2, 2, 1)


# TODO send some update or hello packet 
loss = net.pingAll()
assert loss == 0


print("done")
