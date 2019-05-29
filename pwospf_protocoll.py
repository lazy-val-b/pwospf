from scapy.fields import BitField, ByteField, ShortField, PacketListField, IntField, ByteEnumField, LongField, FieldLenField, PadField, ConditionalField
from scapy.packet import Packet, bind_layers
from scapy.layers.inet import IP
from scapy.layers.l2 import Ether

TYPE_PWOSPF_TYPE = 89
ALLSPFRouters = "224.0.0.5" # 0xe0000005

# Add PWSOPF layer
class PWOSPFHeader(Packet):
    name = "PWOSPFHeader"
    fields_desc = [ 
                    ByteField("Version", 2),
                    ByteEnumField("Type", 1, {1:"Hello", 4:"Link State Update"}),
                    ShortField("PacketLength", None),
                    IntField("routerID", 0),
                    IntField("areaID", 0),
                    ShortField("Checksum", 0),
                    ShortField("Autype", 0),
                    LongField("Authentication", 0),
                ]

class PWOSPFHello(Packet):
    name = "PWOSPFHello"
    fields_desc = [ 
                    IntField("NetworkMask", 0xffffff00),
                    ShortField("HelloInt", 5),
                    ShortField("Padding", 0)
                ]

class PWOSPFLSA(Packet):
    name = "PWOSPFLSA"
    field_desc = [
                    IntField("subnet", 0),
                    IntField("mask", 0),
                    IntField("routerID", 0),
    ]
    # def extract_padding(self, s):
    #     return '', s

class PWOSPFLSU(Packet):
    name = "PWOSPFLSU"
    fields_desc = [ 
                    ShortField("Sequence", 0),
                    ShortField("TTL", 1),
                    PacketListField("Advertisements", None, PWOSPFLSA, count_from = None),
                    FieldLenField("NumAdvertisements",None,count_of="Advertisements", fmt="B"),
                ]

bind_layers(Ether, PWOSPFHeader, type=TYPE_PWOSPF_TYPE)
bind_layers(IP, PWOSPFHeader, proto=TYPE_PWOSPF_TYPE)
bind_layers(PWOSPFHeader, PWOSPFHello, Type=1)
bind_layers(PWOSPFHeader, PWOSPFLSU, Type=4)
bind_layers(PWOSPFLSU, PWOSPFLSA, subnet=2)