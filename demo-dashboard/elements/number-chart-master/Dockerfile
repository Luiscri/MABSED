from node:7.10.0

ENV NODE_PATH=/tmp/node_modules APP_NAME=number-chart

# Install dependencies first to use cache
RUN npm install -g http-server bower

ADD bower.json /usr/src/bower.json
RUN cd /usr/src && \
    bower install --allow-root && \
    cp -a /usr/src/bower_components /usr/src/app/
 
ADD . /usr/src/app
RUN chmod +x /usr/src/app/init.sh
WORKDIR /usr/src/app

CMD ["/usr/src/app/init.sh"]
