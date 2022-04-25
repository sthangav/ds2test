"""
defines all custom functions to aggregate the data
"""
import json
import logging
import os
import time

import httpagentparser

logger = logging.getLogger(__name__)

def init_metric_fillers():
    """
    init new record
    :rtype: dict
    """
    # Initialize the dictionary
    list_keys = [
        "request_count",
        "2xx_count",
        "3xx_count",
        "4xx_count",
        "5xx_count",
    ]
    return dict.fromkeys(list_keys, 0)


def convert_time(epoch_time, time_format="%s", delta=1):
    """
    Converts GMT epoch time to the specified time format.
    Also rounds off to the nearest minute, hour, day when valid delta value is passed
    :param epoch_time: epoch time to be converted
    :param time_format: expected output time format
                         example: "%Y-%m-%d %H:%M:%S", "%s", ...
    :param delta: in seconds to be rounded off.
                  example: 300, 1800, 3600...
    :rtype: time
    Example:
        >>> epoch_time = "1541399309.143"
        >>> convert_time(epoch_time)
        '1541399309'
        >>> convert_time(epoch_time, time_format="%Y-%m-%d %H:%M:%S %Z")
        '2018-11-05 06:28:29 UTC'
        >>> convert_time(epoch_time, time_format="%Y-%m-%d %H:%M:%S %Z", delta=300)
        '2018-11-05 06:25:00 UTC'
        >>> convert_time(epoch_time, delta=300)
        '1541399100'
    """
    os.environ["TZ"] = "UTC"
    time.tzset()
    # reset delta if unexpected value
    if delta <= 0:
        delta = 1
    # round off the epoch to specified delta
    epoch_rounded = float(epoch_time) - (float(epoch_time) % delta)
    # return in GMT format
    return time.strftime(time_format, time.gmtime(float(epoch_rounded)))


def is_valid_datatype(data_to_check, data_types):
    """
    check if the data is of the provided datatypes
    returns True or False
    """
    for data in data_to_check:
        if not isinstance(data, data_types):
            return False
    return True


def cal_base_aggregates(lst, csvdata, col):
    """
    basic aggregations are defined here
    """
    out = 0
    if lst == "sum":
        out = csvdata[col].sum()
    if lst == "min":
        out = csvdata[col].min()
    if lst == "max":
        out = csvdata[col].max()
    if lst == "mean":
        out = csvdata[col].mean()
    if lst == "median":
        out = csvdata[col].median()
    if lst == "variance":
        out = csvdata[col].median()
    if lst == "any":
        out = csvdata[col].any()
    if lst == "count":
        out = csvdata[col].count()
    return float(out)

def get_unique_counts_of_column(input_df) -> dict:
    """
    returns json formatted output of
    distinct counts of the input dataframe column
    """
    buffer = input_df.value_counts()
    return json.loads(buffer.to_json())

def cal_stat_count(status_code_df):
    """
    returns {2,3,4,5}xx_count and request_count
    """

    mdata = init_metric_fillers()
    uniq_status_code_counts = get_unique_counts_of_column(status_code_df)
    for status_code, st_count in uniq_status_code_counts.items():
        status_code_prefix = int(int(status_code) / 100)
        if status_code_prefix in [2, 3, 4, 5]:
            mdata[str(status_code_prefix) + "xx_count"] += st_count

    mdata["request_count"] = int(status_code_df.count())
    return mdata


def cal_traffic_volume(totalbytes_df):
    """
    sum of totalbytes column
    """
    return int(totalbytes_df.sum())


def cal_cache_status(cache_df):
    """
    returns dict;
    example,
    ```
    {
      "cache_hit": 1,
      "cache_miss": 0,
    }
    ```
    """
    uniq_cache_counts = get_unique_counts_of_column(cache_df)
    cache = {}
    cache["cache_hit"] = uniq_cache_counts.get("1", 0)
    cache["cache_miss"] = uniq_cache_counts.get("0", 0)
    return cache


def cal_offload_rate(cache_df):
    """
    calculates offload rate as,
    total cache hits * 100 / total hits
    """
    return cache_df[cache_df == 1].sum() * 100.00 / cache_df.count()


def cal_origin_responsetime(dfs):
    """
    calculated as =>
    sum("turnaroundtimemsec")
    where cachestatus == 0 and cacherefreshsrc == 'origin'
    """
    return int(
        dfs.query("cachestatus == 0 and cacherefreshsrc == 'origin'")[
            "turnaroundtimemsec"
        ].sum()
    )


def extract_from_ua(ua_string, to_extract):
    """
    extracts requested info from User Agent String
    """
    client_info = httpagentparser.detect(ua_string)
    if to_extract in client_info:
        if client_info[to_extract]["name"] is not None:
            return client_info[to_extract]["name"]
    return str("invalid")


def parse_user_agent(user_agent):
    """
    returns platform, os, browser distribution details.
    example,
    ```
    "platform": {
      "Windows": 30
    },
    "os": {
      "Windows": 30
    },
    "browser": {
      "Chrome": 30
    }
    ```
    """
    ua_info = (
        "os",
        "browser",
        "platform",
    )
    client_info = {}
    for to_extract in ua_info:
        client_info[to_extract] = user_agent.apply(extract_from_ua, args=(to_extract,))
        # convert to json
        client_info[to_extract] = json.loads(
            client_info[to_extract].value_counts().to_json()
        )
    return client_info
