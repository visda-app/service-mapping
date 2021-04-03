import unittest
from random import random

from models.text import Text as TextModel
from models.job_text_mapping import JobTextMapping
from lib.logger import logger
from models.db import create_all_tables


logger.info('Creating tables...')
create_all_tables()


class TestJobTextMapping(unittest.TestCase):
    def setUp(self):
        self.text_ids = [str(int(1000 * random())) for i in range(4)]
        self.job_ids = [str(int(1000 * random())) for i in range(4)]

    def tearDown(self):
        for id in self.text_ids:
            TextModel.delete_by_id(id)
        for id in self.job_ids:
            JobTextMapping.delete_by_job_id(id)

    def _random_embedding(self):
        return [int(1000*random())/10 for i in range(3)]

    def test_save_to_db(self):
        TextModel(
            id=self.text_ids[0],
            text='Humans are driven by selfish gene.',
            embedding=self._random_embedding(),
        ).save_or_update()
        TextModel(
            id=self.text_ids[1],
            text='Selfish gene enables human to survive.',
            # embedding=self._random_embedding(),
        ).save_or_update()
        TextModel(
            id=self.text_ids[2],
            text='Selfish gene-s made us collaborative, trustworthy, and social.',
            embedding=self._random_embedding(),
        ).save_or_update()
        TextModel(
            id=self.text_ids[3],
            text='Good and Bad are relative.',
            # embedding=self._random_embedding(),
        ).save_or_update()

        JobTextMapping(
            text_id=self.text_ids[0],
            job_id=self.job_ids[0],
        ).save_to_db()
        JobTextMapping(
            text_id=self.text_ids[1],
            job_id=self.job_ids[0],
        ).save_to_db()
        JobTextMapping(
            text_id=self.text_ids[2],
            job_id=self.job_ids[1],
        ).save_to_db()
        JobTextMapping(
            text_id=self.text_ids[3],
            job_id=self.job_ids[1],
        ).save_to_db()

        not_done = JobTextMapping.get_unprocessed_texts_count_by_job_id(self.job_ids[0])
        total = JobTextMapping.get_total_texts_count_by_job_id(self.job_ids[0])

        assert not_done == 1
        assert total == 2
