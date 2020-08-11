from flask_restful import Resource, reqparse
import models.job.Job


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
