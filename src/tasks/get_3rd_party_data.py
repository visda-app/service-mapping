from tasks.base import Base
from configs.app import ThirdParty


google_api_key = ThirdParty.GOOGLE_API_KEY


class Get3rdPartyData(Base):
    def execute(self, *args, **kwargs):
        pass
