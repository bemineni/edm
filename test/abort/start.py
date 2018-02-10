
import os
import sys
import yaml
import traceback
import transaction
import json
from eldam.elasticdatamanager import ElasticDataManager
from tdm import TestDataManager
# from .tdm import TestDataManager

if __name__ == "__main__":

    test_name = "Abort"
    configpath = os.path.abspath('./edm.yml') if os.path.exists('./edm.yml') else sys.exit(1)

    config = None
    with open(configpath, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as e:
            raise Exception from e

    ret = 0
    # print(config)
    try:
        tdmgr = TestDataManager()
        edm = ElasticDataManager()
        edm.connect(config, config['default_index'])
        data = [{'_type': 'group',
                 '_id': 'g1',
                 '_source': {"gid": 234,
                             "owner": "bemineni",
                             "name": "Sammy",
                             "grp_hash": "456678",
                             "description": "Sammy group"
                             }
                 },
                {'_type': 'group',
                 '_id': 'g2',
                 '_source': {"gid": 456,
                             "owner": "bemineni",
                             "name": "Srikanth",
                             "grp_hash": "456678",
                             "description": "Srikanth group"
                             }
                 },
                {'_type': 'group',
                '_id': 'g3',
                 '_source': {"gid": 789,
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
                edm.connection.create(index=config['default_index'],
                                      doc_type="group",
                                      id=thing['_id'],
                                      body=thing['_source']
                                      )
        # result = edm.connection.get(index=config['default_index'],
        #                             doc_type='group'
        #                             id=2)
        # print(result)
        edm.add({'_type': 'group',
                 '_id': 'g4',
                 '_source': {"gid": 334,
                             "owner": "bhanu",
                             "name": "Bhanu",
                             "grp_hash": "908765",
                             "description": "Bhanu group"
                             }
                 })
        edm.remove({'_type': 'group',
                    '_id': 'g1'})

        item = {}
        item['_query'] = {"wildcard": {"_uid": "g*"}}

        item['_script'] = {"inline": "ctx._source.description = params.description;ctx._source.name = params.name",
                           "params": {"description": "Eldam abort",
                                      "name": "eldam"
                                      },
                           "lang": "painless"
                           }
        item['_type'] = 'group'

        edm.update_by_query(item)

        transaction.commit()

    except Exception as e:
        print("Test failed")
        traceback.print_exc()
    finally:
        edm.connection.indices.refresh(index="_all")
        # Lets check if all the data is back

        search = edm.connection.search(index=config['default_index'],
                                       doc_type="group",
                                       body={'query': item['_query']},
                                       _source=True)

        print(json.dumps(search, sort_keys=True, indent=4))
        set_to_check = {"g1": False,
                        "g2": False,
                        "g3": False,
                        "g4": False}

        for thing in search['hits']['hits']:
            if thing['_id'] in set_to_check:
                if (thing['_source']['description'] != "Eldam abort" and
                        thing['_source']['name'] != "eldam" and thing['_id'] != "g4"):
                    set_to_check[thing['_id']] = True

                if (thing['_id'] == "g4"):
                    set_to_check[thing['_id']] = True

        for (key, value) in set_to_check:
            if ((key == "g4" and value) or
                    (not value)):
                ret = 1

        if(edm.connection.exists(index=config['default_index'],
                                 doc_type="group",
                                 id="g4")):
            edm.connection.delete(index=config['default_index'],
                                  doc_type="group",
                                  id="g4")

        for thing in data:
            if(edm.connection.exists(index=config['default_index'],
                                     doc_type="group",
                                     id=thing['_id'])):
                edm.connection.delete(index=config['default_index'],
                                      doc_type="group",
                                      id=thing['_id'])

        if ret == 1:
            print("Test failed")
        else:
            print("Test passed")

        print(test_name + " Test complete")

    sys.exit(ret)
