FROM docker:26.0.0-cli-alpine3.19

WORKDIR /app

COPY docker/workspace/root.crontab /etc/crontabs/root

ENTRYPOINT [ "sh", "-c", "docker/workspace/workspace.entrypoint.sh && sh" ]