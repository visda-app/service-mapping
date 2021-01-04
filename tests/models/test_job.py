import unittest
from uuid import uuid4

from models.text import session
from models.text import Text as TextModel
from models.job import (
    Job,
    JobStatus,
    JobTextRelation,
    TextTaskStatus
)
from lib.logger import logger
from models.db import create_all_tables


logger.info('Creating tables...')
create_all_tables()


class TestJobModel(unittest.TestCase):
    def test_create_job(self):
        """
        Test creating a job entry in the table
        """
        uuid = str(uuid4())
        Job.log_status(uuid, JobStatus.started)

        q = session.query(Job).filter(
            Job.job_id == uuid
        )
        assert len(q.all()) == 1

        assert q.first().status == 'started'

        q.delete()
        assert len(q.all()) == 0

    def test_set_status(self):
        """
        Test creating a job entry in the table
        """
        uuid = str(uuid4())

        ret_status = Job.get_latest_status(uuid)
        assert ret_status is None

        for status in JobStatus:
            Job.log_status(uuid, status)
            ret_status = Job.get_latest_status(uuid)
            assert ret_status == status.name

        ret_status = Job.get_latest_status(uuid)
        assert ret_status == JobStatus.done.name

    def test_set_status_type_check(self):
        """
        Test set_status only accepts the right type of status
        """
        uuid = str(uuid4())

        with self.assertRaises(ValueError) as e:
            Job.log_status(uuid, "A_dummy_status")


class TestJobTextRelation(unittest.TestCase):
    def setUp(self):
        self.text_ids = ['text-001 ', 'text-002 ', 'text-003 ']
        self.db_entries = []
        for text_id in self.text_ids:
            self.db_entries.append(
                JobTextRelation(
                    job_id='111',
                    text_id=text_id,
                ).save_to_db()
            )
            self.db_entries.append(
                TextModel(
                    id=text_id,
                    text=text_id * 2
                ).save_or_update()
            )
        # process one and update the text embedding for that record
        self.db_entries.append(
            TextModel(
                id=self.text_ids[1],
                embedding=[0.1, 0.2, 0.3]
            ).save_or_update()
        )

    def tearDown(self):
        for entry in self.db_entries:
            entry.delete_from_db()

    def test_get_unprocessed_texts_count_by_job_id(self):
        result = JobTextRelation.get_unprocessed_texts_count_by_job_id('111')
        assert result == 2
