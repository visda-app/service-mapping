from flask_restful import Resource
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from asbool import asbool

from lib.logger import logger


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Mapping",
    "description": "A mapping job identifier",
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string"
        },
        "youtube_video_id": {
            "description": "",
            "type": "string"
        }
    },
    "required": ["youtube_video_id"]
}


class TextMapResult(Resource):
    def get(self, sequence_id):
        """
        Return the status of a job
        """
        data = request.args.to_dict()
        data['include_payload'] = asbool(data.get('include_payload'))
        logger.debug(data)
        validate(data, SCHEMA)

        sequence_id = data['sequence_id']
        include_payload = data.get('include_payload')
        payload = ''

        try:
            return {
                'sequence_id': '',
                'status': '',
                'data': '',
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
