FROM ubuntu:22.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get dist-upgrade -y \
    && apt-get install -y --no-install-recommends \
    wget \
    python3-pip \
    python3-setuptools \
    && cd /usr/local/bin \
    && pip3 --no-cache-dir install --upgrade pip \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    openssh-server \
    git \
    librdkafka-dev \
    bash \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


RUN apt-get remove --purge -y linux-libc-dev

# Update system packages and install required dependencies, including LTS Vim version

WORKDIR /srv/wayne

COPY ./requirements/requirements.txt .

## Creating and activating a virtual environment
#RUN python3 -m venv /opt/venv
#ENV VIRTUAL_ENV /opt/venv
#ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install --upgrade pip setuptools wheel && pip3 install -r ./requirements.txt



# Update system packages and install required dependencies again in the runtime image, ensuring Vim LTS version
#RUN apt update && apt upgrade -y && apt-get install -y \
#    build-essential \
#    git \
#    vim-nox \
#    librdkafka-dev \
#    linux-libc-dev && \
#    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/wayne
RUN mkdir /srv/wayne/repos
#COPY --from=builder /srv/wayne .
#COPY --from=builder /opt/venv /opt/venv



EXPOSE 80

ENTRYPOINT ["python3", "entrypoint.py"]
