import json
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import BadRequest

from lib.logger import logger
from tasks.get_3rd_party_data import Get3rdPartyData
from tasks.find_keywords import FindKeywords
from tasks.await_embedding import AwaitEmbedding
from tasks.cluster_texts import ClusterTexts
from lib.utils import generate_random_id
from lib.cache import cache_region as cache
from resources.resource import Resource
from lib.cache import cache_region, CacheKeys


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Mapping",
    "description": "A mapping job identifier",
    "type": "object",
    "properties": {
        "sequence_id": {
            "type": "string"
        },
        "user_id": {
            "type": "string"
        },
        "limit": {
            "type": "integer",
            "description": "A limit on the number of texts that are allowed to be mapped. Only this limit or slightly higher number of texts would be mapped."
        },
        "source_urls": {
            "description": "The URL of source data such as YouTube or TikTak urls",
            "type": "array",
            "items": {
                "type": "string"
            }
        },
    },
    "additionalProperties": False,
    "required": ["source_urls", "limit", "user_id"]
}


PATCH_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Job",
    "description": "A job identifier",
    "type": "object",
    "properties": {
        "sequence_id": {
            "description": "A sequence ID for the job",
            "type": "string"
        },
    },
    "required": ["sequence_id"]
}



def url_to_get_data_class_mapper(url):
    return Get3rdPartyData


class TextMap(Resource):
    def post(self):
        """
        Example call:

            localhost:5001/textmap \


        curl -X POST \
            $(minikube service mapping-service --url)/textmap \
            -H "Content-Type: application/json"  \
            -d '{
                "source_urls": [
                    "https://www.youtube.com/watch?v=4E29RzEUGrs",
                    "https://www.youtube.com/watch?v=pXswr3XmDw8",
                    "https://www.youtube.com/watch?v=DHjqpvDnNGE"
                ],
                "user_id": "a_user_id",
                "limit": 200
            }' \
            | python -m json.tool \
            | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])" \
            | tee _temp.txt \
        && \
        export SEQ_ID=$(cat _temp.txt) \
        && echo sequence_id=$SEQ_ID \
        """
        # form_data = request.form.to_dict()
        try:
            data = json.loads(request.get_data())
            validate(data, SCHEMA)
        except (ValidationError, json.decoder.JSONDecodeError) as e:
            raise BadRequest(e)

        limit = data['limit']
        if limit is None:
            limit = 2**128
        limit_key = generate_random_id()
        cache.set(limit_key, limit)

        total_num_texts_cache_key = generate_random_id()
        cache.set(total_num_texts_cache_key, 0)

        job_id = data.get('sequence_id')
        if not job_id:
            job_id = generate_random_id()
        
        tasks = []
        for url in data['source_urls']:
            tasks.append(
                url_to_get_data_class_mapper(url)(
                    job_id=job_id,
                    kwargs={
                        'source_url': url,
                        'limit_cache_key': limit_key,
                        'total_num_texts_cache_key': total_num_texts_cache_key,
                    },
                )
            )
        tasks.append(
            AwaitEmbedding(
                job_id=job_id,
                kwargs={
                    'total_num_texts_cache_key': total_num_texts_cache_key,
                },
            )
        )
        tasks.append(
            FindKeywords(
                job_id=job_id,
                kwargs={},
            )
        )
        tasks.append(
            ClusterTexts(
                job_id=job_id, kwargs={
                    'sequence_ids': [job_id],
                }
            )
        )

        task_chain = tasks[0]
        for task in tasks[1:]:
            task_chain = task_chain >> task

        tasks[0].start()

        return {
            'message': f"Job job_id={job_id} submitted.",
            'job_id': job_id,
        }, 200

    def patch(self):
        """
        This is a bit hackey but I use the patch HTTP verb to send
        a stop signal. That is to set a cache key that can be used
        by the jobs to stop

        curl -X PUT \
            $(minikube service mapping-service --url)/textmap \
            -d "{
                \"sequence_id\": \"$SEQ_ID\"
            }"

        """
        try:
            data = json.loads(request.get_data())
            validate(data, PATCH_SCHEMA)

            sequence_id = data['sequence_id']
            cache_region.set(CacheKeys.get_stop_job_key(sequence_id), True)
            logger.debug(
                f"CacheKey={CacheKeys.get_stop_job_key(sequence_id)} set to 'True'"
            )

        except ValidationError as e:
            logger.exception(str(e))
            return {'message': 'Invalid input parameters'}, 400
        except Exception as e:
            logger.exception(str(e))
            return {'message': 'Something went wrong'}, 500

        return {'message': 'Job stopped!'}, 200
