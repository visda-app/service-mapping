import boto3
import json
from botocore import errorfactory
from lib.logger import logger
import base64
import zlib

from configs.app import AWS as aws_configs


CLUSTERING_BUCKET_NAME = "cogneetion-clustering-data"
LOCATION_CONSTRAINT_VALUE = aws_configs.region

client = boto3.client(
    's3',
    aws_access_key_id=aws_configs.access_key_id,
    aws_secret_access_key=aws_configs.secret_access_key,
    region_name=aws_configs.region,
)

try:
    client.create_bucket(
        Bucket=CLUSTERING_BUCKET_NAME,
        CreateBucketConfiguration={
            'LocationConstraint': LOCATION_CONSTRAINT_VALUE,
        }
    )
except client.exceptions.BucketAlreadyOwnedByYou:
    pass
except Exception:
    logger.exception()
    raise


def _upload_to_s3(key, data):
    """
    """
    client.put_object(
        Body=data,
        Bucket=CLUSTERING_BUCKET_NAME,
        Key=key,
        ACL='public-read'
    )


def _delete_from_s3(key):
    """
    """
    response = client.delete_object(
        Bucket=CLUSTERING_BUCKET_NAME,
        Key=key,
    )
    return response


def _get_object_from_s3(key):
    """
    """
    response = client.get_object(
        Bucket=CLUSTERING_BUCKET_NAME,
        Key=key,
    )
    obj_bin = response['Body'].read()
    return obj_bin


def _get_s3_key(sequence_id):
    """
    """
    return f"maps/{sequence_id}"


def _does_obj_exist(key):
    """
    """
    try:
        head_obj = client.head_object(
            Bucket=CLUSTERING_BUCKET_NAME,
            Key=key,
        )
    except client.exceptions.ClientError:
        return False
    return True

def _dumps_and_compress(data):
    """
    Compress data to be unzipped in the JavaScript Code

    More info at:
    https://stackoverflow.com/questions/72947222/compress-with-python-zlib-decompress-in-javascript-zlib

    To decompress in JavaScript:
        ```
        let compressedData = Uint8Array.from(atob(input), (c) => c.charCodeAt(0));
        let decompressedData = pako.inflate(compressedData, { to: "string" });
        let jsonObject = JSON.parse(decompressedData);
        ```
    """
    if type(data) is dict:
        # data = base64.b64encode(
        #     zlib.compress(
        #         bytes(json.dumps(data), "utf-8")
        #     )
        # ).decode("ascii")

        data_dumped = json.dumps(data)
        data_bytes = bytes(data_dumped, "utf-8")
        data_zipped = zlib.compress(data_bytes)
        data_b64 = base64.b64encode(data_zipped)
        data_ascii = data_b64.decode("ascii")

    return data_ascii


def _get_compressed_data_from_s3(key):
    """
    """
    obj_bin = _get_object_from_s3(key)
    
    d0 = obj_bin.decode('utf-8')
    d1 = bytes(d0, "ascii")
    d2 = base64.b64decode(d1)
    d3 = zlib.decompress(d2)
    d4 = d3.decode("utf-8")

    return d4


def upload_to_s3_with_check(key, data):
    """
    """
    if _does_obj_exist(key):
        raise ValueError(f"S3 Obj exists at key={key}")
    _upload_to_s3(key, data)


def upload_clustering_data_to_s3(sequence_id, data):
    """
    """
    if type(data) is not dict:
        raise ValueError("An input with type dictionary is required.")

    s3_key = _get_s3_key(sequence_id)

    data = _dumps_and_compress(data)

    upload_to_s3_with_check(s3_key, data)
