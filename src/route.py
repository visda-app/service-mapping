from flask import Flask, request
from flask_restful import Api

from models.db import create_all_tables
from lib.logger import logger
from resources.job import Job


app = Flask(__name__)
api = Api(app)


@app.before_first_request
def create_tables():
    create_all_tables()


api.add_resource(Job, '/job')


@app.route('/status')
def status():
    logger.debug("We are at the /status, ping!")
    params = request.args.to_dict()
    return {'status': 200, 'data': params}
