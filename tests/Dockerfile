FROM python:3.10.4-alpine3.16
LABEL maintainer="Sergey Trukhin <satruhin@gmail.com>"

WORKDIR /app/tests/

COPY ${PWD}/requirements.txt /app/tests/requirements.txt
RUN pip3 install -r requirements.txt

CMD ["pytest", "-p", "no:cacheprovider"]
