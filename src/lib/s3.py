import boto3
import json
from botocore import errorfactory
from lib.logger import logger

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
except Exception as e:
    logger.exception(e)
    raise


def _upload_to_s3(key, data):
    """
    """
    if type(data) is not str:
        data = json.dumps(data)
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
    obj_str = obj_bin.decode('utf-8')
    obj = json.loads(obj_str)
    return obj


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
    upload_to_s3_with_check(s3_key, data)
