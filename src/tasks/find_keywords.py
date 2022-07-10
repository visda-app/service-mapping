from schema import Schema

from lib.logger import logger
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db


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


        self._total_steps = 4
        self._progress = 0
        self.record_progress(self._progress, self._total_steps)
