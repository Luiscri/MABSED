FROM python:3.6

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD tasks.py .
ADD data/ .
ADD detector/ .
ADD filter/ .
ADD lemmatizer/ .


