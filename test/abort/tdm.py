#!/usr/bin/env python
# -*- coding: utf-8 -*-
#*********************************************
#                 OM Ganesha          
#*********************************************
"""elasticsearch.py view.


"""

import os
import transaction
import logging
from transaction.interfaces import ISavepointDataManager, IDataManagerSavepoint
from zope.interface import implementer
from elasticsearch import Elasticsearch


class IamNotOkVote(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self,msg):
		self.msg = msg  

@implementer(ISavepointDataManager)
class TestDataManager(object):
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
		self.transaction_manager.get().join(self)
		

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


	def tpc_vote(self, transaction):
		"""
			The last chance for a data manager to make sure that the data can 
			be saved is the vote. The way to vote ‘no’ is to raise an exception here.
		"""
		log = logging.getLogger(__name__)
		log.info("tpc_vote")
		# Raise a no vote
		raise IamNotOkVote("Test I am not ok vote")

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
		


	def sortKey(self):
		""" 
			Transaction manager tries to sort all the data manger alphabetically 
			If we want our datamanger to commit last, then start with '~'. Here
			we dont care. Assuming 
		"""
		# Should start with T to be committed after elastic data manager
		return 'testdatamanger' + str(id(self))
		

@implementer(IDataManagerSavepoint)
class TestSavepoint(object):

	def __init__(self, dm):
		self.dm = dm 
		self.saved_committed = self.dm.uncommitted.copy()

	def rollback(self):
		self.dm.uncommitted = self.saved_committed.copy()


