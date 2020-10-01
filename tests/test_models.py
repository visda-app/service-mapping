import unittest
from uuid import uuid4
import time

from models.text import (
    RawText,
    TextEmbedding,
    session
)
from models.job import (
    Job,
    JobStatus
)
from lib.logger import logger
from models.db import create_all_tables


logger.info('Creating tables...')
create_all_tables()


class TestTextModel(unittest.TestCase):
    def setUp(self):
        self.uuid1 = str(uuid4())
        self.uuid2 = str(uuid4())
        self.sequence_id = str(uuid4())
        RawText(
            uuid=self.uuid1, text='some text', sequence_id=self.sequence_id,
        ).save_to_db()
        RawText(
            uuid=self.uuid2, text='some other text', sequence_id=self.sequence_id,
        ).save_to_db()

    def tearDown(self):
        # Delete users
        session.query(TextEmbedding).delete()

        session.query(RawText).filter(
            RawText.uuid.in_([self.uuid1, self.uuid2])
        ).delete(synchronize_session=False)

    def test_raw_text_save_to_db(self):
        # Create a record in DB:
        uuid1 = str(uuid4())
        sequence_id = str(uuid4())
        RawText(
            uuid=uuid1,
            text='some random text',
            sequence_id=sequence_id
        ).save_to_db()
        # Query the created record:
        q = session.query(RawText).filter(
            RawText.uuid == uuid1
        )
        # Check if the record is in DB
        assert len(q.all()) == 1
        # Delete record
        q.delete()
        # Check if deleted successfully
        assert len(q.all()) == 0

    def test_text_embedding_save_to_db(self):
        # Should create a raw text to satisfy the foreign key constraint
        TextEmbedding(
            uuid=self.uuid1,
            embedding=[1.2, 3, 0.91, 5.0]
        ).save_to_db()
        # Query the created record:
        q = session.query(TextEmbedding).filter(
            TextEmbedding.uuid == self.uuid1
        )
        # Check if the record is in DB
        assert len(q.all()) == 1
        # Delete records
        q.delete()
        # Check if deleted successfully
        assert len(q.all()) == 0

    def test_text_embedding_save_to_db_type(self):
        # Create a record in DB:
        uuid = str(uuid4())
        with self.assertRaises(ValueError) as e:
            TextEmbedding(
                uuid=uuid,
                embedding='[1.2, 3 0.91, 5.0]'
            ).save_to_db()
        with self.assertRaises(ValueError) as e:
            TextEmbedding(
                uuid=uuid,
                embedding='3'
            ).save_to_db()
        # Query the created record:
        q = session.query(TextEmbedding).filter(
            TextEmbedding.uuid == uuid
        )
        # Check if the record is in DB
        assert len(q.all()) == 0

    def test_text_embedding_get_count_by_sequence_id(self):
        """
        Test TextEmbedding model to have the right count by sequence_id
        """
        TextEmbedding(uuid=self.uuid1, embedding=[]).save_to_db()
        assert TextEmbedding.get_count_by_sequence_id(self.sequence_id) == 1
        TextEmbedding(uuid=self.uuid2, embedding=[]).save_to_db()
        assert TextEmbedding.get_count_by_sequence_id(self.sequence_id) == 2

    def test_text_embedding_has_same_or_more_items_than_raw_text(self):
        """
        Check if the TextEmbedding model has same or more items
        than RawText for the same sequence id
        """
        te = TextEmbedding(
            uuid=self.uuid1, embedding=[1.3, 9.0]
        )
        te.save_to_db()
        has_more = te.has_same_or_more_seq_count_than_rawtext()
        assert not has_more

        te = TextEmbedding(
            uuid=self.uuid2, embedding=[1.3, 0.0]
        )
        te.save_to_db()
        has_more = te.has_same_or_more_seq_count_than_rawtext()
        assert has_more

    def test_get_sequence_id(self):
        """
        Test getting sequence id for TextEmbedding model
        """
        te = TextEmbedding(
            uuid=self.uuid1, embedding=[1.3, 9.0]
        )
        te.save_to_db()

        assert te.get_sequence_id() == self.sequence_id


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
