# Literature Analysis

This container will deploy the literature analysis module. It is supposed to read a collection of documents (from MongoDB), enrich them with biomedical entities and relations found in the text body and save the results, both in MongoDB and Neo4j, populating the knowledge graph.

This does not expose an API service, just runs ones and exits.

## Details of the contained items

 - README.md
 -- Current file
 - medknow
 -- Folder containing the python module that does the job
   - Authentication.py  
   - data_loader.py  
   - **config.py**
       -- **CHANGE PATH TO SETTINGS.YAML IN config.py**
   - data_saver.py   
   - tasks.py
   - data_extractor.py  
   - init.py  
   - utilities.py
 * Dockerfile
 -- Contains details regarding the image.
 * get-pip.py
 -- Get pip to install the required modules.
 * requirements.txt
 -- List of the required modules
 * start.sh
 -- Helper bash script
 * test.py
 -- Helper python script
* **settings.yaml**
 -- Sample settings file that needs to be configured and moved to the correct folder



## Prerequisities
In summary, in order to run this container you'll need the following installed:
    * [Docker](https://docs.docker.com/)
    * [MongoDB](https://www.mongodb.com/)
    * [Neo4j](https://neo4j.com/)
    * [MetaMap](https://metamap.nlm.nih.gov/)
    * [SEMREP](https://semrep.nlm.nih.gov/)
    
This project is based around concept and relation extractions from text using [SEMREP](https://semrep.nlm.nih.gov/) and and [MetaMap](https://metamap.nlm.nih.gov/). Follow, instructions on their website in order to set-up a copy on they deployment server. Make sure that the SemRep and MetaMap root folders are in the same parent folder.

**IMPORTANT**: The container needs access to the folders of these two installed softwares, in order to set-up services and use them for biomedical entity/relation extraction. It is working under the assumption that we can mount the volume containing these folders to the container, alongside the **settings.yaml** in the same parent folder.

### Usage
#### Settings Parameters

To start with, the module needs information regarding connectivity with MongoDB, Neo4j and other details related to the relation extraction task. We provide the needed info through a **settings.yaml** which also contains information regarding paths to the mounted folders. A sample settings file is also provided.

To customize these settings according to any local enviroment one has to pay attention to the following things.

1) First of the installed SemRep and MetaMap root folders should be in the same parent folder containing the **settings.yaml**. The expected structure is:
-- /path/to/needed/folders/
    - SEMREP
    - MetaMap
    - settings.yaml
2) Change the filepath of the settings.yaml file in config.py (Line-13) setting:

    ```python
    settings_filename = '/path/to/needed/folders/settings.yaml'
    ```
3) Change the path to semrep and metamap files in settings.yaml (Lines 55,59):
    ```python
        metamap: /path/to/needed/folders/Metamap/public_mm/bin/
        semrep: /path/to/needed/folders/SEMREP/public_semrep/bin/
    ```
4) Further details can be changed in settings.yaml, such as MongoDB and Neo4js ips, credentials etc.

#### Container Parameters
The container needs to have access to the aforementioned data and settings. Mount the needed folders with the -v flag.

**IMPORTANT**: **MAKE SURE THE MOUNTED FOLDERS ARE IN THE SAME PATH AS IN THE LOCAL MACHINE AND SET THE PREVIOUS SETTINGS PARAMETERS ACCORDINGLY**

Moreover, Neo4j and MongoDB should be accessible to the container. If other Docker images are responsible for the databases, they should be available in the bridge network. If not, make them accessible from the localhost using the --net="host" flag.

Example call:
```shell
docker run -it --net="host" -v /path/to/needed/folders/:/path/to/needed/folders/ iasis-literature-analysis
```
### Tests
Currently no tests supported.
### Questions/Errors
Bougiatiotis Konstantinos, NCSR ‘DEMOKRITOS’ E-mail: bogas.ko@gmail.com
