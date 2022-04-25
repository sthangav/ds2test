# DS2 Dashboard

# About The Project

To empower DS2 customers and create a value to the data delivered to customer object store(S3), business value driven SDK/Package is provided to customer to run on a serverless function (Lambda) and derive metrics to various destination like cloudwatch, SNS, DyanoDB, etc.., Currently, we are supporing only cloudwatch as destination from lambda functions

#Built With

* python3.8
* pandas
* httpagentparser

![Dataflow](./images/demo.jpg)

## Important files

```sh
├── lambdaModule.zip (zip included lambda.py and it is uploaded to S3)
├── lambda.py (Main appliation for running lambda)
├── metadata
│   ├── aggfield.txt (contains agg fields)
│   ├── edge_fields.json (pulled from the ds2 config API)
│   ├── provision.json (metadata to provision lambda function)
│   └── stream.json (pulled from ds2 config api)
├── prov-helper.py (outputs field names)
├── README.md
```

### Code Structure

```
├── aggregation_code
│   ├── __init__.py
│   ├── custom_functions.py
│   ├── dashboard_class.py
│   ├── provision_class.py
│   ├── stream_class.py
│   └── utils.py
├── cloud_services
│   ├── __init__.py
│   ├── aws
│   │   ├── __init__.py
│   │   ├── connection_details.py
│   │   ├── requirements.txt
│   │   └── utils.py
│   └── azure
│       ├── __init__.py
│       ├── connection_details.py
│       ├── requirements.txt
│       └── utils.py
├── configs
│   ├── all_custom_functions.json
│   ├── all_datastream_fields.json
│   ├── prov_site_with_time.json
│   ├── provision.json
│   └── stream.json
├── readme.md
├── requirements.txt
└── run_aggregations.py
```

## Getting started

### Features

1. Derive metrics from DS2 Logs uploaded to aws S3
2. Supportability DS2 formats
   - JSON
   - STRUCTURED

### Input Configuration Files

The following are the details on the list of input configuration files used by this package

* [all_datastream_fields.json](#all_datastream_fields)
* [all_custom_functions.json](#all_custom_functions)
* [stream.json](#stream-json)
* [provision.json](#provision-json)


#### <a name="all_datastream_fields">all_datastream_fields.json</a>

1. This JSON file consists of all dataset Fields available in datastream 
2. Example
```json
{
    [...]
	"2003": {
		"name": "objSize",
		"cname": "Object size",
		"dtype": "bigint",
		"agg": [
			"min", "max", "sum", 
		]
	},
    [...]
}
```
3. This file contains the following details,
    - field id
        - The field id (say, `"2003"`) corresponds to the the `datasetFieldId` in stream.json file. 
    - _"name"_ 
    - _"dtype"_ 
        - data type of the field
    - _"cname"_ 
        - field description
    - _"agg"_ 
        - The `"agg"` tag consists of the list of aggregate functions that can be supported by this field, provided that field is selected in `stream_json` file. Thus removing it from `"agg"` list disables the function for that field.
        - Say, 
            - _"min"_: minimum
            - _"max"_: maximum
            - _"sum"_
            - _"count"_ 
            - _"mean"_
            - _"median"_
            - _"variance"_

4. Sample File is stored in: `conf/all_datastream_fields.json`
    - This is a common file and updated only when new fields are added to the datastream. 


#### <a name="all_custom_functions">all_custom_functions.json</a>

1. This JSON file contains the list of all the available custom functions that can be selected to aggregate the data.
2. Example,
```json
{
    [...]
    "cal_stat_count": {
        "required-fields": [
            "statuscode"
        ],
        "description": "Show Stat Count of HTTP requests"
    },
    [...]
}
```
3. This file contains the following details,
    - function name  


<-- reached till here -->


2. The dimension tag supports 2 field types say direct and/or derived fields
   1. The direct fields are the list of datasetFieldId in the stream json file.
   2. The derived fields are list of function names specified under the queries section in this JSON file.
3. The formulas are sql functions with column name represented as `_var_`. This will be replaced by the respective column name during the query generation.
4. The functions specified here can be an aggregate(`SUM`, `AVG`, etc) or non aggregate function (`SUBSTR`, `URL_DECODE` etc). However all the enabled non aggregated functions needs to be added to derived dimension.
5. Default: `conf/formulas.json`
6. A customized version of this JSON file can be passed to the script using `--formulas_json <FORMULAS_JSON>` argument.

Example,

```json
{
    "dimension": {
        "direct": [
            "1000",
            "1001"
        ],
        "derived": [
            "req_5min"
        ]
    },
    "queries": {
        "1xx": {
            "q": "sum(case when _var_ / 100 = 1 then 1 else 0 end)",
            "desc": "The count of 1xx error codes for this time interval"
        },
        "2xx": {
            "q": "sum(case when _var_ / 100 = 2 then 1 else 0 end)",
            "desc": "The count of 2xx error codes for this time interval"
        },
        ...
        ...,
        "req_5min": {
            "q": "from_unixtime(_var_ - (_var_ % 300))",
            "desc": "Request Time rounded to the nearest 5 min interval"
        }
    }
}
```

#### <a name="stream-json">stream.json</a>

1. This is a JSON file containing the stream specific details.
2. i.e this file is used to understand the fields configured for this stream.
3. This can be pulled from portal using the steps mentioned [here](#pull-stream-configs)
4. Sample File is stored in: `configs/stream_temp.json`
    - This needs to be updated with the stream specific file.


### Prerequisites

* Create three S3 buckets one for uploading lambdamodule(code-bucket) and one for copying metadata(metadata-bucket). The third bucket is where data is uploaded by DS2.
* Setup Datastream2 config API tools
  https://developer.akamai.com/api/core_features/datastream2_config/v1.html#getstarted

### Setup

1. Clone the repo:

   ```sh
   git clone ssh://git@git.source.akamai.com:7999/sources/ds2-sdk.git
   ```
2. Change the directory ds2-lambda/metadata

   ```sh
   cd ds2-lambda/metadata
   ```
3. Pull the stream detail and edge logs using datastream2 config API

   ```sh
   http --auth-type edgegrid  -a default: :/datastream-config-api/v1/log/streams/{streamid} -o stream.json
   ```

   ```sh
   http --auth-type=edgegrid -a default: ":/datastream-config-api/v1/log/datasets/template/EDGE_LOGS -o edge_fields.json"  
   ```
4. List the  current working directory

   ```sh ls
      aggfield.txt
      edge_fields.json
      provision.json
      stream.json
   ```
5. Upload all files in metadata directory to your S3 bucket (metadata-bucket) created for metadata directly under the bucket.
6. Go to ds2-lambda directory and then  upload lambdaModule.zip file to S3 bucket (code-bucket) created for uploading code

> Note down S3 metadata & code bucketname

### Setup Lambda functions

1. Ensure the IAM user used to create the lambda function has the following policies associated with it
   ```sh
   "arn:aws:iam::aws:policy/AmazonS3FullAccess",
   "arn:aws:iam::aws:policy/AWSLambdaExecute,AWSCloudFormationFullAccess",
   "arn:aws:iam::aws:policy/AWSLambda_FullAccess", 
   "arn:aws:iam::aws:policy/AmazonS3ObjectLambdaExecutionRolePolicy",
   "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess"
   ```
2. Create lambda function in lambda service
3. Select code settings in function
   - code option ->  upload from -> Amazon s3 location
   - provide  s3 location of S3 bucket
   - configure Runtime settings
     - select  : python 3.8
     - Handler : lambda.process
     - Architecture : x86_64
4. Set Configuration settings
   - General configuration : timeout to 5-15 min ~
   - Triggers : set to your incoming DS2 stream s3 bucket
   - Environment Variables :
     - S3_METADATA_BUCKET  yourmetadatabucketname

### How to provision your Lambda function

1. Run provision helper to find the customer opted fields

   ```sh
   python3 prov-helper.py -s  metadata/stream.json -m metadata/edge_fields.json
   ```
2. Choose the fields from the output of helper script toderive metrics, make sure the field opted is present in
   the aggfield.txt

   #### provision.json


   ```json
   {
     "Bytes" : ["max", "min", "sum"],
     "rspcontentLen" : ["sum", "max"],
   }
   ```
   supported aggregation:
   | max  | min | count | sum | mean | median | variance | any |

3. The  provision.json file  is uploaded to S3 metadata bucket when DS2 stream logs flow to the bucket,
   lambda function is triggerred to produce output in the cloudwatch logs
4. sample output will be like the following

   ```json
   {bytes_max : 2000, bytes_min: 1000, bytes_sum : 3000, rspcontentlen_sum: 2000, rspcontentlen_max: 1000}
   ```

### How to provision custom function in Lambda

1. Choose the functions from the table to configure in provision.json


   | custom function | DS2 fields | Recommended Memory |
   | - | - | - |
   | cal_stat_count | statuscode | >512 MB |
   | cal_traffic_volume | totalbytes | > 512 MB |
   | find_cachestatus | cachestatus | > 512 MB |
   | OffloadRate | cachestatus | > 512 MB |
   | originResponsetime | turnaroundtimemsec | > 512 MB |
   | getuserAgent | ua | > 1024 MB |
2. Example for provisioning custom-func

   provision.json

   ```json
   {
     "Bytes" : ["max", "min", "sum"],
     "rspcontentLen" : ["sum", "max"],
     "custom-func" :["cal_stat_count", "getuserAgent" ]
   }
   ```
   sample output:

   ```json
   {bytes_max : 2000, bytes_min: 1000, bytes_sum : 3000, rspcontentlen_sum: 2000, rspcontentlen_max: 1000}
   {'request_count': 14, '2xx_count': 0, '3xx_count': 0, '4xx_count': 14, '5xx_count': 0}
   os: {"Windows":14}
   platform: {"Windows":14}
   browser: {"Chrome":14}
   ```

## How to run for AWS
- Clone the repo 
- Run Locally
    - Install all dependencies
        - `pip3 install -r requirements.txt`
    - Start the website
        - `python3 manage.py runserver`
        - Go to http://127.0.0.1:8000/ and choose the configurations
    - Run the aggregations
        - `python3 run_aggregations.py`

- Deployed on azure
    - navigavate to url http://ds2-django-webapp.azurewebsites.net/
    - choose required fields and configs
    - navigate to url http://test-azure-function-ds2-dash.azurewebsites.net/api/testing_ds2_dash_azfunction to trigger the function
    - output is displayed on the webpage itself (for now)

- Aggregation code present in main/aggregation_code/source_code
    - Main class file is in dashboard_class.py

- To add more custom_functions 
    - add a new line to custom_fields.txt in the format {i,j,k} where i is the custom_function identifier, j is the stream field the custom function uses and k is the description of the custom field
    - add the function definition to main/aggregation_code/source_code/custom_functions.py
    

- To deploy website on azure using cli 
    - Create deployment user on azure cli  
        - `az webapp deployment user set --user-name <username> --password <password>`
    - Create app service plan
        - `az appservice plan create --name staging --resource-group <resource group name> --sku F1 --is-linux`
    - Create app and set runtime
        - `az webapp create --resource-group <resource group name> --plan staging --name configuration-website --runtime "PYTHON|3.8" --deployment-local-git`
    - Copy the git link created from previous command and add it as remote to the git repo of the website
    - Push to the newly added remote to deploy the website
    - Navigate to http://configuration-website.azurewebsites.net/ 


- or use script
    - ` ./deploy_website.sh <username> <password> <resource group name> `
        - username and password cannot contain '@'
        - username should be unique
    -  Navigate to http://configuration-website.azurewebsites.net/ 

## How to run for Azure

TODO: Sathya