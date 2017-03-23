
import os
import sys
import yaml
import traceback
import transaction
from eldam.elasticdatamanager import ElasticDataManager
from tdm import TestDataManager
#from .tdm import TestDataManager

if __name__ == "__main__":

	test_name = "Remove"
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
		tdmgr = TestDataManager()
		edm = ElasticDataManager()
		edm.connect(config,config['default_index'])
		#result = edm.connection.get(index=config['default_index'],
		#							doc_type='group'
		#							id=2)
		#print(result)
		edm.add({'_type':'group',
				'_id':'3',
				'_source':{ 
							"gid": 334, 
							"owner": "bhanu", 
							"name": "Bhanu", 
							"grp_hash": "908765", 
							"description": "Bhanu group"
							}
				})
		edm.remove({'_type':'group',
				'_id':'1'})
		transaction.commit()
	except Exception as e:
		print("Failed to remove item")
		print("Test failed")
		traceback.print_exc()
		ret = 1
	finally:
		print(test_name + " Test complete")

	sys.exit(ret)



