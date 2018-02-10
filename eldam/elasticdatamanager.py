#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *********************************************
#                 OM Ganesha
# *********************************************
"""elasticdatamanager.py view.


"""


import transaction
import logging
import json
from transaction.interfaces import ISavepointDataManager, IDataManagerSavepoint
from zope.interface import implementer
from elasticsearch import Elasticsearch, NotFoundError


class ElasticSearchException(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg):
        self.msg = msg


class ElasticSearchParamMissingError(ElasticSearchException):
    """Missing input param in the input"""
    def __init__(self, msg):
        super().__init__(msg)


class ElasticSearchSourceError(ElasticSearchException):
    """Missing input source in the input"""
    def __init__(self, msg):
        super().__init__(msg)


@implementer(ISavepointDataManager)
class ElasticDataManager(object):
    """
        This is the order
        abort - If needed. If any previous datamangers aborted. This before
                even begining this datamanager process.

        tpc_begin - Prepare for the transaction
        commit - This is like dry commit. Check for potential errors before commiting
        tpc_vote - After commit vote and tell the transacation manager , that I am
                    fine to go or not
        tpc_finish - Final commit, no turning back after this.


        tpc_abort - If this manager voted no, then this function will
                     be called for cleanup

    """

    transaction_manager = transaction.manager

    def __init__(self):
        self._resources = []
        self.current = 0
        self._connection = None

    def connect(self, settings, default_index="", auto_create_index=False):
        """
            Establish a elastic search connection
        """
        eshosts = settings['elasticsearch_hosts']
        self._connection = Elasticsearch(eshosts,
                                         # sniff before doing anything
                                         sniff_on_start=True,
                                         # refresh nodes after a node fails to respond
                                         sniff_on_connection_fail=True,
                                         # and also every 60 seconds
                                         sniffer_timeout=60,
                                         # request timeout
                                         timeout=30)
        self.default_index = default_index
        # applicable for 6.0
        self.auto_create_index = auto_create_index
        self.versions = self._getVersion()
        self.isVersion6 = self._isVersion6_in_cluster()

    @property
    def connection(self):
        """
            property get existing established elastic search connection
        """
        return self._connection

    def get_connection(self):
        return self._connection

    def refresh(self, index="_all"):
        self._connection.indices.refresh(index)

    def add(self, item):
        """
            Add document to the elasticsearch index.
            Required in the item dictionary
                _id = ID for the to be saved document
                _type = Type of the document
                _source = Source/body to be saved
                _index(optional) = If default_index is set, then this is optional
            This will be committed during the transaction process.
        """
        log = logging.getLogger(__name__)
        log.info("Adding elasticsearch item")
        if (len(self._resources) == 0):
            log.info("Joining transaction")
            self.transaction_manager.get().join(self)

        item['_op'] = "add"
        item['processed'] = False
        item['_index'] = self._get_index(item)
        item['index_created'] = False
        self._check_type(item)
        self._check_id(item)

        self._resources.append(item)

    def remove(self, item, check_existence=False):
        """
            Remove document from elasticsearch index
            Required in the item dictionary
                _id = ID for the to be saved document
                _type = Type of the document
                _index(optional) = If default_index is set, then this is optional
            This will be committed during the transaction process.
        """
        log = logging.getLogger(__name__)
        log.info("Removing elasticsearch item")

        item['_op'] = "remove"
        item['processed'] = False
        item['_index'] = self._get_index(item)
        item['index_created'] = False
        self._check_type(item)
        self._check_id(item)

        if check_existence and not self._check_if_exists(item):
            return

        if (len(self._resources) == 0):
            log.info("Joining transaction")
            self.transaction_manager.get().join(self)

        self._resources.append(item)

    def update(self, item, check_existence=False):
        """
            Update document already present in the elasticsearch index.
            Required in the item dictionary
                _id = ID for the to be saved document
                _type = Type of the document
                _index(optional) = If default_index is set, then this is optional
                _source = partial or full source to be updated.
            This will be committed during the transaction process. If the document
            isn't already present in the index, then this will be converted to an add
            request.
        """
        log = logging.getLogger(__name__)
        log.info("Update elasticsearch item")

        item['_op'] = "update"
        item['processed'] = False
        item['_index'] = self._get_index(item)
        item['index_created'] = False
        self._check_type(item)
        self._check_id(item)

        if '_source' not in item:
            raise ElasticSearchParamMissingError("_source data to update missing")

        if check_existence and not self._check_if_exists(item):
            return

        if (len(self._resources) == 0):
            log.info("Joining transaction")
            self.transaction_manager.get().join(self)

        self._resources.append(item)

    def update_by_query(self, item):
        """
            Update document already present in the elasticsearch index.
            Required in the item dictionary
                _id = ID for the to be saved document
                _type = Type of the document
                _index(optional) = If default_index is set, then this is optional
                _query = Query DSL to update all the documents matching the query
                _source = partial or full source to be updated.
            This will be committed during the transaction process. If the document
            isn't already present in the index, then this will be converted to an add
            request.
        """
        log = logging.getLogger(__name__)
        log.info("Update elasticsearch item")
        if (len(self._resources) == 0):
            log.info("Joining transaction")
            self.transaction_manager.get().join(self)

        if '_query' not in item:
            raise ElasticSearchParamMissingError("_query input missing")

        if '_script' not in item:
            raise ElasticSearchParamMissingError("_script data to update missing")

        item['_op'] = "update_by_query"
        item['processed'] = False
        item['_index'] = self._get_index(item)
        item['index_created'] = False
        self._check_type(item)

        self._resources.append(item)

    def delete_by_query(self, item):
        """
            Update document already present in the elasticsearch index.
            Required in the item dictionary
                _id = ID for the to be saved document
                _type = Type of the document
                _index(optional) = If default_index is set, then this is optional
                _query = Query DSL to delete all the documents matching the query
            This will be committed during the transaction process. If the document
            isn't already present in the index, then this will be converted to an add
            request.
        """
        log = logging.getLogger(__name__)
        log.info("Update elasticsearch item")
        if (len(self._resources) == 0):
            log.info("Joining transaction")
            self.transaction_manager.get().join(self)

        if '_query' not in item:
            raise ElasticSearchParamMissingError("_query input missing")

        item['_op'] = "delete_by_query"
        item['processed'] = False
        item['_index'] = self._get_index(item)
        item['index_created'] = False
        self._check_type(item)

        self._resources.append(item)

    def _getVersion(self):
        data = self._connection.cluster.stats()
        if 'nodes' in data and 'versions' in data['nodes']:
            return data['nodes']['versions']
        return []

    def _isVersion6_in_cluster(self):
        for version in self.versions:
            split_version = version.split('.')
            if len(split_version) > 0 and split_version[0] == '6':
                return True
        return False

    def _check_if_exists(self, request):
        try:
            result = self._connection.get_source(index=request['_index'],
                                                 doc_type=request['_type'],
                                                 id=request['_id'])
            print(result)
        except NotFoundError as e:
            return False

        return True

    def _get_index(self, item):

        if ('_index' not in item and len(self.default_index) == 0):
            raise ElasticSearchParamMissingError("_index input missing and default index is not set")

        return item['_index'] if '_index' in item else self.default_index

    def _check_type(self, item):

        if '_type' not in item:
            raise ElasticSearchParamMissingError("_type input missing")

        if self.isVersion6 and item['_type'] != 'doc':
            raise ElasticSearchException("custom _type not supported in 6.x. _type should by default be 'doc'")

    def _check_id(self, item):

        if '_id' not in item:
            raise ElasticSearchParamMissingError("_id input missing")

    def _refresh_if_needed(self, last_operation, currentoperation, unique_indices):
        """
            This function updates the in-memory buffer to a segment so that
            we can search and update the records immediately after creation
            https://www.elastic.co/guide/en/elasticsearch/guide/current/near-real-time.html
        """
        if last_operation == currentoperation or last_operation == "":
            return last_operation, unique_indices
        else:
            self._connection.indices.refresh(list(unique_indices))
            unique_indices.clear()
            return currentoperation, unique_indices

    def _checkAndCreateIndex(self, item):
        if not self._connection.indices.exists(item['_index'], ignore=[400, 404]):
            # index doesn't exist
            self._connection.indices.create(index=item['_index'], ignore=[400])
            return True

        return False

    @property
    def savepoint(self):
        """
            Savepoints are only supported when all connections support subtransactions
        """
        return ElasticSavepoint(self)

    def abort(self, transaction):
        """
            Outside of the two-phase commit proper, a transaction can be
            aborted before the commit is even attempted, in case we come across
            some error condition that makes it impossible to commit. The abort
            method is used for aborting a transaction and forgetting all changes, as
            well as end the participation of a data manager in the current transaction.
        """
        log = logging.getLogger(__name__)
        log.info("abort")
        self.uncommitted = {'add': [], 'remove': []}

    def tpc_begin(self, transaction):
        """
            The tpc_begin method is called at the start of the commit to perform any
            necessary steps for saving the data.
        """
        log = logging.getLogger(__name__)
        log.info("tpc_begin")

    def commit(self, transaction):
        """
            We record and backup existing data and then perform the operation.
            if any of the other transaction managers vote to back up, then we recommit
            all the data backed up during this commit process.
        """

        # ## This is the step where data managers need to prepare to save the changes
        # ## and make sure that any conflicts or errors that could occur during the
        # ## save operation are handled. Changes should be ready but not made
        # ## permanent, because the transaction could still be aborted if other
        # ## transaction managers are not able to commit.

        log = logging.getLogger(__name__)
        log.info(__name__)
        log.info("commit")
        unique_indices = set()
        last_operation = ""
        # Lets commit and keep track of the items that are commited. In case we get
        # an abort request then remove those items.
        for item in self._resources:

            last_operation, unique_indices = self._refresh_if_needed(last_operation,
                                                                     item['_op'],
                                                                     unique_indices)

            unique_indices.add(item['_index'])

            if item['_op'] == 'add':
                # if version 6, there is no support for types
                # All documents get into their own index
                if self.isVersion6:
                    item['index_created'] = self._checkAndCreateIndex(item)

                self._connection.create(index=item['_index'],
                                        doc_type=item['_type'],
                                        id=item['_id'],
                                        body=item['_source'])

            elif item['_op'] == 'remove':
                if(self._connection.exists(index=item['_index'],
                                           doc_type=item['_type'],
                                           id=item['_id'])):
                    item['_backup'] = self._connection.get_source(index=item['_index'],
                                                                  doc_type=item['_type'],
                                                                  id=item['_id'])
                    self._connection.delete(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'])
                else:
                    raise ElasticSearchException("Unable to find " + item['_id'] + " in type " +
                                                 item['_type'] + " and in index " + item['_index'])
            elif item['_op'] == "update":  # Update

                if(self._connection.exists(index=item['_index'],
                                           doc_type=item['_type'],
                                           id=item['_id'])):

                    item['_backup'] = self._connection.get_source(index=item['_index'],
                                                                  doc_type=item['_type'],
                                                                  id=item['_id'])
                    # Dont get the source after update
                    self._connection.update(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'],
                                            body={'doc': item['_source']},
                                            _source=False)
                else:
                    # The item was not present in the first place
                    # moving this to add
                    self._connection.create(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'],
                                            body=item['_source'])
                    # Move the operation to add. In case of
                    # abort we will only remove the newly created
                    # document
                    item['_op'] = 'add'
            elif item['_op'] == "update_by_query":

                # get all the fields provided by the user to update
                # keys = list(item['_source'].keys())

                item['_backup'] = self._connection.search(index=item['_index'],
                                                          doc_type=item['_type'],
                                                          body={"query": item['_query']},
                                                          _source=True)

                # print(json.dumps(item['_backup'],sort_keys=True,indent=4))

                # example script
                #   "script":{
                #           "inline":"ctx._source.description = params.description;ctx._source.grp_hash = grp_hash",
                #           "params" : {
                #                    "description" : "Srikanth group",
                #                    "grp_hash" : "3433"
                #                       }
                #           }

                toupdate = {"script": item['_script'],
                            "query": item['_query'],
                            }
                # print(json.dumps(toupdate,sort_keys=True,indent=4))

                self._connection.update_by_query(index=item['_index'],
                                                 doc_type=item['_type'],
                                                 body=toupdate,
                                                 _source=True)

                # print(json.dumps(t, sort_keys=True, indent=4))

            elif item['_op'] == "delete_by_query":

                # get all the fields provided by the user to update

                item['_backup'] = self._connection.search(index=item['_index'],
                                                          doc_type=item['_type'],
                                                          body={"query": item['_query']},
                                                          _source=True)

                self._connection.delete_by_query(index=item['_index'],
                                                 doc_type=item['_type'],
                                                 body={"query": item['_query']})
            item['processed'] = True

    def tpc_vote(self, transaction):
        """
            The last chance for a data manager to make sure that the data can
            be saved is the vote. The way to vote ‘no’ is to raise an exception here.
        """
        log = logging.getLogger(__name__)
        log.info("tpc_vote")

    def tpc_finish(self, transaction):
        """
            This method is only called if the manager voted ‘yes’ (no exceptions raised)
            during the voting step. This makes the changes permanent and should never
            fail. Any errors here could leave the database in an inconsistent state. In
            other words, only do things here that are guaranteed to work or you may have
            a serious error in your hands.
        """
        # Do the operation to add it to elastic search
        # We are done lets cleanup
        self._resources = []
        # Lets refresh all indices once
        self.refresh()
        log = logging.getLogger(__name__)
        log.info("tcp_finish")

    def tpc_abort(self, transaction):
        """
            This method is only called if the manager voted ‘no’ by raising an exception
            during the voting step. It abandons all changes and ends the transaction.
        """
        log = logging.getLogger(__name__)
        log.info("tpc_abort")
        unique_indices = set()
        last_operation = ""
        for item in self._resources:
            last_operation, unique_indices = self._refresh_if_needed(last_operation,
                                                                     item['_op'],
                                                                     unique_indices)

            unique_indices.add(item['_index'])

            if item['processed']:
                if item['_op'] == 'add':

                    self._connection.delete(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'])
                    if self.isVersion6 and item['index_created']:
                        # We created index in the commit phase,
                        # so we need to delete it if we are aborting
                        # the transaction.
                        self._connection.indices.delete(index=item['_index'], ignore=[400, 404])

                elif item['_op'] == 'remove':

                    self._connection.create(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'],
                                            body=item['_backup'])

                elif item['_op'] == "update":  # Update

                    self._connection.update(index=item['_index'],
                                            doc_type=item['_type'],
                                            id=item['_id'],
                                            body=item['_backup'],
                                            _source=False)

                elif item['_op'] == "update_by_query":

                    for thing in item['_backup']['hits']['hits']:
                        # update back with old value only if the document exists.
                        if self._connection.exists(index=item['_index'],
                                                   doc_type=item['_type'],
                                                   id=thing['_id']):

                            self._connection.update(index=item['_index'],
                                                    doc_type=item['_type'],
                                                    id=thing['_id'],
                                                    body={'doc': thing['_source']},
                                                    _source=False)

                elif item['_op'] == "delete_by_query":

                    for thing in item['backup']['hits']['hits']:
                        self._connection.create(index=item['_index'],
                                                doc_type=item['_type'],
                                                id=thing['_id'],
                                                body=thing['_source'])

    def sortKey(self):
        """
            Transaction manager tries to sort all the data manger alphabetically
            If we want our datamanger to commit last, then start with '~'. Here
            we dont care. Assuming
        """
        return 'elasticsearch' + str(id(self))


@implementer(IDataManagerSavepoint)
class ElasticSavepoint(object):

    def __init__(self, dm):
        self.dm = dm
        self.saved_committed = self.dm.uncommitted.copy()

    def rollback(self):
        self.dm.uncommitted = self.saved_committed.copy()
