#!/bin/bash
set -e

PORT="${PORT:-10000}"

echo "======================================"
echo "      DEBIAN 13 RENDER CONTAINER"
echo "======================================"

# Root password, only when supplied as a Render secret.
if [ -n "${ROOT_PASSWORD:-}" ]; then
    echo "root:${ROOT_PASSWORD}" | chpasswd
fi

# Generate SSH host keys.
ssh-keygen -A >/dev/null 2>&1 || true

mkdir -p /run/sshd

# Start SSH for container-side access where supported.
/usr/sbin/sshd || true

# Start the HTTP health endpoint required by Render.
python3 /opt/health.py &

echo "Debian version:"
cat /etc/debian_version || true

echo "systemd version:"
systemctl --version | head -n 1 || true

echo "Container initialized."

# Keep the main process alive.
exec tail -f /dev/null
