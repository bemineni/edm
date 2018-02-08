
import os
import sys
import yaml
import traceback
import transaction
from eldam.elasticdatamanager import ElasticDataManager

if __name__ == "__main__":

    test_name = "Remove"
    configpath = os.path.abspath('./edm.yml') if os.path.exists('./edm.yml') else sys.exit(1)

    config = None
    with open(configpath, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as e:
            raise Exception from e

    ret = 0
    #  print(config)
    try:
        edm = ElasticDataManager()
        edm.connect(config, config['default_index'])
        #  result = edm.connection.get(index=config['default_index'],
        #                           doc_type='group'
        #                           id=2)
        #  print(result)
        edm.add({'_index': 'group',
                 '_type': 'doc',
                 '_id': '2',
                 '_source': {"gid": 234,
                             "owner": "bemineni",
                             "name": "Sammy",
                             "grp_hash": "456678",
                             "description": "Sammy group"
                             }
                 })

        edm.remove({'_index': 'group',
                    '_type': 'doc',
                    '_id': '2'})

        # check for the existence of this document then remove
        edm.remove({'_index': 'group',
                    '_type': 'doc',
                    '_id': '3'},
                   True)

        transaction.commit()
        try:
            data = edm.connection.get(index='group', doc_type="doc", id="2")
            if '_source' in data:
                raise Exception("Remove id 2 failed")

        except Exception as e:
            # not found, the item got deleted
            # that is what we are looking for.
            print("Test passed")

    except Exception as e:
        print("Failed to remove item")
        print("Test failed")
        traceback.print_exc()
        ret = 1
    finally:
        print(test_name + " Test complete")

    sys.exit(ret)
