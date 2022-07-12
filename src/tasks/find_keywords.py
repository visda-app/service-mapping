from schema import Schema

from lib.logger import logger
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from lib.nlp import get_tokens


KWARGS_SCHEMA = {}


class FindKeywords(BaseTask):
    """
    The texts and the tokens in the text are assumed to
    be vectorized (embedded) so in this module, only the
    relevant keywords are extracted from each sentence
    """
    public_description = "Extracting keywords."

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
        
        # Load all the texts for the job ## FIXME really? All the texts? No paginations?
        from models.clustering_helper import load_first_embeddings_from_db
        texts = load_first_embeddings_from_db(self.job_id)
        logger.debug('Sentences loaded.')
        
        # tokenize
        all_tokens = []
        for item in texts:
            tokens = get_tokens(item['text'])
            all_tokens.extend(tokens)
        all_tokens = list(dict.fromkeys(all_tokens))

        # Get embedding for each token
        from models.text import Text as TextModel
        token_embeddings = []
        for token in tokens:
            embedding = TextModel.get_embedding_by_text(token)
            if embedding:
                token_embeddings[token] = embedding

        # Find similarities and sort hight to low
        for text_item in texts:
            pass
        
        # Store tokens in the database

        self._total_steps = 4
        self._progress = 0
        self.record_progress(self._progress, self._total_steps)
