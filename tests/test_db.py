import unittest
from uuid import uuid4

from src.models.text import (
    RawText,
    session
)
from src.models.job import (
    Job,
    JobStatus
)
from src.lib.logger import logger
from src.models.db import engine, Base


logger.info('Creating tables...')
Base.metadata.create_all(engine)


class TestTextModel(unittest.TestCase):
    def test_save_raw_text_to_db(self):
        # Create a record in DB:
        uuid = str(uuid4())
        sequence_id = str(uuid4())
        RawText(
            uuid=uuid,
            text='some random text',
            sequence_id=sequence_id
        ).save_to_db()
        # Query the created record:
        q = session.query(RawText).filter(
            RawText.uuid == uuid
        )
        # Check if the record is in DB
        assert len(q.all()) == 1
        # Delete record
        q.delete()
        # Check if deleted successfully
        assert len(q.all()) == 0


class TestJobModel(unittest.TestCase):
    def test_create_job(self):
        """
        Test creating a job entry in the table
        """
        uuid = str(uuid4())
        Job(
            job_id=uuid,
            subtask_count=20,
            status=JobStatus.created
        ).save_to_db()

        q = session.query(Job).filter(
            Job.job_id == uuid
        )
        assert len(q.all()) == 1

        assert q.first().status.value == 'created'

        q.delete()
        assert len(q.all()) == 0
