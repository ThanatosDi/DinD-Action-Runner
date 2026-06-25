FROM docker:29.4.1-cli-alpine3.23

WORKDIR /app

COPY docker/workspace/root.crontab /etc/crontabs/root

ENTRYPOINT [ "sh", "-c", "docker/workspace/workspace.entrypoint.sh && crond -f" ]