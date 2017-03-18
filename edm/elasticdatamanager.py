#!/usr/bin/env python
# -*- coding: utf-8 -*-
#*********************************************
#                 OM Ganesha          
#*********************************************
"""elasticdatamanager.py view.


"""

import os
import transaction
import logging
from transaction.interfaces import ISavepointDataManager, IDataManagerSavepoint
from zope.interface import implementer
from elasticsearch import Elasticsearch

class ElasticSearchException(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self,msg):
		self.msg = msg

class ElasticSearchParamMissingError(ElasticSearchException):
    """Missing input param in the input"""
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

	def connect(self,settings,default_index = ""):
		eshosts = settings['elasticsearch_hosts']
		self._connection = Elasticsearch( eshosts,
						# sniff before doing anything 
						sniff_on_start=True,
						# refresh nodes after a node fails to respond
						sniff_on_connection_fail=True,
						# and also every 60 seconds
						sniffer_timeout=60)
		self.default_index = default_index

	@property
	def connection(self):
		return self._connection


	def get_connection(self):
		return self._connection

	def add(self,item):
		log = logging.getLogger(__name__)
		log.info("Adding elasticsearch item")
		if ( len(self._resources) == 0):
			log.info("Joining transaction")
			self.transaction_manager.get().join(self)

		item['_op'] = "add"
		item['processed'] = False
		item['_index'] = self.get_index(item)
		self.check_type(item)
		self.check_id(item)

		self._resources.append(item)

	def remove(self,item):
		log = logging.getLogger(__name__)
		log.info("Removing elasticsearch item")
		if ( len(self._resources) == 0):
			log.info("Joining transaction")
			self.transaction_manager.get().join(self)

		item['_op'] = "remove"
		item['processed'] = False
		item['_index'] = self.get_index(item)
		self.check_type(item)
		self.check_id(item)

		self._resources.append(item)

	def update(self,item):
		log = logging.getLogger(__name__)
		log.info("Update elasticsearch item")
		if ( len(self._resources) == 0):
			log.info("Joining transaction")
			self.transaction_manager.get().join(self)

		item['_op'] = "update"
		item['processed'] = False
		item['_index'] = self.get_index(item)
		self.check_type(item)
		self.check_id(item)

		self._resources.append(item)

	def get_index(self,item):

		if ('_index' not in item and
			len(self.default_index) == 0):
			raise ElasticSearchParamMissingError("_index input missing and default index is not set")

		return  item['_index'] if '_index' in item else self.default_index

	def check_type(self,item):

		if '_type' not in item:
			raise ElastiSearchParamMissingError("_type input missing")


	def check_id(self,item):

		if '_id' not in item:
			raise ElastiSearchParamMissingError("_type input missing")			

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
		self.uncommitted = {'add':[], 'remove':[]}
		

	def tpc_begin(self, transaction):
		"""
			The tpc_begin method is called at the start of the commit to perform any 
			necessary steps for saving the data.
		"""
		log = logging.getLogger(__name__)
		log.info("tpc_begin")

	def commit(self, transaction):
		"""
			This is the step where data managers need to prepare to save the changes 
			and make sure that any conflicts or errors that could occur during the 
			save operation are handled. Changes should be ready but not made 
			permanent, because the transaction could still be aborted if other 
			transaction managers are not able to commit.
		"""
		log = logging.getLogger(__name__)
		log.info("commit")
		# Lets commnit and keep track of the items that are commited. In case we get 
		# an abort request then remove those items.
		for item in self._resources:
			if item['_op'] == 'add':
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
					raise ElasticSearchException("Unable to find " + item['_id'] +" in type " +
												   item['_type']+" and in index " + item['_index'])
			else: # Update
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
											body=item['_source'],
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
		#Do the operation to add it to elastic search
		log = logging.getLogger(__name__)
		log.info("tcp_finish")

	def tpc_abort(self, transaction):
		""" 
			This method is only called if the manager voted ‘no’ by raising an exception 
			during the voting step. It abandons all changes and ends the transaction.
		"""
		log = logging.getLogger(__name__)
		log.info("tpc_abort")
		for item in self._resources:
			if item['processed']:
				if item['_op'] == 'add':
					self._connection.delete(index=item['_index'],
											doc_type=item['_type'],
											id=item['_id'])
					print("Removing item")
				elif item['_op'] == 'remove':
					self._connection.create(index=item['_index'],
											doc_type=item['_type'],
											id=item['_id'],
											body=item['_backup'])
					print("Adding item back")
				else: # Update
					self._connection.update(index=item['_index'],
											doc_type=item['_type'],
											id=item['_id'],
											body=item['_backup'],
											_source=False)
					print("Updating back to old value")


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


