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

# Start a controller for each switch
cpu1 = PWOSPFController(s1, c1, 5, 0xffffff00, 17, [
    { "mac": '00:00:00:00:00:01', "ip": '10.0.0.1', "port": 2}, # GO TO H1
    { "mac": '00:00:00:00:00:02', "ip": '10.0.0.2', "port": 3}, # GO TO H2
    { "mac": '00:00:00:00:00:03', "ip": '10.0.0.3', "port": 4}, # GO TO H3
    { "mac": '00:00:00:00:00:04', "ip": '10.0.0.4', "port": 4}, # GO TO H4
    { "mac": '00:00:00:00:00:05', "ip": '10.0.0.5', "port": 1}, # GO TO C1
    { "mac": '00:00:00:00:00:06', "ip": '10.0.0.6', "port": 4}, # GO TO C2
    { "mac": '00:00:00:00:00:05', "ip": ALLSPFRouters, "port": 1}, # ALLSPFROUTERS
])
cpu1.start()

cpu2 = PWOSPFController(s2, c2, 5, 0xffffff00, 17, [
    { "mac": '00:00:00:00:00:01', "ip": '10.0.0.1', "port": 4}, # GO TO H1
    { "mac": '00:00:00:00:00:02', "ip": '10.0.0.2', "port": 4}, # GO TO H2
    { "mac": '00:00:00:00:00:03', "ip": '10.0.0.3', "port": 2}, # GO TO H3
    { "mac": '00:00:00:00:00:04', "ip": '10.0.0.4', "port": 3}, # GO TO H4
    { "mac": '00:00:00:00:00:05', "ip": '10.0.0.5', "port": 4}, # GO TO C1
    { "mac": '00:00:00:00:00:06', "ip": '10.0.0.6', "port": 1}, # GO TO C2
    { "mac": '00:00:00:00:00:05', "ip": ALLSPFRouters, "port": 1}, # ALLSPFROUTERS
])
cpu2.start()

print net.pingAll()