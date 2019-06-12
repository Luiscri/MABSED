FROM node:7.10.0

# Install gettext to get envsubst
RUN sed -i '/jessie-updates/d' /etc/apt/sources.list  # Now archived
RUN apt-get update && apt-get install -y gettext

ENV NODE_PATH=/tmp/node_modules APP_NAME=demo-dashboard

# Install dependencies first to use cache
RUN npm install -g http-server bower

WORKDIR /usr/src/app/

RUN mkdir -p /etc/ssl/certs
COPY lab.cluster.gsi.dit.upm.es.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

ADD bower.json /usr/src/app/bower.json

RUN bower link --allow-root
RUN bower install --allow-root  && mv bower_components ..

ADD . /usr/src/app

CMD ["/usr/src/app/init.sh"]