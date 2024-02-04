# Literature Analysis

This container will deploy the literature analysis module. It is supposed to read a collection of documents (from MongoDB), enrich them with biomedical entities and relations found in the text body and save the results, both in MongoDB and Neo4j, populating the knowledge graph.

This does not expose an API service, just runs ones and exits.


## Prerequisities
In summary, in order to run this container you'll need the following installed:
    * [Docker](https://docs.docker.com/)
    * [MongoDB](https://www.mongodb.com/)
    * [Neo4j](https://neo4j.com/)
    * [MetaMap](https://metamap.nlm.nih.gov/)
    * [SEMREP](https://semrep.nlm.nih.gov/)

This project is based around concept and relation extractions from text using [SEMREP](https://semrep.nlm.nih.gov/) and and [MetaMap](https://metamap.nlm.nih.gov/). Follow, instructions on their website in order to set-up a copy on they deployment server. Make sure that the SemRep and MetaMap root folders are in the same parent folder.

**IMPORTANT**: The container needs access to the folders of these two installed softwares, in order to set-up services and use them for biomedical entity/relation extraction. It is working under the assumption that we can mount the volume containing these folders to the container, alongside the **settings.yaml located in a different folder**.

### Usage
#### Settings Parameters

To start with, the module needs information regarding connectivity with MongoDB, Neo4j and other details related to the relation extraction task. We provide the needed info through a **settings.yaml** which also contains information regarding paths to the mounted folders. A sample settings file is provided.

To customize these settings according to any local enviroment one has to pay attention to the following things.

1) First of all the installed SemRep and MetaMap root folders should be in the same parent folder. The expected structure is:
-- /path/to/folder/with/SEMREP/and/Metamap/
    - SEMREP
    - MetaMap
2) Change the path to semrep and metamap files in settings.yaml (Lines 55,59):
```
        metamap: /path/to/folder/with/SEMREP/and/Metamap/Metamap/public_mm/bin/
        semrep: /path/to/folder/with/SEMREP/and/Metamap/SEMREP/public_semrep/bin/
```
3) Further details can be changed in **settings.yaml**, such as MongoDB to read and write to and Neo4js ips, credentials etc. Default values according to the harvester modules have been used

#### Container Parameters
The container needs to have access to the aforementioned data and settings. Mount the needed folders with the -v flag.

**IMPORTANT**: **MAKE SURE THE MOUNTED FOLDERS ARE IN THE SAME PATH AS IN THE LOCAL MACHINE AND SET THE PREVIOUS SETTINGS PARAMETERS ACCORDINGLY**

Moreover, Neo4j and MongoDB should be accessible to the container. If other Docker images are responsible for the databases, they should be available in the bridge network. If not, make them accessible from the localhost using the --net="host" flag.

Example call:
```shell
docker run -it --net="host" -v /path/to/folder/with/SEMREP/and/Metamap:/path/to/folder/with/SEMREP/and/Metamap -v /path/to/folder/with/settings/file:/tmp iasis-literature-analysis
```

When running the above command make sure that:
- the folder containing the **settings.yaml** is mounted to ```:/tmp```
- the parent folder containing both SEMREP and Metamap is mounted in the exact same path in the container

### Tests
Currently no tests supported.
### Questions/Errors
Bougiatiotis Konstantinos, NCSR ‘DEMOKRITOS’ E-mail: bogas.ko@gmail.com
