`<google-chart>` is a web component designed to visualize data with Google Charts but obtaining data from an elasticSearch index.

### Usage

This web component accepts the following parameters:

```html

<google-chart
    data="<!-- json with the ElasticSearch results -->"
    field="<! -- field to visualize -->"
    subfield="<! -- subfield to visualize (in case of nested aggregations) -->"
    type='<!-- google chart type: column, pie, column, etc -->'
    filters="{{filters}}"
    icon='<!-- iron icon -->'
    param='{{param}}'
    options='<!-- google chart options -->'
    cols='<!-- columns of the data -->'
</google-chart>

```


An example of use is given in the folder demo.

For more information visit: https://developers.google.com/chart/

### Installation

This web component is available in bower. 

```bash

$ bower install google-chart-elasticsearch

```

This command will install it inside `bower_components` folder

Remember to edit your `elements.html` with this component.

## Development

Requirements:

 * Docker
 * Docker-compose

The docker-compose file can be used to test the component and to develop it.
Simply run:

```
docker compose up
```

And go to http://127.0.0.1:8080/demo/index.html

The docker-compose file mounts the current directory in the docker container, so every change you make to files locally will be reflected immediately in the browser.

If you add new dependencies to the compponent (through the `bower.json` file), you need to either run `bower install` within the container or recreate the image, like so:

```
docker compose up --build

```

Or:

```
docker exec web bower install
```

Note that the component assumes all dependencies are added in `../`.
This is the structure the component will find when installed as a dependency with bower.
To mimic that structure, the `init.sh` script automatically links the bower package.