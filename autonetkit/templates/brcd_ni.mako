! BROCADE MLX Config generated on ${date}
! by ${version_banner}
!

hostname ${node}
!
% if node.global_custom_config:
!
${node.global_custom_config}
% endif
no password strength-check
!
% if node.telnet:
telnet server
% endif
% if node.use_fdp:
!
fdp run
% endif
% if node.mgmt:
!
interface mgmt0
 vrf member management
 ip address ${node.mgmt.ip}  ${node.mgmt.mask}
% endif
!
!
% if node.ospf:
router ospf
% endif
% if node.bgp:
router bgp
% endif
% if node.pim:
router pim
% endif
##SNMP
% if node.snmp:
!
    % if node.snmp.enabled == True:
snmp-server
        % for community in node.snmp.communities:
snmp-server community ${community.name} ${community.permission}
        % endfor
        % for user in node.snmp.users:
snmp-server user ${user.user} ${user.grp} v3
        % endfor
        % for server in node.snmp.servers:
snmp-server host ${server.ip} version ${server.version} ${server.community} port ${server.udp_port}
        % endfor
!
        % for trap in node.snmp.traps:
            % if trap.enabled == True:
                % if trap.id == 'bgp':
router bgp
                % endif
snmp-server enable traps ${trap.id}
            % endif
        % endfor
    % endif
% endif
% if node.ntp:
!
ntp
    % for server in node.ntp.servers:
server ${server.ip} key ${server.key}
    % endfor
% endif
% if node.radius:
!
    % for server in node.radius.servers:
radius-server host ${server.ip} auth-port ${server.auth_port} acct-port ${server.acct_port} authentication-only key ${server.key}
    % endfor
% endif
% if node.lag:
!
!
    % for lag in node.lag:
!
lag ${lag.name} ${lag.type} id ${lag.id}
ports ${lag.ports}
primary port ${lag.primary_port}
deploy
!
    % endfor
% endif
!
!
!
## Physical Interfaces
% for interface in node.interfaces:
!
interface ${interface.id}
    % if interface.comment:
  ! ${interface.comment}
    % endif
    % if interface.is_member_lag:
        % if interface.is_primary_port != True:
no shutdown
<% continue %>:
        % endif
    % endif
    % if interface.category == 'loopback':
        % if node.ospf:
  ip ospf ${node.ospf.process_id} area 0.0.0.0
  ip ospf passive
        % endif
    % endif
    % if interface.pim:
  ip pim sparse mode
    % endif
    % if interface.mtu:
  mtu ${interface.mtu}
    % endif
    % if interface.custom_config:
  ${interface.custom_config}
    % endif
    % if interface.vrf:
  vrf forwarding ${interface.vrf}
    % endif
    % if interface.use_ipv4:
        % if interface.use_dhcp:
  ip address dhcp
        % else:
  ip address ${interface.ipv4_address} ${interface.ipv4_subnet.netmask}
        % endif
    % else:
    !
  ##no ip address
    % endif
    % if interface.use_ipv6:
  ipv6 address ${interface.ipv6_address}
    % endif
    % if interface.rip:
        % if interface.rip.use_ipv6:
  ipv6 rip {node.rip.process_id} enable
        % endif
    % endif
    % if interface.category != "loopback":
        % if interface.ospf:
            % if interface.ospf.priority:
  ip ospf priority ${interface.ospf.priority}
            % endif
            % if interface.ospf.use_ipv4:
                % if not interface.ospf.multipoint:
  ip ospf network point-to-point
                % endif
  ip ospf cost ${interface.ospf.cost}
  ip ospf area ${interface.ospf.area}
            % endif
            % if interface.ospf.use_ipv6:
                % if not interface.ospf.multipoint:
  ipv6 ospfv3 network point-to-point
                % endif
  ipv6 ospfv3 cost ${interface.ospf.cost}
  ipv6 ospfv3 area ${interface.ospf.area}
            % endif
        % endif
    % endif
    % if interface.isis:
        % if interface.isis.use_ipv4:
  ip router isis ${node.isis.process_id}
            % if interface.physical:
  isis circuit-type level-2-only
                % if not interface.isis.multipoint:
  isis network point-to-point
                % endif
  isis metric ${interface.isis.metric}
            % endif
        % endif
        % if interface.isis.use_ipv6:
  ipv6 router isis ${node.isis.process_id}
            % if interface.physical:
  isis ipv6 metric ${interface.isis.metric}
            % endif
        % endif
        % if interface.isis.mtu:
  clns mtu ${interface.isis.mtu}
        % endif
    % endif
    % if interface.physical:
        % if not node.exclude_phy_int_auto_speed_duplex:
  ## don't include auto duplex and speed on platforms eg CSR1000v
  ## include by default
  ##duplex auto
  ##speed auto
        % endif
  no shutdown
    % endif
    % if interface.use_mpls:
  mpls ip
    % endif
    % if interface.te_tunnels:
  mpls traffic-eng tunnels
    % endif
!
% endfor
!
!
% if node.mct:
    % for cluster in node.mct:
!
cluster ${cluster.name} ${cluster.id}
rbridge ${cluster.rbridge_id}
session-vlan ${cluster.session_vlan}
member-vlan ${cluster.member_vlan}
icl ${cluster.name} ${cluster.icl}
        % for peer in node.mct_peer:
peer ${peer.ip} rbridge-id ${peer.rbridge_id_peer} icl ${cluster.name}
deploy
        % endfor
    % endfor
% endif
## OSPF
% if node.ospf:
!
    % if node.ospf.use_ipv4:
router ospf
router-id ${node.loopback}
        % if node.ospf.custom_config:
  ${node.ospf.custom_config}
        % endif
        % if node.ospf.ipv4_mpls_te:
  mpls traffic-eng router-id ${node.ospf.mpls_te_router_id}
  mpls traffic-eng area ${node.ospf.loopback_area}
        % endif
## Loopback
  log-adjacency-changes
    % endif
    % if node.ospf.use_ipv6:
router ospfv3
  router-id ${node.loopback}
  !
  address-family ipv6 unicast
  exit
    % endif
% endif
## ISIS
% if node.isis:
router isis ${node.isis.process_id}
    % if node.isis.custom_config:
  ${node.isis.custom_config}
    % endif
    % if node.isis.ipv4_mpls_te:
  mpls traffic-eng router-id ${node.isis.mpls_te_router_id}
  mpls traffic-eng level-2
    % endif
  net ${node.isis.net}
  metric-style wide
    % if node.isis.use_ipv6:
  !
  address-family ipv6
    multi-topology
  exit
    % endif
% endif
####
!
## BGP
% if node.bgp:
!
router bgp
local-as ${node.asn}
  router-id ${node.router_id}
  % if node.bgp.custom_config:
  ${node.bgp.custom_config}
  % endif
! ibgp
## iBGP Route Reflector Clients
## iBGP Route Reflectors (Parents)
## iBGP peers
  % for neigh in node.bgp.ibgp_neighbors:
    % if loop.first:
  ! ibgp peers
    % endif
  !
  neighbor ${neigh.loopback} remote-as ${neigh.asn}
  description iBGP peer ${neigh.neighbor}
  neighbor ${neigh.loopback} update-source loopback ${node.bgp.lo_interface}
  address-family ipv4 unicast
    send-community both
    % if node.bgp.route_reflector == True:
  route-reflector-client
    % endif
    % if node.vxlan:
  address-family l2vpn evpn
  send-community both
    % endif
  % endfor
!
## eBGP peers
  % for neigh in node.bgp.ebgp_neighbors:
    % if loop.first:
! ebgp
    % endif
  !
  neighbor ${neigh.dst_int_ip} remote-as ${neigh.asn}
  description eBGP to ${neigh.neighbor}
  address-family ipv4 unicast
    % if neigh.multihop:
  neighbor ${neigh.dst_int_ip} ebgp-multihop ${neigh.multihop}
    % endif
    % if loop.last:
!
    % endif
  % endfor
!
## ********
  % if node.bgp.use_ipv4:
 !
    % for peer in node.bgp.ipv4_peers:
      % if peer.is_ebgp:
      % endif
      % if peer.next_hop_self:
      % endif
      % if peer.rr_client:
      % endif
    % endfor
 exit
  % endif
  % if node.bgp.use_ipv6:
 !
 #address-family ipv6 unicast
    % for subnet in node.bgp.ipv6_advertise_subnets:
  #network ${subnet}
    % endfor
    % for peer in node.bgp.ipv6_peers:
  #neighbor ${peer.remote_ip} activate
      % if peer.is_ebgp:
  #send-community
      % endif
      % if peer.next_hop_self:
  ## iBGP on an eBGP-speaker
  #next-hop-self
      % endif
    % endfor
 exit
  % endif
!
!
##end
% endif
