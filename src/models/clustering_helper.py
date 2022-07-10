import json

from models.job_text_mapping import (
    JobTextMapping,
    TextTypes,
)
from models.text import Text
from models.clustered_text import ClusteredText
from models.db import session
from lib.logger import logger


def load_first_embeddings_from_db(job_id):
    q = session.query(Text, JobTextMapping).filter(
        Text.id == JobTextMapping.text_id
    ).filter(
        JobTextMapping.job_id == job_id
    ).filter(
        JobTextMapping.text_type == TextTypes.SENTENCE.value
    )
    db_vals = q.all()

    results = []

    for (text, job_text_relation) in db_vals:
        results.append({
            'embedding': json.loads(text.embedding),
            'text': text.text,
            'uuid': text.id,
            'sequence_id': job_id
        })

    return results


def _get_query_clustering(job_id):
    q = session.query(Text, JobTextMapping).filter(
        Text.id == JobTextMapping.text_id
    ).filter(
        JobTextMapping.job_id == job_id
    )
    logger.debug(q)
    return q


def get_clustering_count(sequence_id):
    q = _get_query_clustering(sequence_id)
    return q.count()


def save_clustering_to_db(sequence_id, clustering):
    ClusteredText(
        sequence_id=sequence_id,
        clustering=clustering
    ).save_to_db()
