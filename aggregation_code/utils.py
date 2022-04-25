"""
    File to read metadata files from azure blob storage
    Uses connection string to connect to storage
"""

import io
import json
import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class BaseUtils:
    """
    Base class modules
    """

    def __init__(self):
        """
        init
        """

        self.__base_dir = str(Path(__file__).resolve().parent.parent)
        self.config_dir = os.path.join(self.__base_dir, "configs")
        self.input_configs = {
            "provision_file": "provision.json",
            "stream_file": "stream.json",
            "all_datastream_fields": "all_datastream_fields.json",
            "all_custom_functions": "all_custom_functions.json",
        }

    def get_dict_from_json(self, json_content) -> dict:
        """
        deserialize JSON formatted string and returns a dict
        :params:
        """
        try:
            return json.load(json_content)
        except Exception as err:
            logger.warning("%s: %s", type(err), err)
        return {}

    def get_bytes_io_buffer(self, resp_body) -> io.BytesIO:
        """
        in memory buffer
        returns BytesIO object for the response string
        """
        try:
            return io.BytesIO(resp_body.read())
        except Exception as err:
            logger.warning("%s: %s", type(err), err)
        return None

    def upload_file(self, filename, data):
        """
        write binary file to config directory
        """
        try:
            with open(os.path.join(self.config_dir, filename), "wb") as file_writer:
                file_writer.write(data)
            logger.debug("write success for file: %s", filename)

        except Exception as err:
            logger.error("write failed for file: %s", filename)
            logger.error("%s: %s", type(err), err)

    def read_file_to_text(self, file_to_read: str) -> dict:
        """
        Parse file and retuns content as text
        """
        lines = None
        try:
            with open(file_to_read, "r", encoding="UTF-8") as file_reader:
                lines = file_reader.read()

        except Exception as err:
            logger.error("reading failed for file: %s", file_to_read)
            logger.error("%s: %s", type(err), err)

        return lines

    def read_json_file_to_dict(self, file_to_read: str) -> dict:
        """
        Parse a JSON file and returns dict
        """
        json_data = {}
        try:
            with open(file_to_read, "r", encoding="UTF-8") as json_file_reader:
                json_data = json.load(json_file_reader)

        except Exception as err:
            logger.error("parsing failed for json file: %s", file_to_read)
            logger.error("%s: %s", type(err), err)
            raise

        return json_data

    def read_all_datastream_fields_metadata(self):
        # TODO: add info
        if "all_datastream_fields" in self.input_configs:
            return self.read_json_file_to_dict(
                os.path.join(
                    self.config_dir, self.input_configs["all_datastream_fields"]
                )
            )
        return {}

    def read_all_custom_functions_metadata(self):
        # TODO: add info
        if "all_custom_functions" in self.input_configs:
            return self.read_json_file_to_dict(
                os.path.join(
                    self.config_dir, self.input_configs["all_custom_functions"]
                )
            )
        return {}

    def read_stream_metadata(self):
        # TODO: add info
        if "stream_file" in self.input_configs:
            return self.read_json_file_to_dict(
                os.path.join(self.config_dir, self.input_configs["stream_file"])
            )
        return {}

    def read_provision_metadata(self):
        # TODO: add info
        if "provision_file" in self.input_configs:
            return self.read_json_file_to_dict(
                os.path.join(self.config_dir, self.input_configs["provision_file"])
            )
        return {}

    def read_data_file_from_local(
        self, filename, file_format, chosen_field_names, custom_field_names
    ):
        return self.read_data_file(
            filename, file_format, chosen_field_names, custom_field_names
        )

    def read_data_file(
        self, filename_or_buffer, file_format, chosen_field_names, custom_field_names
    ):
        """
        reads the content from the provided filename or iobuffer
        """
        output_dataframe = None

        logger.debug("all columns in the input file... \n%s", chosen_field_names)
        logger.debug("columns needed for aggregation... \n%s", custom_field_names)

        if file_format == "STRUCTURED":
            output_dataframe = pd.read_csv(
                filename_or_buffer,
                index_col=False,
                header=None,
                compression="gzip",
                names=chosen_field_names,
                usecols=custom_field_names,
                delimiter=" ",
            )
        else:
            output_dataframe = pd.read_json(
                filename_or_buffer, lines="True", compression="gzip", encoding="utf-8"
            )
            json_cnames = list(output_dataframe.columns.values)
            json_new_cname = [x.lower() for x in json_cnames]
            new_name_dic = {}
            count = 0
            for cname in json_cnames:
                new_name_dic[cname] = json_new_cname[count]
                count = count + 1
                output_dataframe = output_dataframe.rename(
                    columns=new_name_dic, inplace=False
                )

        # check if read properly
        logger.debug("top 5 rows... \n%s", output_dataframe.head(5))
        logger.debug("total rows: %s", output_dataframe.size)
        logger.debug("columns... \n%s", output_dataframe.columns)

        return output_dataframe
