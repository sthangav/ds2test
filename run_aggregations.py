"""
Main Module
"""
# TODO: add more info

import argparse
import textwrap
import logging
import time
import json
import os

from aggregation_code.dashboard_class import StreamDash


def parse_inputs() -> dict:
    """
    parse the input command line arguments
    and return dictionary
    """
    # TODO: add details of the code functionality
    parser = argparse.ArgumentParser(
        prog=__file__,
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """\
            Helps aggregate data
            """
        ),
    )

    parser.add_argument(
        "--loglevel",
        default="debug",
        type=str,
        choices=["critical", "error", "warn", "info", "debug"],
        help=textwrap.dedent(
            """\
            logging level.
            (default: %(default)s)
            \n"""
        ),
    )

    args, _ = parser.parse_known_args()
    return vars(args)


def init_logging(log_level):
    """
    creates a logger
    """
    log_levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=log_levels[log_level],
        format="%(process)5d| "
        + "%(asctime)s| "
        + "%(levelname)8s| "
        + "%(name)s:[%(funcName)s]:%(lineno)d|"
        + " %(message)s",
    )
    # create logger
    logger = logging.getLogger()

    return logger


def main(aws_event, azure_blob, cloud=None):
    """
    main function
    """
    params = parse_inputs()

    # reset defaults
    # params["loglevel"] = "info"

    logger = init_logging(params["loglevel"])
    logger.debug("logging level set to %s mode", params["loglevel"])

    # init
    obj = StreamDash(cloud_provider=cloud)

    # parse config files
    logger.debug("read metadata files...")
    obj.read_metadata()

    # set input data
    input_file = None
    input_bucket = None

    if cloud is None:
        # temporarily setting the input file
        input_file = os.getcwd() + "/sample-input/test-data-custom.gz"

    if cloud == "aws":
        input_bucket = aws_event["Records"][0]["s3"]["bucket"]["name"]
        input_file = aws_event["Records"][0]["s3"]["object"]["key"]

    if cloud == "azure":
        input_file = azure_blob

    # parse input data
    logger.debug("read input files...")
    obj.read_input_data(input_file=input_file, bucket_name=input_bucket)

    # process input data
    logger.debug("process input files...")
    obj.process_data()

    # publish results
    return obj.result


if __name__ == "__main__":
    result = main(None, None, None)
    print("Result...")
    print(json.dumps(result, indent=2))
