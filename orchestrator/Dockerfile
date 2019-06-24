FROM python:3.6

WORKDIR /usr/src/app/

COPY requirements.txt ./
RUN pip3 install --user -r requirements.txt

COPY my_sched.py ./
COPY tasks.py ./
COPY detector/ ./detector/
COPY filter/ ./filter/
COPY lemmatizer/ ./lemmatizer/

CMD python my_sched.py