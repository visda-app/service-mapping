import unittest
from uuid import uuid4

from models.text import Text as TextModel
from lib.logger import logger
from models.db import create_all_tables


logger.info('Creating tables...')
create_all_tables()


class TestTextModel(unittest.TestCase):
    # def setUp(self):
    #     self.uuid1 = str(uuid4())
    #     self.uuid2 = str(uuid4())
    #     Text(
    #         uuid=self.uuid1,
    #         text='some text',
    #         embedding=[0.1, 0.2, 0.3],
    #     ).save_or_update()
    #     Text(
    #         uuid=self.uuid2,
    #         text='some other text',
    #         embedding=[0.4, 0.5, 0.6],
    #     ).save_or_update()

    # def tearDown(self):
    #     # Delete users
    #     session.query(TextEmbedding).filter(
    #         TextEmbedding.uuid.in_([self.uuid1, self.uuid2])
    #     ).delete(synchronize_session=False)

    #     session.query(RawText).filter(
    #         RawText.uuid.in_([self.uuid1, self.uuid2])
    #     ).delete(synchronize_session=False)

    def test_save_to_db(self):
        uuid1 = str(uuid4())

        # Check no record exist in the beginning
        results = TextModel.get_by_id(uuid1)
        assert results is None

        # Create a record in the DB
        # embedding = [0.11, 0.22, 0.3]
        TextModel(
            id=uuid1,
            text='some text',
            # embedding=embedding,
        ).save_or_update()

        results = TextModel.get_by_id(uuid1)
        assert results is not None

        breakpoint()

        # Delete the record
        TextModel.delete_by_id(uuid1)

        results = TextModel.get_by_id(uuid1)
        assert results is None

    def test_save_or_update(self):
        uuid1 = str(uuid4())

        # Check no record exist in the beginning
        results = TextModel.get_by_id(uuid1)
        assert results is None

        # Create a record in the DB
        first_embedding = [0.1, 0.2, 0.3]
        TextModel(
            id=uuid1,
            text='some text',
            embedding=first_embedding,
        ).save_or_update()

        results = TextModel.get_by_id(uuid1)
        assert results is not None

        # Update the record
        second_embedding = [0.7, 0.8, 0.9]
        TextModel(
            id=uuid1,
            embedding=second_embedding,
        ).save_or_update()

        results = TextModel.get_by_id(uuid1)
        assert results is not None
        assert results.embedding == second_embedding

        # Delete the record
        TextModel.delete_by_id(uuid1)

        results = TextModel.get_by_id(uuid1)
        assert results is None

    def test_save_or_update_nullable_false(self):
        uuid1 = str(uuid4())

        # Create a record in the DB
        with self.assertRaises(ValueError):
            TextModel(
                id=uuid1,
                embedding=[0.1, 0.2, 0.3],
            ).save_or_update()

        results = TextModel.get_by_id(uuid1)
        assert results is None


    # def test_raw_text_save_to_db(self):
    #     # Create a record in DB:
    #     uuid1 = str(uuid4())
    #     sequence_id = str(uuid4())
    #     RawText(
    #         uuid=uuid1,
    #         text='some random text',
    #         sequence_id=sequence_id
    #     ).save_to_db()
    #     # Query the created record:
    #     q = session.query(RawText).filter(
    #         RawText.uuid == uuid1
    #     )
    #     # Check if the record is in DB
    #     assert len(q.all()) == 1
    #     # Delete record
    #     q.delete()
    #     # Check if deleted successfully
    #     assert len(q.all()) == 0

    # def test_text_embedding_save_to_db(self):
    #     # Should create a raw text to satisfy the foreign key constraint
    #     TextEmbedding(
    #         uuid=self.uuid1,
    #         embedding=[1.2, 3, 0.91, 5.0]
    #     ).save_to_db()
    #     # Query the created record:
    #     q = session.query(TextEmbedding).filter(
    #         TextEmbedding.uuid == self.uuid1
    #     )
    #     # Check if the record is in DB
    #     assert len(q.all()) == 1

    # # def test_text_embedding_get_count_by_sequence_id(self):
    # #     """
    # #     Test TextEmbedding model to have the right count by sequence_id
    # #     """
    # #     TextEmbedding(uuid=self.uuid1, embedding=[]).save_to_db()
    # #     assert TextEmbedding.get_count_by_sequence_id(self.sequence_id) == 1
    # #     TextEmbedding(uuid=self.uuid2, embedding=[]).save_to_db()
    # #     assert TextEmbedding.get_count_by_sequence_id(self.sequence_id) == 2

    # def test_text_embedding_has_same_or_more_items_than_raw_text(self):
    #     """
    #     Check if the TextEmbedding model has same or more items
    #     than RawText for the same sequence id
    #     """
    #     te = TextEmbedding(
    #         uuid=self.uuid1, embedding=[1.3, 9.0]
    #     )
    #     te.save_to_db()
    #     has_more = te.has_same_or_more_seq_count_than_rawtext()
    #     assert not has_more

    #     te = TextEmbedding(
    #         uuid=self.uuid2, embedding=[1.3, 0.0]
    #     )
    #     te.save_to_db()
    #     has_more = te.has_same_or_more_seq_count_than_rawtext()
    #     assert has_more

    # def test_get_sequence_id(self):
    #     """
    #     Test getting sequence id for TextEmbedding model
    #     """
    #     te = TextEmbedding(
    #         uuid=self.uuid1, embedding=[1.3, 9.0]
    #     )
    #     te.save_to_db()

    #     assert te.get_sequence_id() == self.sequence_id
