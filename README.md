# qb-port-sync
Automatically syncs the qBittorrent listening port with the VPN-assigned forwarded port from Gluetun (supports ProtonVPN and similar VPNs with port forwarding).  Designed for Docker setups where qBittorrent is routed through Gluetun (network_mode: service:gluetun) Ensures port-forwarded torrent traffic continues working even after VPN reconnections
