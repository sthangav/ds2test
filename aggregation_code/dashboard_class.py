"""
Functions to aggregate data
"""

import importlib
import json
import logging
import os
import sys
import time

from aggregation_code import custom_functions
from aggregation_code.provision_class import ProvisionMetadata
from aggregation_code.stream_class import StreamMetadata
from aggregation_code.utils import BaseUtils

logger = logging.getLogger(__name__)


def import_dynamic_modules(module_name):
    """
    dynamically import cloud services specific modules
    """
    # pylint: disable=broad-except
    try:
        return importlib.import_module(module_name)
    except ImportError as err:
        # warning
        logger.warning("%s: %s", type(err), err)
    except Exception as err:
        # failure on any other exception
        logger.fatal("%s: %s", type(err), err)
        sys.exit(err)
    return None


class StreamDash:
    """
    main class that reads metadata,
    input data and aggregates them
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, cloud_provider=None):

        # setting time zone as UTC
        os.environ["TZ"] = "UTC"
        time.tzset()

        # variables
        self.all_fields_map = {}
        self.result = {}
        self.final_result = {}
        self.time_period_agregatable_custom_fields = []

        # to hold class objects
        self.provision_metadata = None
        self.stream_metadata = None

        # input
        self.input_file = None
        self.all_custom_functions = None
        # self.bucket_name = bucket_name

        # to hold the results
        self.dataframe = None

        # supported other values: azure or aws
        self.cloud = cloud_provider

        # init cloud object
        self.cloud_storage_object = None
        self.init_cloud_storage_object()

    def init_cloud_storage_object(self):
        """
        sets cloud_storage_object for appropriate
        cloud service
        """

        if self.cloud is None:
            self.cloud_storage_object = BaseUtils()

        # import cloud modules and return object
        # for the respective cloud providers
        if self.cloud == "azure":
            self.azure = import_dynamic_modules("cloud_services.azure.utils")
            self.cloud_storage_object = self.azure.AzureStorageContainer()

        if self.cloud == "aws":
            self.aws = import_dynamic_modules("cloud_services.aws.utils")
            self.cloud_storage_object = self.aws.AWSStorageContainer()

    def read_metadata(self, read_provision=True):
        """
        Parent function to read all metadata/config files
        """
        self.read_all_datastream_fields()
        self.read_all_custom_functions()
        self.read_stream_metadata()
        if read_provision:
            self.read_provision()


    def read_all_datastream_fields(self):
        """
        reads the all_fields_map file consisting of
        all field related details say, id, field name, functions etc
        """
        self.all_fields_map = self.cloud_storage_object.read_all_datastream_fields_metadata()
        for i in self.all_fields_map:
            self.all_fields_map[i]["name"] = self.all_fields_map[i]["name"].lower()

    def read_all_custom_functions(self):
        self.all_custom_functions = (
            self.cloud_storage_object.read_all_custom_functions_metadata()
        )
        logger.debug("self.all_custom_functions: %s", self.all_custom_functions)

    def read_stream_metadata(self):
        """
        reads <stream>.json file and parse
        stream related details
        """
        self.stream_metadata = StreamMetadata()
        stream_buffer = self.cloud_storage_object.read_stream_metadata()
        self.stream_metadata.populate_fields(stream_buffer, self.all_fields_map)

    def read_provision(self):
        """
        To read the provision file containing
        the list of functions to aggregate data
        """
        self.provision_metadata = ProvisionMetadata()
        prov_buffer = (
            self.cloud_storage_object.read_provision_metadata()
        )  # get_provision_from_file()
        self.provision_metadata.populate_fields(prov_buffer, self.all_custom_functions)

    def read_input_data(self, input_file, bucket_name=None):
        """
        read the input file and sets the dataframe
        """

        self.input_file = input_file
        # from local dir
        if self.cloud is None:
            self.dataframe = self.cloud_storage_object.read_data_file_from_local(
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

        # for azure
        if self.cloud == "azure":
            self.dataframe = self.cloud_storage_object.read_data_file_from_azure_blob(
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

        # for aws
        if self.cloud == "aws":

            # read data file from s3 storage
            self.dataframe = self.cloud_storage_object.read_data_file_from_s3(
                bucket_name,
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

    def get_custom_fields(self):
        """
        Gets all custom fields available to the user
        used for front end
        """
        available_custom_fields = {}
        self.time_period_aggregatable_custom_fields = []
        stream_fields = self.stream_metadata.get_stream_field_names()
        logger.debug("all_custom_fields... \n%s", json.dumps(stream_fields, indent=2))

        for custom_function, custom_function_spec in self.all_custom_functions.items():
            for required_field in custom_function_spec["required-fields"]:
                if required_field in stream_fields:
                    available_custom_fields[required_field] = custom_function_spec[
                        "description"
                    ]
            if custom_function_spec["aggregatable-over-time"] == "1":
                self.time_period_aggregatable_custom_fields.append(custom_function)

        return available_custom_fields

    def process_data(self) -> dict:
        """
        reads self.dataframe and aggregate data
        """

        # invoke selected aggregation functions for fields
        for col, function_list in self.provision_metadata.fields_to_aggregate.items():
            if custom_functions.is_valid_datatype(self.dataframe[col], (int, float)):
                for function in function_list["funcs"]:
                    key_name = str(col) + "_" + str(function)
                    self.result[key_name] = custom_functions.cal_base_aggregates(
                        function, self.dataframe, col
                    )

        # invoke selected custom aggregate functions
        for function in self.provision_metadata.custom_functions:
            if function == "cal_stat_count":
                self.result.update(
                    custom_functions.cal_stat_count(self.dataframe["statuscode"])
                )

            if function == "find_cachestatus":
                self.result.update(
                    custom_functions.cal_cache_status(self.dataframe["cachestatus"])
                )

            if function == "cal_traffic_volume":
                self.result["trafficvolume"] = custom_functions.cal_traffic_volume(
                    self.dataframe["totalbytes"]
                )

            if function == "OffloadRate":
                self.result["OffloadRate"] = custom_functions.cal_offload_rate(
                    self.dataframe["cachestatus"]
                )

            if function == "originResponsetime":
                self.result[
                    "originResponsetime"
                ] = custom_functions.cal_origin_responsetime(
                    self.dataframe[
                        ["cachestatus", "cacherefreshsrc", "turnaroundtimemsec"]
                    ]
                )

            if function == "getuserAgent":
                self.result.update(
                    custom_functions.parse_user_agent(self.dataframe["ua"])
                )

            if function == "test":  # only for testing purpose
                print(self.dataframe["totalbytes"])
                print(self.dataframe["cachestatus"])
                print(self.dataframe["bytes"])
                print(self.dataframe["ua"])

            # all new custom defined functions can be invoked here

        # logger.debug(f"\nself.result: \n{json.dumps(self.result, indent=2)}")

        return self.result


def test_print(*args):
    """
    test function
    """
    print(args)
