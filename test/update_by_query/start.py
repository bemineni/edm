
import os
import sys
import yaml
import traceback
import transaction
import json
from eldam.elasticdatamanager import ElasticDataManager

if __name__ == "__main__":

	test_name = "Update_by_query"
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


		data = [{'_type':'group',
				'_id':'g2',
				'_source':{ 
							"gid": 234, 
							"owner": "bemineni", 
							"name": "Sammy", 
							"grp_hash": "456678", 
							"description": "Sammy group"
							}
				},
				{'_type':'group',
				'_id':'g3',
				'_source':{ 
							"gid": 456, 
							"owner": "bemineni", 
							"name": "Srikanth", 
							"grp_hash": "456678", 
							"description": "Srikanth group"
							}
				},
 				{'_type':'group',
 				'_id':'g4',
				'_source':{ 
							"gid": 789, 
							"owner": "bemineni", 
							"name": "bangaram", 
							"grp_hash": "456678", 
							"description": "Bangaram group"
							}
				}]

		for thing in data:
			if(not edm.connection.exists(index=config['default_index'],
									doc_type="group",
									id=thing['_id'])):
				edm.add(thing)

		transaction.commit()


		item = {}
		item['_query'] = {
							"wildcard": {
											"_uid": "g*"
										}
						}

		item['_script'] = {
					"inline":"ctx._source.description = params.description;ctx._source.name = params.name",
					"params":{
						"description": "Eldam group",
						"name":"eldam"
					},
					"lang":"painless"
				}
		item['_type'] = 'group'


		edm.update_by_query(item)

		transaction.commit()

		edm.connection.indices.refresh(index="_all")

		search = edm.connection.search(index=config['default_index'],doc_type="group",body={'query':item['_query']},_source=True)

		print(json.dumps(search, sort_keys=True, indent=4))
		
		for things in search['hits']['hits']:
			if (things['_source']['description'] != 'Eldam group' or
				things['_source']['name'] != "eldam"):
				raise Exception("Unable to update the documents")


		transaction.commit()

		
	except Exception as e:
		print("Failed to update items by query")
		print("Test failed")
		traceback.print_exc()
		ret = 1
	finally:

		print("****************Deleting items****************")

		for thing in data:
			if(edm.connection.exists(index=config['default_index'],
		  							doc_type="group",
		  							id=thing['_id'])):
		  		out = edm.connection.delete(index=config['default_index'],doc_type=thing['_type'],id=thing['_id'])
		  		print(json.dumps(out, sort_keys=True, indent=4))

		print(test_name + " Test complete")

	sys.exit(ret)



	