FROM alpine:latest

WORKDIR /home/sandboxfs
ADD requirements.txt ./
ADD socketfs_server.py ./
ADD start_sandboxfs.sh ./

RUN apk update && apk add python3 \
&& apk add py3-pip \
&& pip install --upgrade pip \
&& pip install -r requirements.txt

CMD /bin/sh start_sandboxfs.sh
