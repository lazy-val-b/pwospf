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

# # Start a controller for each switch
cpu1 = PWOSPFController(s1, c1, 5, 0xffffff00, 17, net)
cpu1.start()

# cpu2 = PWOSPFController(s2, c2, 5, 0xffffff00, 17, net)
# cpu2.start()

# print net.pingAll()