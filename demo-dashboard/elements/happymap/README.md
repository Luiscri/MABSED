# HappyMap Element

HappyMap is a Polymer element that visualizes with different layers analyzed tweets by Senpy.

# Demo

  - Clone this project
  - Run at root project's path: *python -m SimpleHTTPServer*
  - Go to *localhost:8000/demo* to see HappyMap in action   

# Layers
This element shows several layers to display the anlayzed data. Right now it displays four different layers, and each one have a certain meaning:
  - HappyMap Layer: Heatmap that shows the evolution of the valence score got from Senpy.
  - IntenseMap Layer: Heatmap that shows the evolution of the arousal score got from Senpy.
  - PowerMap Layer: Heatmap that shows the evolution of the dominance score got from Senpy.
  - EmojiMap Layer: Clusterization map that shows with emojis over a grographical zone what are the.

All heatmaps use [Leaflet.Heat plugin](https://github.com/Leaflet/Leaflet.heat) and the EmojiMap uses [Leaflet.Markercluster plugin](https://github.com/Leaflet/Leaflet.markercluster)


# Installation
You can easily install HappyMap in your project via Bower with:
```sh
$ bower install happymap-element
```

# Implementation
An implementation example can be found in [this demo dashboard](https://lab.cluster.gsi.dit.upm.es/sefarad/happymap-dashboard)

Supposing that you are familiar with Polymer modular development, here are some aspects to have into account when implementing HappyMap:

#### Parameters
happymap-element receives two array parameters: *data* and *selected*.
- *data*: Tweets that have to display in the map
- *selected*: Tweets that have to be markers markers on the map. It should be a fraction of data, but it will actually work with any dataset.

#### Required dataset structure
The dashboard HappyMap is integrated on have to provide data in certain form in order to it to understand it (this applies to *data* and *selected* parameters). Data have to be a JS object array and each object have to contain the following attributes:
- text (string): Tweet text that will be displayed when clicking a marker
- lat (int, double or float): latitude from the tweet was posted
- lon (int, double or float): longitude from the tweet was posted
- valence (int, double or float): Valence score obtained from Senpy emotion-anew analysis
- arousal (int, double or float): Arousal score obtained from Senpy emotion-anew analysis
- dominance (int, double or float): Dominance score obtained from Senpy emotion-anew analysis
- emotion (string): tag corresponding to either "joy", "sadness", "negative-fear", "disgust", or "anger".
