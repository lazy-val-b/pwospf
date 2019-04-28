from scapy.fields import BitField, ByteField, ShortField, IntField, ByteEnumField, LongField
from scapy.packet import Packet, bind_layers
from scapy.layers.inet import IP
from scapy.layers.l2 import Ether

TYPE_PWOSPF_METADATA = 89

# Add PWSOPF layer
class PWOSPFMetadata(Packet):
    name = "PWOSPFMetadata"
    fields_desc = [ ByteField("Version", 2),
                    ByteEnumField("Type", 1, {1:"Hello", 4:"Link State Update"}),
                    ShortField("Packet length", None),
                    IntField("Router ID", 0),
                    IntField("Area ID", 0),
                    ShortField("Checksum", 0),
                    ShortField("Autype", 0),
                    LongField("Authentication", 0),
                ]

bind_layers(Ether, PWOSPFMetadata, type=TYPE_PWOSPF_METADATA)
bind_layers(IP, PWOSPFMetadata, proto=TYPE_PWOSPF_METADATA)