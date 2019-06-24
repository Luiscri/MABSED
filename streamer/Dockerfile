FROM python:3.6

RUN pip3 install --user tweepy

WORKDIR /usr/src/app/
COPY startStreaming.py /usr/src/app/
COPY credentials.py /usr/src/app/

CMD python startStreaming.py