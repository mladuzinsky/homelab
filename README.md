# Homelab Ansible

Ansible setup and automation for managing the servers and IoT devices on my home network.

## Goals

- Bootstrap Ansible onto a fresh control node regardless of Linux distro
- Maintain a single inventory of all home servers and IoT devices
- Use playbooks/roles to configure, update, and manage those hosts consistently

## Repo layout

```
.
├── install_ansible.py   # Detects the Linux distro and installs Ansible
├── inventory/            # Ansible inventory (hosts, groups) — TBD
├── playbooks/             # Ansible playbooks — TBD
└── roles/                # Reusable Ansible roles — TBD
```

(Inventory, playbooks, and roles will be added as the project grows.)

## Getting started

### 1. Install Ansible on the control node

`install_ansible.py` detects your Linux distribution via `/etc/os-release` and installs Ansible using the correct package manager (`apt`, `dnf`/`yum`, `pacman`, `zypper`, or `apk`).

```bash
sudo python3 install_ansible.py
```

Supported distro families: Debian/Ubuntu, RHEL/CentOS/Fedora/Rocky/AlmaLinux, Arch, openSUSE/SLES, Alpine.

### 2. Verify

```bash
ansible --version
```

### 3. Define your inventory

Add your servers and IoT devices to `inventory/hosts.yml` (or `.ini`), grouped by type, e.g.:

```yaml
all:
  children:
    servers:
      hosts:
        nas:
          ansible_host: 192.168.1.10
    iot:
      hosts:
        living_room_pi:
          ansible_host: 192.168.1.20
```

### 4. Run playbooks

```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

## Notes

- SSH key-based auth to all managed hosts is recommended over passwords.
- Keep secrets (Wi-Fi passwords, API keys, etc.) out of this repo — use `ansible-vault` for anything sensitive.
