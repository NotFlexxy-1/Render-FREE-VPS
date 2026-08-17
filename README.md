# HyperVM Debian 13 Render Console

This project runs a Debian 13 container on Render and exposes an authenticated browser terminal backed by a real PTY and `/bin/bash`.

## Render settings

Create a **Web Service** and choose **Docker**. Render will build the included `Dockerfile`.

Set an Environment Variable / Secret:

- `CONSOLE_TOKEN` = a long random secret

Render automatically supplies `PORT`; do not hard-code a public port in the Render dashboard.

## Local test

```bash
docker build -t hypervm-console .
docker run --rm -p 10000:10000 -e CONSOLE_TOKEN='replace-with-a-long-secret' hypervm-console
```

Then open `http://localhost:10000`.

## Important limitation

The browser terminal is a shell inside the Render container. It is not equivalent to a privileged VPS. Host/kernel operations, nested Docker/LXC, KVM, and unrestricted systemd behavior are outside what a normal Render container provides.
