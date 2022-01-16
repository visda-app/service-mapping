from flask_restful import Resource
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from asbool import asbool

from lib.logger import logger
from models.text import (
    load_clustering_from_db,
    get_clustering_count,
    RawText,
    TextEmbedding
)
from models.job import Job as JobModel
from lib.cache import cache_region


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
            payload = ''
            if include_payload:
                payload = load_clustering_from_db(sequence_id)

            status = {
              'total_texts': RawText.get_count_by_sequence_id(sequence_id),
              'vectorized_texts': 'TODO',
                # TextEmbedding.get_count_by_sequence_id(sequence_id),
              'latest_status': JobModel.get_latest_status(sequence_id)
            }

            return {
                'sequence_id': sequence_id,
                'status': status,
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

    def delete(self):
        """
        This API is used to stop a job. This is probalby not the best place, but good for now

        curl -X DELETE \
            $(minikube service mapping-service --url)/job \
            -d '{
                "sequence_id": "a_sequence_id"
            }'
        """
        try:
            data = request.args.to_dict()
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

