import json

from tasks.base import Base
from configs.app import ThirdParty


google_api_key = ThirdParty.GOOGLE_API_KEY


class Get3rdPartyData(Base):
    def execute(self, *args, **kwargs):
        API_PATH = 'https://www.googleapis.com/youtube/v3/commentThreads'


        import os

        import googleapiclient.discovery

        def main():
            # Disable OAuthlib's HTTPS verification when running locally.
            # *DO NOT* leave this option enabled in production.
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

            api_service_name = "youtube"
            api_version = "v3"
            DEVELOPER_KEY = google_api_key
            video_id = 'oieNTzEeeX0'

            youtube = googleapiclient.discovery.build(
                api_service_name, api_version,
                developerKey=DEVELOPER_KEY
            )

            request = youtube.commentThreads().list(
                part="snippet",
                maxResults=1000,
                textFormat="plainText",
                videoId=video_id
            )
            response = request.execute()

            with open('tests/data/youtube_comments.json', 'w') as f:
                f.write(json.dumps(response, indent=4))

        main()