from flask import request
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from lib.logger import logger
from lib.cache import cache_region
from resources.resource import Resource


SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Job",
  "description": "A job identifier",
  "type": "object",
  "properties": {
    "sequence_id": {
      "description": "A sequence ID for the job",
      "type": "string"
    },
    "include_payload": {
      "description": "Include payload if True; "
                     "otherwise, just return count. Default: False",
      "type": "boolean"
    }
  },
  "required": ["sequence_id"]
}


class Job(Resource):
    def post(self):
        """
        Create a job entry in the jobs table
        """
        return {'data': 'test post data'}

    def get(self):
        """
        Return the status of a job
        """
        pass

    def put(self):
        """
        Updates the status of a job
        """
        pass

    def delete(self):
        """
        This API is used to stop a job. This is probalby not the best place, but good for now

        export SEQ_ID=$(cat _temp.txt) && \
        curl -X DELETE \
            $(minikube service mapping-service --url)/job \
            -d "{
                \"sequence_id\": \"$SEQ_ID\"
            }"
        """
        try:
            data = json.loads(request.get_data())
            logger.debug(data)
            validate(data, SCHEMA)

            sequence_id = data['sequence_id']

            cache_region.set(sequence_id + '_STOP', True)

            return 200

        except ValidationError as e:
            logger.exception(str(e))
            return {'message': 'Invalid input parameters'}, 400
        except Exception as e:
            logger.exception(str(e))
            return {'message': 'Something went wrong'}, 500

