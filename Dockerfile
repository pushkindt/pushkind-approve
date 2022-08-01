FROM python:slim

RUN useradd pushkind

WORKDIR /home/pushkind

RUN apt-get update
RUN apt-get -y install default-libmysqlclient-dev gcc vim-nox
COPY requirements.txt requirements.txt
RUN python3 -m venv venv
RUN venv/bin/python3 -m pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY approve.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP approve.py

RUN chown -R pushkind:pushkind ./
USER pushkind

CMD ["./boot.sh"]
