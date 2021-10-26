FROM alpine

RUN apk add --no-cache python3 gcc make curl-dev libc-dev json-c-dev sqlite-dev argp-standalone py3-pip libressl-dev libffi-dev python3-dev openssl-dev cargo

RUN pip install wheel flask pyopenssl

ENV FLASK_APP=/app/tests/ecwid/app.py

WORKDIR /app

COPY . .

CMD ["make", "tests"]