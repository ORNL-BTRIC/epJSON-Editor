FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get install -y python3.7 \
  && apt-get update

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
RUN update-alternatives --config python
RUN python --version
RUN apt-get update \
  && apt-get install -y python3-pip python3.7-dev \
  && pip3 install --upgrade pip
RUN pip --version

ADD ./ /home/project/
WORKDIR /home/project/epjsoneditor/

# pip install from requirements is bypassed due to wxPython issue.
RUN python3.7 -m pip install coverage \
  coverage \
  nose \
  setuptools~=47.1.0 \
  jsonschema~=3.2.0 \
  pyinstaller~=4.2

RUN python3.7 -m pip install -U \
  -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 \
  wxPython
RUN python3.7 -m pip install pypubsub

RUN pyinstaller -F main.py

# ENTRYPOINT ["python3"]
