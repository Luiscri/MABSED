FROM python:3.6

COPY requirements.txt /usr/src/orchestrator/
RUN pip install -r requirements.txt

COPY tasks.py /usr/src/orchestrator/
COPY detector/ /usr/src/orchestrator/detector/
COPY filter/ /usr/src/orchestrator/filter/
COPY lemmatizer/ /usr/src/orchestrator/lemmatizer/