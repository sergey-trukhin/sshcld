FROM python:3.10.4-alpine3.16
LABEL maintainer="Sergey Trukhin <satruhin@gmail.com>"

WORKDIR /app/

COPY ${PWD}/requirements.txt /app/tests/requirements.txt
RUN pip3 install -r /app/tests/requirements.txt

COPY ${PWD}/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
