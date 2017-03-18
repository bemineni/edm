
import os
import sys
import yaml
import traceback
from edm.elasticdatamanager import ElasticDataManager

if __name__ == "__main__":

	test_name = "Connect"
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
		print(edm.connection.cluster.health())
	except Exception as e:
		print("Failed to connect")
		traceback.print_exc()
		ret = 1
	finally:
		print(test_name + " Test complete")

	sys.exit(ret)



