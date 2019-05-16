from mininet.topo import Topo

class MyTopo( Topo ):

    def build( self, n, k ):
        switches = {}
        hosts = {}

        # Add hosts and switches dynamically
        for i in xrange(1, n+1):
            key = 's' + str(i)
            switches[key] = self.addSwitch(key)

        hosts['h1'] = self.addHost('h1', ip = "192.168.0.1", mac = '00:00:00:00:00:01')
        hosts['h2'] = self.addHost('h2', ip = "192.168.0.2", mac = '00:00:00:00:00:02')
        hosts['h3'] = self.addHost('h3', ip = "192.168.0.3", mac = '00:00:00:00:00:03')
        hosts['h4'] = self.addHost('h4', ip = "192.168.0.4", mac = '00:00:00:00:00:04')
        hosts['h5'] = self.addHost('h5', ip = "192.168.0.5", mac = '00:00:00:00:00:05')
        hosts['h6'] = self.addHost('h6', ip = "192.168.0.6", mac = '00:00:00:00:00:06')
        hosts['c1'] = self.addHost('c1', ip = "192.168.0.7", mac = '00:00:00:00:00:07')
        hosts['c2'] = self.addHost('c2', ip = "192.168.0.8", mac = '00:00:00:00:00:08')
        hosts['c3'] = self.addHost('c3', ip = "192.168.0.9", mac = '00:00:00:00:00:09')




            
        # Add links (hardcode for now, 3 links per switch)
        self.addLink(switches['s1'], switches['s2'], port1=4, port2=4)
        self.addLink(switches['s2'], switches['s3'], port1=5, port2=5)

        self.addLink(hosts['c1'], switches['s1'], port2=1)
        self.addLink(hosts['c2'], switches['s2'], port2=1)
        self.addLink(hosts['c3'], switches['s3'], port2=1)

        self.addLink(hosts['h1'], switches['s1'], port2=2)
        self.addLink(hosts['h2'], switches['s1'], port2=3)
        self.addLink(hosts['h3'], switches['s2'], port2=2)
        self.addLink(hosts['h4'], switches['s2'], port2=3)
        self.addLink(hosts['h5'], switches['s3'], port2=2)
        self.addLink(hosts['h6'], switches['s3'], port2=3)



topos = { 'mytopo': ( lambda: MyTopo() ) }