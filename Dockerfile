FROM docker.io/library/alpine:latest AS builder
ARG ghtoken
WORKDIR /build

RUN apk add --update --no-cache github-cli openssh-keygen python3

COPY requirements.txt .
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && pip install --no-cache-dir -r requirements.txt

RUN echo ${ghtoken} | gh auth login --with-token
RUN gh release download -R chenxiaolong/avbroot -p '*-x86_64-unknown-linux-gnu.zip*'
RUN gh release download -R chenxiaolong/Custota -p '*-x86_64-unknown-linux-gnu.zip*'
RUN gh release download -R topjohnwu/Magisk -p 'Magisk-*.apk'

RUN echo chenxiaolong ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDOe6/tBnO7xZhAWXRj3ApUYgn+XZ0wnQiXM8B7tPgv4 > chenxiaolong_trusted_keys
RUN cat avbroot-*.zip | ssh-keygen -Y verify -f chenxiaolong_trusted_keys -I chenxiaolong -n file -s avbroot-*.sig
RUN cat custota-*.zip | ssh-keygen -Y verify -f chenxiaolong_trusted_keys -I chenxiaolong -n file -s custota-*.sig

RUN unzip avbroot-*.zip avbroot
RUN unzip custota-*.zip custota-tool
RUN mv Magisk* 'magisk.apk'

FROM docker.io/library/alpine:latest
WORKDIR /opt

RUN apk add --update --no-cache python3
COPY --from=builder /opt/venv .
COPY updater .
COPY generate-keys .
RUN chmod +x updater generate-keys

WORKDIR /usr/bin
COPY --from=builder /build/magisk.apk /opt/magisk.apk
COPY --from=builder /build/custota-tool .
COPY --from=builder /build/avbroot .
RUN chmod +x custota-tool avbroot

WORKDIR /
COPY crontab crontab.tmp
RUN crontab crontab.tmp && rm crontab.tmp
RUN mkdir publish
CMD crond -l 4 -f
