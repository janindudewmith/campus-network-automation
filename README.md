# Campus Network Automation and Design

**Course:** EE8203 Design and Management of Data Networks  
**Department:** Electrical and Information Engineering, Faculty of Engineering, University of Ruhuna  
**Authors:** Dewmith M.K.J. (EG/2021/4474) | Sewinda L.L.D. (EG/2021/4807)

---

## 📖 Table of Contents
1. [Executive Summary](#executive-summary)
2. [Network Design & Architecture](#network-design--architecture)
3. [VLAN & IP Addressing Plan](#vlan--ip-addressing-plan)
4. [Access Control Policy (ACLs)](#access-control-policy-acls)
5. [Network Automation](#network-automation)
6. [Monitoring System (Zabbix)](#monitoring-system-zabbix)
7. [Challenges & Troubleshooting](#challenges--troubleshooting)

---

## Executive Summary
This project demonstrates the end-to-end design, implementation, automation, and monitoring of a campus data network interconnecting four departments: DEIE, DCEE, DMME, and DIS. Built entirely in GNS3 using Cisco IOSv and IOSvL2 images, the network adheres to a three-layer hierarchical model. 

Key features include OSPF dynamic routing, strict ACL-based security filtering at the department gateways, Python/Netmiko automation for L3 routing, Ansible orchestration for L2 switching, and active SNMPv2c monitoring via Zabbix 6.0 LTS.

---

## Network Design & Architecture

The campus network is structured around a resilient, scalable three-layer hierarchical model:

* **Edge/Core Layer:** `R-EDGE` terminates the WAN link (NAT/PAT) and isolates the internal routing domain. `R-CORE` and `SW-CORE` (a Layer-3 switch) form the high-speed routed backbone.
* **Distribution Layer:** `SW-D-DEIE`, `SW-D-DCEE`, and `SW-D-DMME` act as per-department gateways. **Design Choice:** Gateways were deliberately placed at the distribution layer rather than the core to enforce departmental security policies at the very first Layer-3 hop, dropping forbidden traffic before it consumes backbone bandwidth.
* **Access Layer:** Pure Layer-2 access switches (`SW-A-DEIE`, `SW-A-DCEE`, `SW-A-DMME`, `SW-A-DIS`) provide end-host connectivity, optimizing port cost and scalability.

### Logical Implementation (Packet Tracer)
![Logical Topology](Diagrams/Figures/Topology_Packet_Tracer_V_2_Corrected.png)

### Physical Implementation (GNS3)
![GNS3 Topology](Diagrams/Figures/gns3.png)

---

## VLAN & IP Addressing Plan

The IP scheme is segmented by purpose: User/Server VLANs (`10.10.x.0/24`), Management Subnets (`10.99.x.0/24`), and Infrastructure/Routing (`10.255.x.x`).

### VLAN Allocation
| VLAN | Name | Purpose | Subnet | Gateway (SVI) |
|---|---|---|---|---|
| **10** | VLAN-DEIE | DEIE workstations | 10.10.10.0/24 | 10.10.10.1 (SW-D-DEIE) |
| **20** | VLAN-DCEE | DCEE administration | 10.10.20.0/24 | 10.10.20.1 (SW-D-DCEE) |
| **30** | VLAN-DMME | DMME workshop lab | 10.10.30.0/24 | 10.10.30.1 (SW-D-DMME) |
| **40** | VLAN-DIS | DIS server farm | 10.10.40.0/24 | 10.10.40.1 (SW-CORE) |
| **99** | VLAN-MGMT | Out-of-band management | *Per Dept.* | *See table below* |
| **100**| NATIVE-VLAN | Untagged trunk traffic | N/A | N/A |

### Management Addressing & Routing (OSPF Area 0)
Due to L3 point-to-point links separating distribution switches from the core, VLAN 99 operates as distinct broadcast domains to prevent OSPF route poisoning.
* **Core/DIS/VMs:** `10.99.99.0/24` (Gateway: `SW-CORE`)
* **DEIE:** `10.99.100.0/24` (Gateway: `SW-D-DEIE`)
* **DCEE:** `10.99.101.0/24` (Gateway: `SW-D-DCEE`)
* **DMME:** `10.99.102.0/24` (Gateway: `SW-D-DMME`)

---

## Access Control Policy (ACLs)

Security is strictly enforced via stateless Extended ACLs bound inbound to each department's SVI, preventing lateral movement and securing the server farm.

| Source | Destination | Policy / Justification | Enforced By |
|---|---|---|---|
| **DEIE** | Any | Permit all (Engineering staff need full server access) | `ACL_DEIE_IN` |
| **DCEE** | DIS | Permit HTTP/HTTPS & DNS only (Admin web access) | `ACL_DCEE_IN` |
| **DMME** | DIS | Deny all (Workshop requires no server access) | `ACL_DMME_IN` |
| **DCEE/DMME** | Cross-Dept | Deny all (Strict inter-department isolation) | `ACL_DCEE_IN` / `ACL_DMME_IN` |
| **Monitoring** | All Devices | Permit UDP 161 (SNMP polling) | `ACL_DIS_IN` |
| **Management** | All VTY lines | Permit TCP 22 (SSH) from `10.99.x.x` only | `ACL_MGMT_SSH` |

---

## Network Automation

Infrastructure as Code (IaC) principles were applied using two distinct automation tools, selected based on configuration requirements.

### 1. Python / Netmiko (L3 Routers & SNMP)
Used for sequential tasks where execution order is critical (e.g., assigning IPs before declaring OSPF networks). Python scripts parse a YAML inventory and push configurations to `R-CORE` and `R-EDGE`, while distributing SNMP community strings network-wide.
![Netmiko Output](Diagrams/Figures/netmiko.png)

### 2. Ansible (L2 Switching)
Used to orchestrate scalable, repeatable switch configurations. Four modular roles (`vlans`, `trunking`, `access_ports`, `stp`) are executed via `site.yml`. 
* **Idempotency:** Uses Cisco IOS resource modules (e.g., `ios_l2_interfaces`) to verify state before pushing changes, ensuring zero configuration drift during repeated runs.
* **Rollback:** `rollback.yml` restores default interface states while preserving the VLAN 99 SVI, preventing accidental management lockouts.

![Ansible Idempotency Check](Diagrams/Figures/ans_site_yaml_running_02_check.png)

---

## Monitoring System (Zabbix)

Zabbix 6.0 LTS actively monitors the network from `VM-ZABBIX` on the management plane (`10.99.99.60`). 

* **Polling:** Devices are polled via SNMPv2c. Routers are polled at their stable Loopback IPs, while switches are polled at their management SVIs.
* **Triggers:**
  * Host Unreachable (3 consecutive ICMP failures)
  * Interface Down / Operational State Change
  * High CPU Load (>80% for 60s)
  * Guarded Port Violations (Alerts when an edge port with BPDU Guard drops, indicating unauthorized switch connections).

### Device Availability Map
![Zabbix Host List](Diagrams/Figures/zabbix_devices_map.png)

### Active Alerts & Triggers
![Zabbix Alerts](Diagrams/Figures/zabbix_alert.png)

### Global Campus Dashboard
![Zabbix Dashboard](Diagrams/Figures/zabbix_dash.png)

---

## Challenges & Troubleshooting

### 1. Discontinuous Management Subnet & OSPF Routing Loops
Initially, all management interfaces were assigned to a single flat `10.99.99.0/24` subnet. Because the core-to-distribution uplinks are routed L3 links, this fragmented VLAN 99 into isolated islands. Multiple switches advertised the exact same `/24` subnet into OSPF, causing severe routing loops, asymmetric paths, and SSH timeouts during Ansible runs.
* **Resolution:** Re-architected the management plane by allocating unique `/24` blocks to each department (`10.99.100.0/24`, `10.99.101.0/24`, etc.) and updating the VTY Access-Class lists, instantly restoring reliable automation transport.

### 2. Native VLAN Disagreements
Configuring 802.1Q trunks triggered spanning-tree `PVID_LOCAL` blocking errors when one side was moved to Native VLAN 100 before the other.
* **Resolution:** Validated that Native VLAN changes must be treated as atomic, synchronous operations across both ends of a link.

### 3. BPDU Guard & Virtualization Bridging
Applying `spanning-tree portfast` and `bpduguard enable` to the DIS server farm access ports instantly put them in `err-disable` state.
* **Resolution:** Identified that virtual machines (like the Ubuntu DHCP/Ansible hosts) bridging traffic internally generate BPDUs that mimic switch behavior. BPDU Guard was stripped from VM-facing ports to restore connectivity.
