from p4app import P4Mininet
from mininet.topo import Topo
from myTopo import MyTopo
from controller import PWOSPFController
import time


N = 3 # Number of switches
K = 3 # Number of hosts per switch
mgid = 10 # Multicast ID

topo = MyTopo(N, K)
net = P4Mininet(program='PWOSPF.p4', topo=topo)
net.start()

s1, s2, s3 = net.get('s1'), net.get('s2'), net.get('s3')
h1, h2, h3, h4, c1, c2, c3 = net.get('h1'), net.get('h2'), net.get('h3'), net.get('h4'), net.get('c1'), net.get('c2'), net.get('c3')

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
# Since the IP of the 0th interface is always the same, I set the router ID here myself.
cpu1 = PWOSPFController(s1, c1, 5, 0xffffffff, 17, net, [("192.168.0.1", 2), ("192.168.0.2", 3) ], rid=1 ).start()

cpu2 = PWOSPFController(s2, c2, 5, 0xffffffff, 17, net, [("192.168.0.3", 2), ("192.168.0.4", 3) ], rid=2).start()

cpu3 = PWOSPFController(s3, c3, 5, 0xffffffff, 17, net, [("192.168.0.5", 2), ("192.168.0.6", 3) ], rid=3).start()


while True:
        time.sleep(3)
# print net.pingAll()