from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from asbool import asbool

from lib.logger import logger
from lib import s3
from tasks.job_auditor import JobAuditor
from models.clustered_text import ClusteredText
from resources.resource import Resource


class TextMapResult(Resource):
    def get(self, sequence_id):
        """
        Return the status of a job        
        
        export SEQ_ID=$(cat _temp.txt) && \
        curl \
            -X GET \
            "$(minikube service mapping-service --url)/textmap/sequence_id/$SEQ_ID?include_clustering=false" \
            | python -m json.tool
        """
        data = request.args.to_dict()
        include_clustering = asbool(data.get('include_clustering'))

        ordered_tasks = JobAuditor.get_job_details(sequence_id)
        res = []
        for task in ordered_tasks:
            res.append(
                {
                    'task': task['description'],
                    'progress': task['progress'],
                    'events': task['events'],  # A list of event messages (strings)
                }
            )

        clustering_s3_url = None
        if include_clustering:
            clustering_s3_url = s3.get_s3_url_if_exist(sequence_id)

        return {
            'status': res,
            'clustering_data_url': clustering_s3_url
        }, 200

    def put(self):
        """
        Updates the status of a job
        """
        pass
