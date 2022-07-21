from uuid import uuid4
import pytest
from unittest.mock import patch

from tasks.find_keywords import FindKeywords



TEXT_EMBEDDINGS = [
    {
        'uuid': 'something_unique_001',
        'text': 'How are you?',
        'embedding': [1, 2, 3],
        'sequence_id': 'a_unique_sequence_idk',
    },
    {
        'uuid': 'something_unique_002',
        'text': 'How are you?',
        'embedding': [0.1, 0.2, 0.3],
        'sequence_id': 'a_unique_sequence_idk',
    },
]


@patch('tasks.find_keywords.TextModel.save_or_update')
@patch('tasks.find_keywords.TextModel.get_embedding_by_text')
@patch('tasks.find_keywords.load_first_embeddings_from_db')
def test_get_3rd_party_data_execute(mock_load_embeddings_from_db, mock_text_model, mock_save_to_db):
    job_id = str(uuid4())

    mock_load_embeddings_from_db.return_value = TEXT_EMBEDDINGS
    mock_text_model.return_value = [2, 3, 4]

    t = FindKeywords(
        job_id=job_id,
        kwargs={}
    )

    t.execute()

