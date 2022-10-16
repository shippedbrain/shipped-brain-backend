FROM continuumio/miniconda3

RUN apt update
RUN apt install python3-pip -y
RUN conda update -n base -c defaults conda

WORKDIR /app

ADD ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

ADD ./src/ .
