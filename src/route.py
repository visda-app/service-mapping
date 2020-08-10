from flask import Flask
from flask import send_from_directory
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_log_request_id import RequestID

from configs.app_configs import BaseConfig
from models.db import db
from lib.logger import logger
import resources.user
import resources.restaurant
import resources.review


app = Flask(__name__)
app.config.from_object(BaseConfig)
api = Api(app)
db.init_app(app)
jwt = JWTManager(app)
RequestID(app)


@app.before_first_request
def create_tables():
    db.create_all()


api.add_resource(resources.user.UserRegistration, '/registration')
api.add_resource(resources.user.UserLogin, '/login')
api.add_resource(resources.user.UserLogoutAccess, '/logout/access')
api.add_resource(resources.user.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.user.TokenRefresh, '/token/refresh')
api.add_resource(resources.user.AllUsers, '/users')
api.add_resource(resources.user.SecretResource, '/secret')
api.add_resource(
    resources.restaurant.Restaurants,
    '/restaurants'
)
api.add_resource(
    resources.restaurant.Restaurant,
    '/restaurant/<string:id>'
)
api.add_resource(
    resources.review.Review,
    '/review'
)
api.add_resource(
    resources.review.Reply,
    '/reply'
)


@app.route('/')
def home():
    logger.warning("We are at the root, ping!")
    return send_from_directory('react_build', 'index.html')


@app.route('/favicon.ico')
def favicon():
    logger.debug("Returning the favicon.ico!")

    return send_from_directory('react_build', 'favicon.ico')


@app.route('/static/<file_type>/<filename>')
def get_static_file(file_type, filename):
    logger.debug(f"Returning {file_type} / {filename}...")
    return send_from_directory(
        "react_build/static/" + file_type, filename
    )
