
import os
import sys
import yaml
import traceback
import transaction
import json
from elasticsearch import Elasticsearch


if __name__ == "__main__":

	test_name = "Add"
	configpath = os.path.abspath('./edm.yml') if os.path.exists('./edm.yml') else sys.exit(1)

	config=None
	with open(configpath , 'r') as stream:
		try:
			config = yaml.load(stream)
		except yaml.YAMLError as e:
			raise Exception from e

	ret = 0
	#print(config)
	try:
		connection = Elasticsearch( config['elasticsearch_hosts'],
						# sniff before doing anything 
						sniff_on_start=True,
						# refresh nodes after a node fails to respond
						sniff_on_connection_fail=True,
						# and also every 60 seconds
						sniffer_timeout=60)
		
		

		connection.create(index=config['default_index'],doc_type='group',id='2',
							body={ 
							"gid": 234, 
							"owner": "bemineni", 
							"name": "Sammy", 
							"grp_hash": "456678", 
							"description": "Sammy group"
							})
		data = connection.get_source(index=config['default_index'],doc_type="group",id='2')
		print(json.dumps(data,indent=4,sort_keys=True))

		
	except Exception as e:
		print("Failed to add item")
		print("Test failed")
		traceback.print_exc()
		ret = 1
	finally:
		print(test_name + " Test complete")

	sys.exit(ret)



