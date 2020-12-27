import os
import json
import googleapiclient.discovery

from tasks.base import Base
from configs.app import ThirdParty


class Get3rdPartyData(Base):
    def execute(self, *args, **kwargs):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY
        video_id = kwargs['video_id']

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version,
            developerKey=DEVELOPER_KEY
        )

        params = {
            'part': 'snippet',
            'maxResults': 1000,
            'textFormat': 'plainText',
            'videoId': video_id
        }
        if kwargs.get('page_token'):
            params['pageToken'] = kwargs['page_token']

        request = youtube.commentThreads().list(**params)
        response = request.execute()

        if kwargs.get('test'):
            with open('tests/data/youtube_comments.json', 'w') as f:
                f.write(json.dumps(response, indent=4))

