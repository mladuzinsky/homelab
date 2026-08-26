#!/usr/bin/env python3
"""Detect the Linux distribution and install Ansible using the appropriate package manager."""

import os
import shutil
import subprocess
import sys


def require_root():
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo).", file=sys.stderr)
        sys.exit(1)


def read_os_release():
    info = {}
    path = "/etc/os-release"
    if not os.path.isfile(path):
        print(f"Cannot detect distribution: {path} not found.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            info[key] = value.strip().strip('"')
    return info


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def install_ansible(os_release):
    distro_id = os_release.get("ID", "").lower()
    id_like = os_release.get("ID_LIKE", "").lower()
    family = f"{distro_id} {id_like}"

    if any(name in family for name in ("debian", "ubuntu")):
        run(["apt-get", "update"])
        run(["apt-get", "install", "-y", "ansible"])

    elif any(name in family for name in ("rhel", "centos", "fedora", "rocky", "almalinux")):
        pkg_mgr = "dnf" if shutil.which("dnf") else "yum"
        if pkg_mgr == "yum":
            # EPEL is required on older RHEL/CentOS to get the ansible package.
            run(["yum", "install", "-y", "epel-release"])
        run([pkg_mgr, "install", "-y", "ansible"])

    elif "arch" in family:
        run(["pacman", "-Sy", "--noconfirm", "ansible"])

    elif any(name in family for name in ("suse", "sles")):
        run(["zypper", "--non-interactive", "install", "ansible"])

    elif "alpine" in family:
        run(["apk", "add", "ansible"])

    else:
        print(f"Unsupported or undetected distribution (ID={distro_id!r}, ID_LIKE={id_like!r}).",
              file=sys.stderr)
        print("Please install Ansible manually.", file=sys.stderr)
        sys.exit(1)


def verify_installation():
    try:
        result = subprocess.run(["ansible", "--version"], capture_output=True, text=True, check=True)
        print("\nAnsible installed successfully:")
        print(result.stdout.splitlines()[0])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ansible installation could not be verified.", file=sys.stderr)
        sys.exit(1)


def main():
    require_root()
    os_release = read_os_release()
    name = os_release.get("PRETTY_NAME", "Unknown Linux")
    print(f"Detected distribution: {name}")

    try:
        install_ansible(os_release)
    except subprocess.CalledProcessError as e:
        print(f"Installation command failed: {e}", file=sys.stderr)
        sys.exit(1)

    verify_installation()


if __name__ == "__main__":
    main()
