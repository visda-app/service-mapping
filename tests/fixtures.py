import pytest

import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.realpath(__file__)
    ) + '/../web_engine'
)
from route import app as app
from models.db import create_all_tables


@pytest.fixture
def client():
    with app.app_context():
        create_all_tables()

    client = app.test_client()
    yield client

    # with app.app_context():
    #     db.session.remove()
