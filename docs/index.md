
Elasticsearch Data manager
==========================

Elasticserach data manager (ELDAM) with zope transaction support. Other transaction data manager like sqlalchemy
use the database atomic operation feature to roll back if an error occurs during the commit process. This is not
achievable in elastic search. To overcome this eldam finalizes the records in the commit call of the two-phase transaction process. At the same time takes backup of the existing data in the index, if it involves removing or updating a record.