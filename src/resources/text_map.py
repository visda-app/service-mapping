import json
from flask_restful import Resource
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import BadRequest

from lib.logger import logger
from tasks.get_3rd_party_data import Get3rdPartyData
from tasks.await_embedding import AwaitEmbedding
from tasks.cluster_texts import ClusterTexts
from lib.utils import generate_random_job_id



SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Mapping",
    "description": "A mapping job identifier",
    "type": "object",
    "properties": {
        "sequence_id": {
            "type": "string"
        },
        "youtube_video_id": {
            "description": "",
            "type": "string"
        }
    },
    "required": ["youtube_video_id"]
}


class TextMap(Resource):
    def post(self):
        """
        Example call:

        curl -X POST \
            $(minikube service mapping-service --url)/textmap \
            -H "Content-Type: application/json"  \
            -d '{
                "youtube_video_id": "CLiic14t2YQ"
            }' \
            | python -m json.tool \
            | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])" \
            | tee _temp.txt
        export SEQ_ID=$(cat _temp.txt)
        echo sequence_id=$SEQ_ID
        """
        # form_data = request.form.to_dict()
        try:
            data = json.loads(request.get_data())
            validate(data, SCHEMA)
        except (ValidationError, json.decoder.JSONDecodeError) as e:
            raise BadRequest(e)
        youtube_video_id = data['youtube_video_id']
        logger.info(f"Request received for youtube_video_id={youtube_video_id}")

        job_id = data.get('sequence_id')
        if not job_id:
            job_id = generate_random_job_id()

        task_1 = Get3rdPartyData(
            job_id=job_id,
            kwargs={
                'video_id': youtube_video_id
            }
        )
        task_2 = AwaitEmbedding(job_id=job_id)
        task_3 = ClusterTexts(
            job_id=job_id, kwargs={
                'sequence_ids': [job_id]
            }
        )

        task_1 >> task_2 >> task_3

        task_1.start()

        return {
            'message': f"Job job_id={job_id} submitted.",
            'job_id': job_id,
        }, 200

    def put(self):
        """
        Updates the status of a job
        """
        pass