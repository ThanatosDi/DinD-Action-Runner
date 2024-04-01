FROM python:3.10-bookworm

WORKDIR /tmp

COPY ../../requirements.txt /tmp/requirements.txt

RUN pip install -r requirements.txt

RUN apt update && apt install ca-certificates curl -y --no-install-recommends

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc

RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt update && apt install docker-ce-cli -y --no-install-recommends

WORKDIR /app

CMD ["python"]