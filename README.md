# 🌀 qb-port-sync  
### Automatically sync qBittorrent’s listening port with Gluetun’s VPN-forwarded port

![Docker Image Version](https://img.shields.io/docker/v/adxglock/qb-port-sync?sort=semver&style=for-the-badge)
![Docker Pulls](https://img.shields.io/docker/pulls/adxglock/qb-port-sync?style=for-the-badge)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ADXGlock/qb-port-sync/docker-publish.yml?branch=main&style=for-the-badge)
![License](https://img.shields.io/github/license/ADXGlock/qb-port-sync?style=for-the-badge)

---

## 🧭 Overview

`qb-port-sync` is a lightweight Python-based sidecar container that automatically updates your **qBittorrent** listening port to match the **VPN-assigned forwarded port** from [Gluetun](https://github.com/qdm12/gluetun).  

Perfect for setups where **qBittorrent runs through Gluetun** (`network_mode: service:gluetun`) with VPN providers that support port forwarding such as **ProtonVPN**, **Mullvad**, and others.

---

## 🚀 Features

✅ Syncs qBittorrent’s listening port with the latest Gluetun-forwarded port  
✅ Detects Gluetun VPN reconnections and updates automatically  
✅ Optional **firewall monitor** — restarts qBittorrent if it becomes firewalled  
✅ Optional **webhook notifications** (Discord, Slack, ntfy, Gotify, etc.)  
✅ Built for Docker — minimal footprint (~15MB)  
✅ Works with WireGuard and OpenVPN connections  

---

## 🧩 Example Docker Compose Setup

```yaml
services:
  gluetun:
    image: qmcgaw/gluetun:latest
    container_name: gluetun
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    ports:
      - 8888:8888/tcp # HTTP proxy
      - 8388:8388/tcp # Shadowsocks
      - 8388:8388/udp # Shadowsocks
      - 8000:8000 # required for Gluetun API access
      # Other services
      # qBittorrent
      - 9092:9092  # qBittorrent Web UI
      #- 6881:6881 #torrenting port  Not needed if using qBittorrent with network_mode: "service:gluetun"
      #- 6881:6881/udp #torrenting port  Mpt needed if using qBittorrent with network_mode: "service:gluetun"
      # Other containers that are being routed via the container where you still want access the resources like web ui on local network
    networks:
      internal:
      web:
    volumes:
      - /configs/gluetun:/gluetun
    environment:
      # I specify the PUID and PGID but this is optional (default is 1000,1000), description from Wiki "User ID/Group ID to run as non root and for ownership of files written"
      - PUID=1001
      - PGID=100
      - UMASK=002
      - TZ=America/New_York
      # See https://github.com/qdm12/gluetun-wiki/tree/main/setup#setup
      #- VPN_SERVICE_PROVIDER=custom
      - VPN_SERVICE_PROVIDER=protonvpn
      - VPN_TYPE=wireguard
      # OpenVPN:
      #- OPENVPN_USER=
      #- OPENVPN_PASSWORD=
      # Wireguard:
      #- WIREGUARD_PUBLIC_KEY="Daer24dSnQMoGm/LIDjPbKgrlUjF0ldjiDA9dfe+EXk="
      #- WIREGUARD_PRIVATE_KEY="2PQELfYggxzvppKFkj68FKPYBSSQwea6roE5T/0CP0M="
      - WIREGUARD_PRIVATE_KEY=XXXXXXXXXXXXXXXXXX
      - SERVER_COUNTRIES=United States
      - PORT_FORWARD_ONLY=on
      #- WIREGUARD_ADDRESSES=10.2.0.2/32
      #- VPN_ENDPOINT_IP=146.70.202.130 # "Endpoint" under [Peer] in WG Config
      #- VPN_ENDPOINT_PORT=51820 # should be the default 51820 but can confirm by seeing the port after IP in "Endpoint"
      #- VPN_DNS_ADDRESS=DNS = 10.2.0.1 # "DNS" under [Interface] in WG Config
      - VPN_PORT_FORWARDING=on
      - VPN_PORT_FORWARDING_PROVIDER=protonvpn
      # Server list updater
      # See https://github.com/qdm12/gluetun-wiki/blob/main/setup/servers.md#update-the-vpn-servers-list
      - UPDATER_PERIOD=24h
      - HTTP_CONTROL_SERVER_USER=admin
      - HTTP_CONTROL_SERVER_PASSWORD=password
    labels:
      - "com.centurylinklabs.watchtower.enable=True"
    restart: unless-stopped

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    network_mode: "service:gluetun"
    depends_on:
      gluetun:
        condition: service_healthy
    environment:
      - PUID=1001
      - PGID=100
      - UMASK=002
      - TZ=America/New_York
      - WEBUI_PORT=9092
      #- TORRENTING_PORT=6881
    volumes:
      - /configs/qbittorrent:/config
      - /downloads:/downloads #optional
      - /media:/media #optional for uploading
    labels:
      - "com.centurylinklabs.watchtower.enable=True"
    healthcheck:
      test: curl --fail http://ifconfig.me/ || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
      #test: "ifconfig | grep -q eth0"
      #interval: 1m
      #timeout: 30s
      #retries: 0
    restart: unless-stopped

  qb-port-sync:
    #build: ./qb-port-sync
    image: adxglock/qb-port-snyc:latest
    container_name: qb-port-sync
    network_mode: "service:gluetun"
    depends_on:
      gluetun:
        condition: service_healthy
      qbittorrent:
        condition: service_healthy
    environment:
      - PUID=1001
      - PGID=100
      - TZ=America/New_York
      - GLUETUN_API=http://localhost:8000/v1/openvpn/portforwarded
      - GLUETUN_USER=admin
      - GLUETUN_PASS=password
      - QBITTORRENT_HOST=http://localhost:9092
      - QBITTORRENT_USER=admin
      - QBITTORRENT_PASS=adminadmin
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      - "com.centurylinklabs.watchtower.enable=True"
    healthcheck:
      test: curl --fail http://ifconfig.me/ || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
networks:
  internal:
    external: true
    name: internal
  web:
    external: true
    name: web
```

📝 **Tip:**  
Make sure `qbittorrent` and `qb-port-sync` share the same network namespace as Gluetun by using  
`network_mode: "service:gluetun"`.  
This allows API access via `localhost` inside the shared namespace.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|-----------|----------|-------------|
| `GLUETUN_API` | `http://localhost:8000/v1/openvpn/portforwarded` | Gluetun API endpoint |
| `GLUETUN_USER` | `admin` | Gluetun control server username |
| `GLUETUN_PASS` | `password` | Gluetun control server password |
| `QBITTORRENT_HOST` | `http://localhost:9092` | qBittorrent WebUI base URL |
| `QBITTORRENT_USER` | `admin` | qBittorrent WebUI username |
| `QBITTORRENT_PASS` | `adminadmin` | qBittorrent WebUI password |
| `CHECK_INTERVAL` | `300` | Poll interval in seconds |
| `MONITOR_FIREWALL` | `true` | If enabled, restarts qBittorrent when firewalled |
| `QBT_CONTAINER_NAME` | `qbittorrent` | Container name to restart |
| `WEBHOOK_URL` | *(optional)* | Webhook URL for notifications |

---

## 🔍 How It Works

1. Polls the Gluetun control API (`/v1/openvpn/portforwarded`) every few minutes  
2. Reads the latest VPN-forwarded port number  
3. Logs into qBittorrent’s WebUI via API  
4. Updates its `listen_port` dynamically  
5. (Optional) Checks for “firewalled” state and restarts the qBittorrent container  
6. (Optional) Sends webhook notifications when changes or restarts occur

---

## 🧪 Manual Run Example

```bash
docker run --rm \
  -e GLUETUN_API=http://localhost:8000/v1/openvpn/portforwarded \
  -e GLUETUN_USER=admin \
  -e GLUETUN_PASS=password \
  -e QBITTORRENT_HOST=http://localhost:9092 \
  -e QBITTORRENT_USER=admin \
  -e QBITTORRENT_PASS=yourpass \
  -v /var/run/docker.sock:/var/run/docker.sock \
  adxglock/qb-port-sync:latest
```

---

## 🧰 Build Locally

```bash
git clone https://github.com/ADXGlock/qb-port-sync.git
cd qb-port-sync
docker build -t adxglock/qb-port-sync:latest .
```

---

## 📦 DockerHub Auto-Build

This repo includes a GitHub Actions workflow that:
- Builds and pushes multi-arch Docker images (`amd64` and `arm64`)
- Tags builds automatically (`latest` and version tags)
- Runs on every push to `main` or tag like `v1.0.0`

You just need two GitHub Secrets:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

---

## 🧑‍💻 Maintainer

**Author:** ADXGlock  
**GitHub:** [ADXGlock](https://github.com/ADXGlock)  
**DockerHub:** [adxglock](https://hub.docker.com/r/adxglock/qb-port-sync)

---

## 🛡️ License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## ⭐ Support

If you find this project helpful:
- ⭐ Star it on [GitHub](https://github.com/ADXGlock/qb-port-sync)
- 🐋 Pull it from [DockerHub](https://hub.docker.com/r/adxglock/qb-port-sync)
- ☕ Buy the author a coffee (optional)

---

### 💬 Example webhook notification (ntfy)

If you set `WEBHOOK_URL=https://ntfy.sh/qb-port-sync`, you’ll receive:
```
🔁 Updated qBittorrent port to 42311
⚠️ qBittorrent is firewalled. Restarting container...
```

---

By ADXGlock
For Gluetun + qBittorrent power users.
