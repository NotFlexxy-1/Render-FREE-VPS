FROM debian:13

ENV DEBIAN_FRONTEND=noninteractive
ENV container=docker

USER root

WORKDIR /root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        systemd \
        systemd-sysv \
        dbus \
        dbus-user-session \
        bash \
        bash-completion \
        sudo \
        curl \
        wget \
        git \
        ca-certificates \
        openssh-server \
        openssh-client \
        rsync \
        nano \
        vim \
        less \
        htop \
        tree \
        unzip \
        zip \
        tar \
        gzip \
        bzip2 \
        xz-utils \
        jq \
        file \
        lsof \
        procps \
        psmisc \
        iproute2 \
        iputils-ping \
        net-tools \
        dnsutils \
        traceroute \
        socat \
        netcat-openbsd \
        ncdu \
        pciutils \
        usbutils \
        kmod \
        locales \
        tzdata \
        cron \
        logrotate \
        gnupg \
        openssl \
        python3 \
        python3-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Root sudo
RUN printf '%s\n' \
    'root ALL=(ALL:ALL) NOPASSWD: ALL' \
    > /etc/sudoers.d/root && \
    chmod 0440 /etc/sudoers.d/root

# SSH directories
RUN mkdir -p /run/sshd /root/.ssh && \
    chmod 700 /root/.ssh

# Don't bake a password into the image.
# Set ROOT_PASSWORD in Render if you need one.
COPY start.sh /usr/local/bin/start.sh
RUN chmod 0755 /usr/local/bin/start.sh

# Minimal HTTP endpoint required by Render Web Service.
COPY health.py /opt/health.py

EXPOSE 22

CMD ["/usr/local/bin/start.sh"]
