from flask_restful import Resource
from flask import request
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from asbool import asbool

from lib.logger import logger
from tasks.job_auditor import JobAuditor
from models.clustered_text import ClusteredText


class TextMapResult(Resource):
    def get(self, sequence_id):
        """
        Return the status of a job
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
                }
            )

        if include_clustering:
            clustering = ClusteredText.get_last_by_sequence_id(sequence_id)

        return {
            'status': res,
            'data': clustering
        }, 200

    def put(self):
        """
        Updates the status of a job
        """
        pass
