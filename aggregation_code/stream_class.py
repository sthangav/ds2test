import logging

logger = logging.getLogger(__name__)


class Fields:
    def __init__(self, dataset_id, dataset_name):
        self.id = dataset_id
        self.name = dataset_name


class StreamMetadata:
    def __init__(self):

        self.stream_activation_status = None
        self.delimiter = None
        self.stream_format = None
        self.chosen_fields = []  # list of objects of class Fields

    def __str__(self):
        """
        outputs all the members of the class
        """
        return "Stream Metadata-> \n\t Activation-Status : {},\n\t Delimiter : {},\n\t Format : {},\n\t Field Names : {}\n".format(
            self.stream_activation_status,
            self.delimiter,
            self.stream_format,
            self.chosenFieldsNames,
        )

    def get_datasetids(self, stream_datasets) -> list:
        """
        Returns the ordered list of dataset ids
        """

        rslt = {}
        for dataset in stream_datasets:
            for datafield in dataset["datasetFields"]:
                rslt[datafield.get("order", datafield["datasetFieldId"])] = str(
                    datafield["datasetFieldId"]
                )

        # return array as specified in the order
        return [val for _, val in sorted(rslt.items())]

    def populate_fields(self, stream_buffer, all_ds_fields):
        """
        sets self.chosen_fields
        """
        try:
            self.stream_activation_status = stream_buffer.get("activationStatus")
            if "config" in stream_buffer:
                self.stream_format = stream_buffer["config"].get("format")
                self.delimiter = stream_buffer["config"].get("delimiter")
        except Exception as err:
            logger.error(
                "%s: Stream activationStatus or config format/delimiter not set: %s",
                type(err),
                err,
            )

        chosen_ids = self.get_datasetids(stream_buffer.get("datasets", []))

        self.chosen_fields.append(Fields(None, "version"))
        for i in chosen_ids:
            try:
                self.chosen_fields.append(Fields(i, all_ds_fields[i]["name"].lower()))
            except Exception as err:
                logger.warn("%s: key %s not found in all_fields_map ", err, i)

        logger.debug("stream fields... \n%s", self.get_stream_field_names())

    def get_stream_field_names(self):
        """
        returns the list of field names
        """
        return [field.name for field in self.chosen_fields]
