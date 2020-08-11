from flask import Flask
from flask_restful import Api

from models.db import create_all_tables
from lib.logger import logger
import resources.job


app = Flask(__name__)
api = Api(app)


@app.before_first_request
def create_tables():
    create_all_tables()


api.add_resource(resources.job.Job, '/job')


@app.route('/')
def home():
    logger.debug("We are at the root, ping!")
    return {'status': 200, 'data': 'Hi!'}
