#!/usr/bin/env python3
"""Detect the OS (Linux or Windows) and install VirtualBox using the appropriate method."""

import argparse
import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request

# Fallback direct-download URL used on Windows only if neither winget nor
# choco is available. Update this if VirtualBox releases a newer version.
WINDOWS_FALLBACK_URL = "https://download.virtualbox.org/virtualbox/7.1.6/VirtualBox-7.1.6-167084-Win.exe"

DRY_RUN = False


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    if DRY_RUN:
        return
    subprocess.run(cmd, check=True)


def require_admin():
    if DRY_RUN:
        return
    system = platform.system()
    if system == "Windows":
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            print("This script must be run from an elevated (Administrator) prompt.", file=sys.stderr)
            sys.exit(1)
    else:
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


def install_linux():
    os_release = read_os_release()
    distro_id = os_release.get("ID", "").lower()
    id_like = os_release.get("ID_LIKE", "").lower()
    family = f"{distro_id} {id_like}"
    name = os_release.get("PRETTY_NAME", "Unknown Linux")
    print(f"Detected distribution: {name}")

    if any(name in family for name in ("debian", "ubuntu")):
        run(["apt-get", "update"])
        run(["apt-get", "install", "-y", "virtualbox"])

    elif any(name in family for name in ("rhel", "centos", "fedora", "rocky", "almalinux")):
        pkg_mgr = "dnf" if shutil.which("dnf") else "yum"
        print("Note: VirtualBox is not in the default Fedora/RHEL repos and usually "
              "requires RPM Fusion (free) to be enabled first.")
        run([pkg_mgr, "install", "-y", "VirtualBox"])

    elif "arch" in family:
        run(["pacman", "-Sy", "--noconfirm", "virtualbox"])

    elif any(name in family for name in ("suse", "sles")):
        run(["zypper", "--non-interactive", "install", "virtualbox"])

    else:
        print(f"Unsupported or undetected distribution (ID={distro_id!r}, ID_LIKE={id_like!r}).",
              file=sys.stderr)
        print("Please install VirtualBox manually.", file=sys.stderr)
        sys.exit(1)


def install_windows():
    if shutil.which("winget"):
        run(["winget", "install", "-e", "--id", "Oracle.VirtualBox",
             "--accept-package-agreements", "--accept-source-agreements"])
        return

    if shutil.which("choco"):
        run(["choco", "install", "virtualbox", "-y"])
        return

    print("Neither winget nor choco found; downloading installer directly from Oracle.")
    print(f"Source: {WINDOWS_FALLBACK_URL}")
    with tempfile.TemporaryDirectory() as tmpdir:
        installer_path = os.path.join(tmpdir, "VirtualBox-Setup.exe")
        if DRY_RUN:
            print(f"$ download {WINDOWS_FALLBACK_URL} -> {installer_path}")
        else:
            urllib.request.urlretrieve(WINDOWS_FALLBACK_URL, installer_path)
        run([installer_path, "-silent"])


def verify_installation():
    if DRY_RUN:
        print("\n(dry run: skipping verification)")
        return
    vboxmanage = "VBoxManage.exe" if platform.system() == "Windows" else "vboxmanage"
    try:
        result = subprocess.run([vboxmanage, "--version"], capture_output=True, text=True, check=True)
        print("\nVirtualBox installed successfully:")
        print(result.stdout.strip().splitlines()[0])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("VirtualBox installation could not be verified "
              "(you may need to open a new shell for PATH changes to take effect).",
              file=sys.stderr)


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description="Install VirtualBox on Linux or Windows.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Print the commands that would run without executing them.")
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    require_admin()
    system = platform.system()

    try:
        if system == "Linux":
            install_linux()
        elif system == "Windows":
            install_windows()
        else:
            print(f"Unsupported OS: {system}", file=sys.stderr)
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Installation command failed: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)

    verify_installation()


if __name__ == "__main__":
    main()
