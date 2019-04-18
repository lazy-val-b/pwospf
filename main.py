from p4app import P4Mininet
from mininet.topo import Topo
from myTopo import MyTopo

N = 2 # Number of switches
K = 3 # Number of hosts per switch
mgid = 10 # Multicast ID

topo = MyTopo(N, K)
net = P4Mininet(program='PWOSPF.p4', topo=topo)
net.start()

s1, s2 = net.get('s1'), net.get('s2')
h1, h2, h3, h4, h5, h6 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4'), net.get('h5'), net.get('h6')

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

for i in range(1, K +1):
    h = net.get('h%d' % i)
    h.cmd('arp -s 10.0.0.255 ff:ff:ff:ff:ff:ff')

    s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.%d" % i, 32]},
                        action_name='MyIngress.set_egr',
                        action_params={'port': i})
    s1.insertTableEntry(table_name='MyEgress.send_frame',
                        match_fields={'standard_metadata.egress_port': i},
                        action_name='MyEgress.rewrite_dst',
                        action_params={'mac': '00:00:00:00:00:%02x' % i,
                                        'ip': '10.0.0.%d' % i})

s1.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                    match_fields={'hdr.ipv4.dstAddr': ["10.0.0.255", 32]},
                    action_name='MyIngress.set_mgid',
                    action_params={'mgid': mgid})
s1.insertTableEntry(table_name='MyIngress.switch_forward',
                    match_fields={'hdr.ipv4.dstAddr': ["10.0.0.4", 32]},
                    action_name='MyIngress.forward_to_switch',
                    action_params={'port': 0})

s1.addMulticastGroup(mgid=mgid, ports=range(1, K+1))

for i in range((N-1)* K + 1, N * K + 1):
    h = net.get('h%d' % i)
    h.cmd('arp -s 10.0.0.255 ff:ff:ff:ff:ff:ff')

    s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                        match_fields={'hdr.ipv4.dstAddr': ["10.0.0.%d" % i, 32]},
                        action_name='MyIngress.set_egr',
                        action_params={'port': i})
    s2.insertTableEntry(table_name='MyEgress.send_frame',
                        match_fields={'standard_metadata.egress_port': i},
                        action_name='MyEgress.rewrite_dst',
                        action_params={'mac': '00:00:00:00:00:%02x' % i,
                                        'ip': '10.0.0.%d' % i})

s2.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                    match_fields={'hdr.ipv4.dstAddr': ["10.0.0.255", 32]},
                    action_name='MyIngress.set_mgid',
                    action_params={'mgid': mgid})
s2.insertTableEntry(table_name='MyIngress.switch_forward',
                    match_fields={'hdr.ipv4.dstAddr': ["10.0.0.1", 32]},
                    action_name='MyIngress.forward_to_switch',
                    action_params={'port': 0})



s2.addMulticastGroup(mgid=mgid, ports=range(K + 1, N * K))
loss = net.pingAll()
assert loss == 0

# Should receive a pong from h2 and h3 (i.e. a duplicate pong).
out = net.get('h1').cmd('ping -c2 10.0.0.255')
print(out)
assert 'from 10.0.0.3' in out
assert 'from 10.0.0.2' in out

# # Update group. Should only receive a pong from h2.
s1.updateMulticastGroup(mgid=mgid, ports=[2])
out = net.get('h1').cmd('ping -c2 10.0.0.255')
assert 'from 10.0.0.2' in out
assert 'from 10.0.0.3' not in out

# # Delete group. Packets should not be forwarded.
s1.deleteMulticastGroup(mgid=mgid, ports=[])
out = net.get('h1').cmd('ping -W1 -c2 10.0.0.255')
assert '0 received, 100% packet loss' in out
