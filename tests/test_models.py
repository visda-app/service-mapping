import unittest
from uuid import uuid4

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

    def test_save_text_embedding_to_db(self):
        # Create a record in DB:
        uuid = str(uuid4())
        TextEmbedding(
            uuid=uuid,
            embedding=[1.2, 3, 0.91, 5.0]
        ).save_to_db()
        # Query the created record:
        q = session.query(TextEmbedding).filter(
            TextEmbedding.uuid == uuid
        )
        # Check if the record is in DB
        assert len(q.all()) == 1
        # Delete record
        q.delete()
        # Check if deleted successfully
        assert len(q.all()) == 0

    def test_text_embedding_has_same_or_more_items_than_raw_text(self):
        """
        Check if the TextEmbedding model has same or more items
        than RawText for the same sequence id
        """
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        sequence_id = str(uuid4())
        RawText(
            uuid=uuid1, text='some text', sequence_id=sequence_id,
        ).save_to_db()
        RawText(
            uuid=uuid2, text='some other text', sequence_id=sequence_id,
        ).save_to_db()
        te = TextEmbedding(
            uuid=uuid1, embedding=[1.3, 9.0]
        )
        te.save_to_db()
        has_more = te.has_same_or_more_seq_count_than_rawtext()
        assert not has_more

        te = TextEmbedding(
            uuid=uuid2, embedding=[1.3, 0.0]
        )
        te.save_to_db()
        has_more = te.has_same_or_more_seq_count_than_rawtext()
        assert has_more

        # Delete records
        session.query(TextEmbedding).filter(
            TextEmbedding.uuid.in_([uuid1, uuid2])
        ).delete(synchronize_session=False)
        session.query(RawText).filter(
            RawText.uuid.in_([uuid1, uuid2])
        ).delete(synchronize_session=False)

    def test_get_sequence_id(self):
        """
        Test getting sequence id for TextEmbedding model
        """
        uuid1 = str(uuid4())
        sequence_id = str(uuid4())
        RawText(
            uuid=uuid1, text='some text', sequence_id=sequence_id,
        ).save_to_db()
        te = TextEmbedding(
            uuid=uuid1, embedding=[1.3, 9.0]
        )
        te.save_to_db()

        assert te.get_sequence_id() == sequence_id

        # delete records from DB
        session.query(TextEmbedding).filter(
            TextEmbedding.uuid.in_([uuid1])
        ).delete(synchronize_session=False)
        session.query(RawText).filter(
            RawText.uuid.in_([uuid1])
        ).delete(synchronize_session=False)


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

        assert q.first().status.name == 'created'

        q.delete()
        assert len(q.all()) == 0
