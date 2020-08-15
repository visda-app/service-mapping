from flask_restful import Resource
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from asbool import asbool

from lib.logger import logger
from models.text import (
    load_clustering_from_db,
    get_clustering_count
)


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
        try:
            data = request.args.to_dict()
            data['include_payload'] = asbool(data.get('include_payload'))
            logger.debug(data)
            validate(data, SCHEMA)

            sequence_id = data['sequence_id']
            include_payload = data.get('include_payload')
            count = get_clustering_count(sequence_id)
            payload = ''
            if include_payload:
                payload = load_clustering_from_db(sequence_id)

            return {
                'sequence_id': sequence_id,
                'count': count,
                'data': payload
            }, 200
        except ValidationError as e:
            logger.exception(str(e))
            return {'message': 'Invalid input parameters'}, 400
        except Exception as e:
            logger.exception(str(e))
            return {'message': 'Something went wrong'}, 500

    def put(self):
        """
        Updates the status of a job
        """
        pass
