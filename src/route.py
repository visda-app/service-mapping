from flask import Flask, request
from flask_restful import Api

from lib.logger import logger
from resources.text_map import TextMap
from resources.text_map_result import TextMapResult
from resources.job import Job
from models.db import create_all_tables


app = Flask(__name__)
api = Api(app)


@app.before_first_request
def create_tables():
    create_all_tables()


api.add_resource(TextMap, '/textmap')
api.add_resource(TextMapResult, '/textmap/sequence_id/<string:sequence_id>')
api.add_resource(Job, '/job')


@app.route('/status')
def status():
    logger.debug("We are at the /status, ping!")
    logger.warning("Warning: We are at the /status, ping!")
    params = request.args.to_dict()
    return {'status': 200, 'data': params}

@app.route('/create_tables')
def create_tables():
    params = request.args.to_dict()
    create_all_tables()

    return {'status': 200, 'data': params}
