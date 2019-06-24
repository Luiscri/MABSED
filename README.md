# MABSED

![MABSED logo](./demo-dashboard/img/MABSEDlogoAzul.png)

## About

MABSED (Mention-Anomaly Based Streaming Event Detector) is a monitoring system which allows the user to track the top three most impactful events that have been discussed on a social network as Twitter in the last 24 hours. This study has focused on the city of Madrid, but it can be applied to any other city or even country.

Detection module bases his predictions on the total number of users and mentions that each event has involved. Moreover, results are displayed in a visualization module allowing the viewer to identify each event characteristics as well as its temporal and spatial patterns through different widgets.

## Author

Luis Cristóbal López García

## Performance

The system is completely Dockerized and has a multi-container structure with four different services which interacts between them; proyect can be raised with a single command, starting all the process. Detector needs at least a 24-hour dataset in order to achieve a proper detection, so once the process is started it will first enter a collection phase where tweets will be saved in the host file system. Once this phase is over the detection task will be performed every 30 minutes, returning the top three events ocurred in the last 24 hours and saving the results in a persistence layer provided by ElasticSearch. Progress can be tracked at any time by the information displayed on console.

## Requirements

Before the project can be executed there are certain requirements and instructions that must be pleased.
1. Since the project will be deployed using Docker, host system will need to install it in case it doesn't already have it. Moreover docker-compose is also needed, so although this process can vary depeding on the Operative System you can follow [this](https://docs.docker.com/compose/install/) link if you need more information.
2. User must have access to a Twitter Developer Account in order to collect the Streaming data. Once the application has been registered and all the necessary keys have been obtained they must be uploaded to `Project/streamer/credentials.py` file.
3. Finally, some services need to share data saved in a host local folder. This will be achieved by a Docker volume which will be mounted later in each Docker container, so before running the project you will need to specify at `Project/.env` file the ABSOLUTE path to the `Project/data/` folder, which will be different for every user.
 
## Usage
 
Once the requirements are met you can move to the project path and start it with the command:

```
sudo docker-compose up
```

As have been said before, data will be saved in `Project/data/` folder. Within this route there will be different folders containing (I) the collected streaming tweets grouped in 30 minutes interval files, (II) preprocessed data once spam has been filtered away and the text lemmatized, (III) every tweet that has been labeled as spam and (IV) the detection results, which will be saved later in ElasticSearch.

Data stored in the persistence layer can be accessed through the following route.

```
http://localhost:9200/
```

There are two different indices where data is stored: `mabsed-events` (for each event information) and `mabsed-tweets` (for the tweets describing to each event). For example, if we wanted to see 100 tweets stored in ES, we would follow this route:

```
http://localhost:9200/mabsed-tweets/_search?size=100
```

Finally, the Dashboard with which the user can interact and see the detection results is found in:

```
http://localhost:8080/
```

## References

If a deeper understanding of the project is desired the lecture of the document contained in this repository is highly recommended.

For further investigations, please cite this repository as well as the author name in your publications.

The approach employed as base line for the final detection model was developed by Adrien Guille and Cécile Favre. You can learn more about this project in [this](http://mediamining.univ-lyon2.fr/people/guille/publications/snam.pdf) publication, and its lecture is also recommended in case changes want to be applied to the project.