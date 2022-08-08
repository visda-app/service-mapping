from schema import Schema
import numpy as np

from lib.logger import logger
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from lib.nlp import get_tokens
from models.clustering_helper import load_first_embeddings_from_db
from models.text import Text as TextModel


KWARGS_SCHEMA = {}


def _cacheable_get_tokens(text):
    return get_tokens(text)


class FindKeywords(BaseTask):
    """
    The texts and the tokens in the text are assumed to
    be vectorized (embedded) so in this module, only the
    relevant keywords are extracted from each sentence
    """
    public_description = "Extracting keywords"

    def __init__(self, *args, **kwargs):
        logger.debug(kwargs)
        super().__init__(*args, **kwargs)

    @record_start_finish_time_in_db
    def execute(self):
        # Validate schema
        schema = Schema(KWARGS_SCHEMA)
        try:
            schema.validate(self.kwargs)
        except Exception as e:
            logger.exception(str(e))
            raise
        job_id = self.job_id
        
        # Load all the texts for the job ## FIXME Add some sort of paginations?
        texts = load_first_embeddings_from_db(job_id)
        logger.debug('Sentences loaded.')
        self._total_steps = len(texts)

        self._progress = 0
        self.record_progress(self._progress, self._total_steps)
        
        # Get embedding for each token
        token_embeddings = {}

        # Calculate similarities and sort high to low
        for text_item in texts:
            text_embed = text_item['embedding']
            text_embed_array = np.array(text_embed)

            txt = text_item['text']
            tokens = _cacheable_get_tokens(txt)

            for token in tokens:
                if token not in token_embeddings:
                    embedding = TextModel.get_embedding_by_text(token)
                    if embedding:
                        token_embeddings[token] = np.array(embedding)


            token_embeds = [{
                'token': token,
                'similarity': token_embeddings[token].dot(text_embed_array)
            } for token in tokens]
            token_embeds.sort(key=lambda x: -x['similarity'])

            # Store tokens in the database
            TextModel(
                id=text_item['uuid'],
                tokens=token_embeds,
            ).save_or_update()

            self._progress += 1
            self.record_progress(self._progress, self._total_steps)
