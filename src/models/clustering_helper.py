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
        JobTextMapping.text_type == TextTypes.RAW_TEXT.value
    )
    db_vals = q.all()

    results = []

    for (text, job_text_relation) in db_vals:
        tokens = None
        if text.tokens:
            tokens = json.loads(text.tokens)
        results.append({
            'embedding': json.loads(text.embedding),
            'text': text.text,
            'uuid': text.id,
            'sequence_id': job_id,
            'tokens': tokens,
        })

    return results


def load_texts_from_db(job_id):
    results = load_first_embeddings_from_db(job_id)
    return [
        {
            "uuid": e["uuid"],
            "text": e["text"],
        } 
        for e in results
    ]


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

