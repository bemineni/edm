Elasticsearch Data manager
==========================

Elasticserach data manager (ELDAM) with zope transaction support. Other transaction data manager like sqlalchemy
use the database atomic operation feature to roll back if an error occurs during the commit process. This is not
achievable in elastic search. To overcome this eldam finalizes the records in the commit call of the two-phase transaction process. At the same time takes backup of the existing data in the index, if it involves removing or updating a record.

**Some requirements kept in mind while designing this library**
---------------------------------------------------------------

* This module is not atomic. If any of the other transactions fail, then there is a brief period where the data still resides in Elasticsearch and will be removed during the `tcp_abort` call.
* **Please use it with your discretion if Elasticsearch is your primary data store**. This library is perfect if Elasticsearch is used only for searching in your application.

**Transaction process**
------------------------

`abort` - If needed, If any of the previous data managers aborted. This is before even beginning this data manager process. Elasticsearch data manager doesn't do anything in this call. Since we haven't committed anything to ElasticSearch

`tpc_abort` - If any of the other manager voted no after elasticsearch data manager has commites, then this function will be called for cleanup

### Two step commit 

* `tpc_begin` - Prepare for the transaction. Elastic search does nothing in this call
* `commit` - Elasticsearch data manager actually commits the data, at the same time takes back of the existing data in case of delete or update. Raises an exception if the any of the commits fail.
* `tpc_vote` - After committing, vote and tell the transaction manager, that I am fine to go or not. Elasticsearch data manager votes yes
* `tpc_finish` - Final commit, no turning back after this. Elasticsearch data manager has already committed the data.

API Documentation
-----------------

### `connect(settings,default_index = "")`

Connect to ElasticSearch database

Parameter 
- settings - Dictionary with elasticsearch connections details
  * 'elasticsearch_hosts' : array of elasticsearch hosts [localhost, localhost:443, 16.74.45.322]
- defualt_index - Default index to store documents. If not specified, then add, remove and update input need to mention the index details.

```python 
from eldam.elasticdatamanger import ElasticDataManager

edm = new ElasticDataManager()
edm.connect(["16.83.62.232:9200","16.83.63.114:9200"],"test")
```

### `connection()`

Is class property to get the established connection.

``` python
from eldam.elasticdatamanger import ElasticDataManager

edm = new ElasticDataManager()
edm.connect(["16.83.62.232:9200","16.83.63.114:9200"],"test")
# you can directly run api's defined from python ElasticSearch 5.0.0 and above
print(edm.connection.cluster.health())
```

### `add(item)`

Add a document to be included into Elasticsearch once the transaction is committed. If this instance of data manager was not added to the transaction manager, then this call will automatically add it to the current transaction.

Parameters

- item - Dictionary of the document to be added 
  - '_index' - Index to which this document needs to be included. This is optional if default_index is set during connect.
  - '_type' - Type of the document.
  - '_id' - Id of the document.
  - '_source' - Source of the document.

```python
from eldam.elasticdatamanger import ElasticDataManager


edm = ElasticDataManager()
edm.connect(["16.83.62.232:9200","16.83.63.114:9200"],"test")
edm.add({'_type':'group',
        '_id':'2',
        '_source':{ 
                    "gid": 234, 
                    "owner": "bemineni", 
                    "name": "Sammy", 
                    "grp_hash": "456678", 
                    "description": "Sammy group"
                    }
        })
transaction.commit()
```

### `remove(item)`

Remove an existing document from Elasticsearch once the transaction is committed. If this instance of data manager was not added to the transaction manager, then this call will automatically add it to the current transaction.

Parameters

- item - Dictionary of the document to be added 
  - '_index' - Index to which this document needs to be included. This is optional if default_index is set during connect.
  - '_type' - Type of the document.
  - '_id' - Id of the document.

```python
from eldam.elasticdatamanger import ElasticDataManager


edm = ElasticDataManager()
edm.connect(["16.83.62.232:9200","16.83.63.114:9200"],"test")
edm.remove({'_type':'group',
                '_id':'2'})

# commit the transaction                
transaction.commit()
```

### `update(item)`

Update an existing document from Elasticsearch once the transaction is committed. If the document doesn't exist in the index, then this call will automatically convert to an add call and a new document will be included into ElasticSearch using the `_source` provided in the `item`. If this instance of data manager was not added to the transaction manager, then this call will automatically add it to the current transaction.

Parameters

- item - Dictionary of the document to be added 
  - '_index' - Index to which this document needs to be included. This is optional if default_index is set during connect.
  - '_type' - Type of the document.
  - '_id' - Id of the document.
  - '_source' - Source of the document. Can be partial update attributes of the original document.

```python
from eldam.elasticdatamanger import ElasticDataManager


edm = ElasticDataManager()
edm.connect(["16.83.62.232:9200","16.83.63.114:9200"],"test")
edm.update({'_type':'group',
                '_id':'2',
                '_source':{ 
                            "description": "Sammy study group"
                            }
                })

# commit the transaction                
transaction.commit()
```