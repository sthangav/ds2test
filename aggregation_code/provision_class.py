"""
used to parse provision file and populate
necessary fields that will be used for aggregation.
"""

import logging
import json

logger = logging.getLogger(__name__)


class ProvisionMetadata:
    """
    provision class
    """

    def __init__(self):
        self.__data = {}
        self.fields_to_aggregate = {}
        self.custom_functions = {}
        self.default_agg_interval = -1

    def __str__(self) -> str:
        return f"ProvisionMetadata obj, fields={self.fields_to_aggregate}, custom_fields={self.custom_functions}"

    def populate_fields(self, provbuffer, all_custom_functions):
        """
        sets self.fields_to_aggregate
        and self.custom_fields by reading the provbuffer
        """

        # read provision file
        self.__data = {k.lower(): v for k, v in provbuffer.items()}

        # construct the necessary fields needed to apply
        # basic aggregate functions and custom functions
        for func_name in self.__data.keys():
            if func_name != "custom-func":
                self.fields_to_aggregate[func_name] = {
                    "agg_interval": self.__data[func_name][0],
                    "funcs": self.__data[func_name][1],
                }
            else:
                for function in self.__data["custom-func"]:
                    if function not in all_custom_functions:
                        logger.debug("function invalid or not defined: %s", function)
                        continue

                    self.custom_functions[function] = {
                        "agg_interval": self.default_agg_interval,
                        "funcs": [],
                    }
                    # append the fields used for dependent functions
                    for dep_field in all_custom_functions[function].get("required-fields"):
                        # check to prevent overriding of any aggregates
                        if dep_field not in self.fields_to_aggregate:
                            self.fields_to_aggregate[dep_field] = {
                                "agg_interval": self.default_agg_interval,
                                "funcs": [],
                            }

        logger.debug(
            "provision_metadata.fields_to_aggregate... \n%s",
            json.dumps(self.fields_to_aggregate, indent=2),
        )
        logger.debug(
            "provision_metadata.custom_functions... \n%s",
            json.dumps(self.custom_functions, indent=2),
        )

    def get_provision_field_names(self):
        """
        returns the list of field names
        from the provision file
        """
        return list(self.fields_to_aggregate.keys())
