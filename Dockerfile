FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y python3-pip python-dev\
  && apt-get install -y software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get install -y python3.6 \
  && apt-get update

RUN apt-get install -y python3-pip python3.6-dev \
  && pip3 install --upgrade pip \
  && apt-get install -y curl \
  && apt-get update

# venv build
# without the use of VIRTUAL_ENV the venv will not activate or be seen
ENV VIRTUAL_ENV=/opt/venv
RUN python3.6 -m venv $VIRTUAL_ENV --without-pip
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN rm get-pip.py
RUN python --version
RUN pip --version

# pip install from requirements is bypassed due to wxPython issue.
RUN python -m pip install coverage \
  coverage \
  nose \
  setuptools~=47.1.0 \
  jsonschema~=3.2.0 \
  pyinstaller~=4.2

# special wxPython install
RUN python -m pip install -U \
  -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 \
  wxPython
RUN python -m pip install pypubsub

# additional packages needed to compile project
RUN apt-get install -y libgtk-3-0 \
  libxxf86vm-dev \
  libsm6 \
  libnotify-dev \
  libsdl2-dev

ADD ./ /home/project/
WORKDIR /home/project/epjsoneditor/

RUN pyinstaller linux_onefile_main.spec
#RUN pyinstaller main.spec