FROM python:3.11

RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN mkdir /app
COPY discord_crawler/ /app/

WORKDIR /app
