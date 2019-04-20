`<tweet-chart>` is a web component designed to visualize Tweets and visualize each Tweet sentiment.
Tweet background is coloured green if tweet's text is posive, red if it is negative or grey if neutral.
This web component obtains data from an elasticSearch index.

### Usage

This web component accepts the following parameters:

```html

<tweet-chart
    datos="{{data}}"   
    icon='face'>
</tweet-chart>

```

### Installation

This web component is available in bower. 

```bash

$ bower install tweet-chart

```

This command will install it inside `bower_components` folder

Remember to edit your `elements.html` with this component.