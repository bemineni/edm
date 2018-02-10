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

    config = None
    with open(configpath, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as e:
            raise Exception from e

    ret = 0
    # print(config)
    try:
        connection = Elasticsearch(config['elasticsearch_hosts'],
                                   # sniff before doing anything
                                   sniff_on_start=True,
                                   # refresh nodes after a node fails to respond
                                   sniff_on_connection_fail=True,
                                   # and also every 60 seconds
                                   sniffer_timeout=60)
        item = {}
        item['query'] = {"wildcard": {"_uid": {"value": "g*"}}}

        item['script'] = {"inline": "ctx._source.description = params.description;ctx._source.name = params.name",
                          "lang": "painless",
                          'params': {"description": "eldam group",
                                     "name": "eldam"
                                     }
                          }

        print(json.dumps(item, indent=4, sort_keys=True))

        # data = connection.get_source(index=config['default_index'],doc_type="group",id='g1')
        # print(json.dumps(data,indent=4,sort_keys=True))

        # data = connection.get_source(index=config['default_index'],doc_type="group",id='g2')
        # print(json.dumps(data,indent=4,sort_keys=True))

        # data = connection.get_source(index=config['default_index'],doc_type="group",id='g3')
        # print(json.dumps(data,indent=4,sort_keys=True))

        print("*******************Search Data*********************")

        data = connection.search(index=config['default_index'],
                                 doc_type="group",
                                 body={'query': item['query']}, _source=True)
        print(json.dumps(data, indent=4, sort_keys=True))

        connection.indices.refresh(index="_all")

        output = connection.update_by_query(index=config['default_index'],
                                            doc_type="group",
                                            body=item,
                                            _source=True)

        connection.indices.refresh(index="_all")

        print(json.dumps(output, indent=4, sort_keys=True))

        print("*******************Search Data*********************")

        data = connection.search(index=config['default_index'],
                                 doc_type="group",
                                 body={'query': item['query']},
                                 _source=True)
        print(json.dumps(data, indent=4, sort_keys=True))

    except Exception as e:
        print("Failed to add item")
        print("Test failed")
        traceback.print_exc()
        ret = 1
    finally:
        print(test_name + " Test complete")

    sys.exit(ret)
