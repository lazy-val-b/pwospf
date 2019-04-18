from mininet.topo import Topo

class MyTopo( Topo ):

    def build( self, n, k ):
        switches = {}
        hosts = {}

        # Add hosts and switches dynamically
        for i in xrange(1, n+1):
            key = 's' + str(i)
            switches[key] = self.addSwitch(key)

        for i in xrange(1, n * k+1):
            key = 'h' + str(i)
            hosts[key] = self.addHost(key, ip = "10.0.0.%d" % i, mac = '00:00:00:00:00:%02x' % i)
            
        # Add links (hardcode for now, 3 links per switch)
        self.addLink(switches['s1'], switches['s2'], port1=0, port2=0)
        self.addLink(hosts['h1'], switches['s1'], port2=1)
        self.addLink(hosts['h2'], switches['s1'], port2=2)
        self.addLink(hosts['h3'], switches['s1'], port2=3)
        self.addLink(hosts['h4'], switches['s2'], port2=4)
        self.addLink(hosts['h5'], switches['s2'], port2=5)
        self.addLink(hosts['h6'], switches['s2'], port2=6)



topos = { 'mytopo': ( lambda: MyTopo() ) }