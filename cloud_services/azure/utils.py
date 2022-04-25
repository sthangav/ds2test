"""
    Utils to interact with Azure blob storage
    Uses connection string to connect to storage
"""

import logging
import json
from typing import Container
import io 
from aggregation_code.utils import BaseUtils
from cloud_services.azure import connection_details

from azure.storage.blob import ContainerClient

logger = logging.getLogger(__name__)


def get_container_client(load_function):
    """
    return client to interact with a specific container
    """
    try:
        connect_info = load_function()
        #connect_info = connection_details.load_metadata_config()

        
        # TODO: test purpose; need to remove this debug msg
        logger.debug(
            "azure_storage_connectionstring: %s\n",
            connect_info["azure_storage_connectionstring"],
        )
        logger.debug(
            "metadata_container_name: %s\n", connect_info["metadata_container_name"]
        )
        return ContainerClient.from_connection_string(
            connect_info["azure_storage_connectionstring"],
            connect_info["metadata_container_name"],
        )
    except Exception as err:
        logger.error("%s: %s", type(err), err)
    return None


def read_from_blob(container_client, file_name):
    """
    reads the file_name from blob
    and returns the content as text
    """
    try:
        blob_client = container_client.get_blob_client(file_name)
        return blob_client.download_blob().readall()

       # return blob_client.download_blob().content_as_text()
    except Exception as err:
        logger.error("%s: %s", type(err), err)
    return None


def upload_file(container_client, filename, data):
    """
    upload file to blob
    """
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(data)


def delete_file(container_client, filename):
    """
    delete file from blob
    """
    container_client.delete_blob(filename)


class AzureStorageContainer(BaseUtils):
    # TODO: add info

    def __init__(self):
        """
        init
        """
        # init base class
        super().__init__()

        # Create Container Clients to read metadata and data
        self.container_client_for_metadata = get_container_client(
            connection_details.load_metadata_config
        )
        self.container_client_for_data = None

    def read_json_metadata_from_blob(self, container_client, json_file):
        """
        read json file from blob storage
        and return dict object
        """
        try:
            json_content = read_from_blob(container_client, json_file)
            return json.loads(json_content)
            
          #  return self.get_dict_from_json(json_content)
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return {}

    def read_all_datastream_fields_metadata(self):
        """"""
        # TODO: add info
        return self.read_json_metadata_from_blob(
            self.container_client_for_metadata,
            self.input_configs["all_datastream_fields"],
        )

    def read_all_custom_functions_metadata(self):
        """"""
        return self.read_json_metadata_from_blob(
            self.container_client_for_metadata,
            self.input_configs["all_custom_functions"],
        )

    def read_stream_metadata(self):
        """"""
        # TODO: add info
        return self.read_json_metadata_from_blob(
            self.container_client_for_metadata, self.input_configs["stream_file"]
        )

    def read_provision_metadata(self):
        """"""
        # TODO: add info
        return self.read_json_metadata_from_blob(
            self.container_client_for_metadata, self.input_configs["provision_file"]
        )

    def read_data_file_from_azure_blob(
        self, filename, file_format, chosen_field_names, custom_columns
    ):
        """
        reads data file from azure blob store
        and returns dataframe
        """

        data_buffer = io.BytesIO(filename.read())
        
        return self.read_data_file(
            data_buffer, file_format, chosen_field_names, custom_columns
        )
