FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3.7 
RUN python3.7 -m venv venv --without-pip
RUN apt-get install -y curl
RUN apt-get update
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN rm get-pip.py

COPY ./ /home/project/
RUN ls -la /home/project/*
WORKDIR /home/project

RUN pip install -r requirements.txt

# ENTRYPOINT ["python3"]
