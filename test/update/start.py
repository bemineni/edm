
import os
import sys
import yaml
import traceback
import transaction
import json
from eldam.elasticdatamanager import ElasticDataManager

["16.83.62.232:9200","16.83.63.114:9200"],"test"

if __name__ == "__main__":

	test_name = "Update"
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
		edm.connection.create(index=config['default_index'],doc_type='group',id='g100',body={ 
							"gid": 234, 
							"owner": "bemineni", 
							"name": "Sammy", 
							"grp_hash": "456678", 
							"description": "Sammy group"
							})
		edm.update({'_type':"group",'_id':'g100','_source':{'grp_hash':'12345','name':"Srikanth"}})

		transaction.commit()
		
		data = edm.connection.get_source(index=config['default_index'],doc_type="group",id='g100')
		if(data['grp_hash'] != "12345" or 
			data['name'] != "Srikanth"):
			raise Exception("Unable to add/update item")
		else:
			print(json.dumps(data,indent=4,sort_keys=True))
			print("Test passed")
		
	except Exception as e:
		print("Failed to add item")
		print("Test failed")
		traceback.print_exc()
		ret = 1
	finally:
		print(test_name + " Test complete")
		edm.connection.delete(index=config['default_index'],doc_type="group",id="g100")

	sys.exit(ret)



