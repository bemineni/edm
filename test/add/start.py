
import os
import sys
import yaml
import traceback
import transaction
from eldam.elasticdatamanager import ElasticDataManager

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
		edm = ElasticDataManager()
		edm.connect(config,config['default_index'])
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
	except Exception as e:
		print("Failed to add item")
		print("Test failed")
		traceback.print_exc()
		ret = 1
	finally:
		print(test_name + " Test complete")

	sys.exit(ret)



