/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

/* Type definitions */
typedef bit<9>  port_t;
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<16> mcastGrp_t;

/* Easier to use IPv4 and PWOSPF constants */
const bit<16> TYPE_IPV4 = 0x800;
const bit<8>  TYPE_PWOSPF  = 0x59; // 89
const port_t CPU_PORT           = 0x1; // 1


// SZ: 8bits = 1
#define ETH_SZ 14
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

#define IPV4_SZ 20
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

/* PWOSPF Packet */
#define PWOSPF_SZ 24
header pwospf_t {
    bit<8>    version;
    bit<8>    type;
    bit<16>   totalLen;
    bit<32>   routerID;
    bit<32>   areaID;
    bit<16>   hdrChecksum;
    bit<16>   autype;
    bit<64>   authentication;
}

struct metadata {
    /* empty */
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    pwospf_t pwospf;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_PWOSPF: parse_pwospf;
            default: accept;
        }
    }
    
    state parse_pwospf {
        packet.extract(hdr.pwospf);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop();
    }
    action decr_ttl() {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.dstAddr  = dstAddr;
        decr_ttl();
    }

    action set_mgid(mcastGrp_t mgid) {
        standard_metadata.mcast_grp = mgid;
        decr_ttl();
    }

    action send_to_CPU() {
        standard_metadata.egress_spec = CPU_PORT;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            drop;
            ipv4_forward;
            set_mgid;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
        if (hdr.pwospf.isValid() && standard_metadata.ingress_port != CPU_PORT) {
            send_to_CPU();
        }
        else if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0) {
            ipv4_lpm.apply();
        }
        else {
            drop();
        }

    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply { }
}
// control MyEgress(inout headers hdr,
//                  inout metadata meta,
//                  inout standard_metadata_t standard_metadata) {
//     action rewrite_dst(macAddr_t mac, ip4Addr_t ip) {
//         hdr.ethernet.dstAddr = mac;
//         hdr.ipv4.dstAddr = ip;
//     }
//     action drop() {
//         mark_to_drop();
//     }
//     table send_frame {
//         key = {
//             standard_metadata.egress_port: exact;
//         }
//         actions = {
//             rewrite_dst;
//             drop;
//             NoAction;
//         }
//         size = 256;
//         default_action = NoAction();
//     }
//     apply {
//         if (hdr.ipv4.isValid()) {
//           send_frame.apply();
//         }
//     }
// }

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.pwospf);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;