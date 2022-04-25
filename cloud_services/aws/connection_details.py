"""
returns aws credentials
"""
# TODO: can be extended to parse it from file

def load_metadata_config():

    return {
        "S3_METADATA_BUCKET": "suselvar-ds2-dashboard-test",
        "S3_METADATA_PATH": "configs",
    }
