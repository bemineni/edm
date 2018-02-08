import os
import sys
import yaml
import traceback
import transaction
import json
from elasticsearch import Elasticsearch


if __name__ == "__main__":

	ret = 0
	#print(config)
	try:
		connection = Elasticsearch( ['127.0.0.1'],
						# sniff before doing anything 
						sniff_on_start=True,
						# refresh nodes after a node fails to respond
						sniff_on_connection_fail=True,
						# and also every 60 seconds
						sniffer_timeout=60)
		
		

		connection.create(index="eldam",doc_type='group',id='g1',
							body={ 
							"gid": 234, 
							"owner": "bemineni", 
							"name": "Srikanth", 
							"grp_hash": "456678", 
							"description": "Srikanth group"
							})
		connection.create(index="eldam",doc_type='group',id='g2',
							body={ 
							"gid": 456, 
							"owner": "bemineni", 
							"name": "Bangaram", 
							"grp_hash": "456678", 
							"description": "Bangaram group"
							})
		connection.create(index="eldam",doc_type='group',id='g3',
							body={ 
							"gid": 789, 
							"owner": "bemineni", 
							"name": "Sammy",  
							"grp_hash": "456678", 
							"description": "Sammy group"
							})

		connection.indices.refresh(index="_all")
		


		item = {}
		item['query'] = {
							"wildcard": {
											"_uid": {
														"value":"g*"
													}
										}
						}

		print(json.dumps(item,indent=4,sort_keys=True))

		# data = connection.get_source(index="eldam",doc_type="group",id='g1')
		# print(json.dumps(data,indent=4,sort_keys=True))

		# data = connection.get_source(index="eldam",doc_type="group",id='g2')
		# print(json.dumps(data,indent=4,sort_keys=True))

		# data = connection.get_source(index="eldam",doc_type="group",id='g3')
		# print(json.dumps(data,indent=4,sort_keys=True))

		print("*******************Search Data*********************")


		data = connection.search(index="eldam",doc_type="group",body={'query':item['query']},_source=True)
		print(json.dumps(data,indent=4,sort_keys=True))
		
	except Exception as e:
		traceback.print_exc()
		ret = 1

	sys.exit(ret)



