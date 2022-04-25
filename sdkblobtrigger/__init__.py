import logging
import run_aggregations
import json
import azure.functions as func


def main(myblob: func.InputStream, result_doc: func.Out[func.Document]):
    result = run_aggregations.main(None, myblob, cloud="azure")
    logging.info(
        f"Python blob trigger function processed blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    logging.info(json.dumps(result, indent=2))

    result_doc.set(func.Document.from_json(json.dumps(result)))
