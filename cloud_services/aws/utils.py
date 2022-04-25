"""
    Utils to interact with AWS storage
"""
import io
import logging

import boto3
from aggregation_code.utils import BaseUtils
from cloud_services.aws import connection_details

logger = logging.getLogger(__name__)


class AWSStorageContainer(BaseUtils):
    """
    S3 storage modules
    """

    def __init__(self):
        """
        init bucket name and boto3 client for s3
        """
        super().__init__()
        self.metadata_bucket = None
        self.metadata_path = None
        self.data_bucket = None

        # s3 client from boto3
        self.s3_client = None

        # init metadata bucket and s3_client
        self.set_metadata_bucket()
        self.set_s3_client()

    def set_metadata_bucket(self):
        """
        returns bucket name configured
        """
        try:
            connect_info = connection_details.load_metadata_config()
            self.metadata_bucket = connect_info.get("S3_METADATA_BUCKET")
            self.metadata_path = connect_info.get("S3_METADATA_PATH")
        except Exception as err:
            logger.error(
                "Err: set variable S3_METADATA_BUCKET to your metadata bucketname "
            )
            logger.error("%s: %s", type(err), err)

    def set_s3_client(self):
        """
        returns boto3 client for s3
        """
        try:
            self.s3_client = boto3.client("s3")
        except Exception as err:
            logger.error("Error creating boto3 client for s3")
            logger.error("%s: %s", type(err), err)

    def read_from_s3(self, bucket, file_to_read) -> io.BytesIO:
        """
        returns an io buffer handle to read from
        """

        if self.s3_client is None:
            self.set_s3_client()

        response = None
        try:
            logger.debug("reading file: %s from bucket: %s", file_to_read, bucket)
            response = self.s3_client.get_object(Bucket=bucket, Key=file_to_read)
            return self.get_bytes_io_buffer(response["Body"])
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return response

    def read_json_metadata_from_s3(self, json_file) -> dict:
        """
        reads buffer from blob storage
        and return dict object
        """
        try:

            if self.metadata_path is not None:
                json_file_path = self.metadata_path + "/" + json_file

            json_buffer = self.read_from_s3(self.metadata_bucket, json_file_path)
            return self.get_dict_from_json(json_buffer)
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return {}

    def read_all_datastream_fields_metadata(self):
        # TODO: add info
        return self.read_json_metadata_from_s3(
            self.input_configs["all_datastream_fields"]
        )

    def read_all_custom_functions_metadata(self):
        """"""
        return self.read_json_metadata_from_s3(
            self.input_configs["all_custom_functions"]
        )

    def read_stream_metadata(self):
        # TODO: add info
        return self.read_json_metadata_from_s3(self.input_configs["stream_file"])

    def read_provision_metadata(self):
        """
        reads the provision_file from blob and returns the data buffer
        """

        return self.read_json_metadata_from_s3(self.input_configs["provision_file"])

    def read_data_file_from_s3(
        self, bucket, filename, file_format, chosen_field_names, custom_columns
    ):
        """
        read input data file and returns a dataframe
        """

        data_buffer = self.read_from_s3(bucket, filename)
        return self.read_data_file(
            data_buffer, file_format, chosen_field_names, custom_columns
        )
