from p4app import P4Mininet
from mininet.topo import Topo
from myTopo import MyTopo
from controller import PWOSPFController
from pwospf_protocoll import ALLSPFRouters


N = 2 # Number of switches
K = 3 # Number of hosts per switch
mgid = 10 # Multicast ID

topo = MyTopo(N, K)
net = P4Mininet(program='PWOSPF.p4', topo=topo)
net.start()

s1, s2 = net.get('s1'), net.get('s2')
h1, h2, h3, h4, c1, c2 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4'), net.get('c1'), net.get('c2')
# s1.setIP(ALLSPFRouters)
# s1.intfs[0].setIP("172.17.0.5", 32)
# s2.setIP(ALLSPFRouters)
# s2.intfs[0].setIP("172.17.0.6", 32)


def printLinkInfos():
        for link in topo.links():
                print('###############')
                print('LINK')
                print(link)
                print(link[0] + '<---->' + link[1])
                print(topo.linkInfo(link[0], link[1]))
                print(link[0])
                print(topo.nodeInfo(link[0]))
                print(link[1])
                print(topo.nodeInfo(link[1]))

# S1 TABLE ENTRIES
s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [c1.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': c1.MAC(),
                                        'port': topo.linkInfo('c1', 's1')['port2']})
s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h1.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': h1.MAC(),
                                        'port': topo.linkInfo('h1', 's1')['port2']})
s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h2.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': h2.MAC(),
                                        'port': topo.linkInfo('h2', 's1')['port2']})

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h3.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': h3.MAC(),
                                        'port': topo.linkInfo('s1', 's2')['port2'] })

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [c2.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': c2.MAC(),
                                        'port': topo.linkInfo('s1', 's2')['port2'] })

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h4.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': h4.MAC(),
                                        'port': topo.linkInfo('s1', 's2')['port2'] })

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [ALLSPFRouters, 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': c1.MAC(),
                                        'port': topo.linkInfo('c1', 's1')['port2']})


# S2 TABLE ENTRIES
s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [c2.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': c2.MAC(),
                                        'port': topo.linkInfo('c2', 's2')['port2']})
s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h3.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': h3.MAC(),
                                        'port': topo.linkInfo('h3', 's2')['port2']})
s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h4.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'dstAddr': h4.MAC(),
                                        'port': topo.linkInfo('h4', 's2')['port2']})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [ALLSPFRouters, 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={'port': topo.linkInfo('c2', 's2')['port2']})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h1.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': h1.MAC(),
                                        'port': topo.linkInfo('s2', 's1')['port2']})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [c1.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': c1.MAC(),
                                        'port': topo.linkInfo('s2', 's1')['port2']})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': [h2.IP(), 32]},
                        action_name='MyIngress.ipv4_forward',
                        action_params={ 'dstAddr': h2.MAC(),
                                        'port': topo.linkInfo('s2', 's1')['port2']})

# Start a controller for each switch
# cpu1 = PWOSPFController(s1, c1, 5, 0xffffff00, 17, 0.5)
# cpu1.start()

# cpu2 = PWOSPFController(s2, c2, 5, 0xffffff00, 17, 0.5)
# cpu2.start()

print net.pingAll()