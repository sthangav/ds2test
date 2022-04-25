"""
returns azure credentials
"""
# TODO: can be extended to parse it from file

def load_metadata_config():

    return {
        "azure_storage_connectionstring": "DefaultEndpointsProtocol=https;AccountName=hotchips;AccountKey=P8uIDQMu6OI71IU12BR2U31R6QXRAAsTm+etU5oeucUz0KspME1PU/xWgSdjai+11FOw1gO7JxFmUljqNQPH1A==;EndpointSuffix=core.windows.net",
        "metadata_container_name": "ds2meta",
    }
