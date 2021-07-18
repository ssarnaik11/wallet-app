import json
from aws_kinesis_agg.deaggregator import deaggregate_records
from datetime import datetime
import amazon.ion.simpleion as ion
import base64
import boto3

REVISION_DETAILS_RECORD_TYPE = "REVISION_DETAILS"
USER_ACCOUNT = 'user_account'
USER_TABLE_FIELDS = ["userAccountId","Name", "Balance"]
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user_account_history')

def lambda_handler(event, context):
    
    # Get all records
    raw_kinesis_records = event['Records']
    
    records = deaggregate_records(raw_kinesis_records)
    
    for record in filtered_records_generator(records,table_names=[USER_ACCOUNT]):
        table_name = record["table_info"]["tableName"]
        revision_data = record["revision_data"]
        revision_metadata = record["revision_metadata"]
        version = revision_metadata["version"]
        document = None

        if revision_data:
            if (table_name == USER_ACCOUNT) and fields_are_present(USER_TABLE_FIELDS, revision_data):
                document = create_document(USER_TABLE_FIELDS, revision_data)
                print(type(document))
                print(document)
                item ={}
                item['userAccountId'] = document['userAccountId']
                item['Name'] = document['Name']
                item['Balance'] = str(document['Balance'])
                item['Timestamp'] = datetime.now().isoformat()
                table.put_item(Item = item)
    return {
        'statusCode': 200
    }

def filtered_records_generator(kinesis_deaggregate_records, table_names=None):
    for record in kinesis_deaggregate_records:
        # Kinesis data in Python Lambdas is base64 encoded
        payload = base64.b64decode(record['kinesis']['data'])
        # payload is the actual ion binary record published by QLDB to the stream
        ion_record = ion.loads(payload)
        print("Ion record: ", (ion.dumps(ion_record, binary=False)))

        if ("recordType" in ion_record) and (ion_record["recordType"] == REVISION_DETAILS_RECORD_TYPE):
            table_info = get_table_info_from_revision_record(ion_record)

            if not table_names or (table_info and (table_info["tableName"] in table_names)):
                revision_data, revision_metadata = get_data_metdata_from_revision_record(ion_record)

                yield {"table_info": table_info,
                       "revision_data": revision_data,
                       "revision_metadata": revision_metadata}


def get_data_metdata_from_revision_record(revision_record):

    revision_data = None
    revision_metadata = None

    if ("payload" in revision_record) and ("revision" in revision_record["payload"]):
        if "data" in revision_record["payload"]["revision"]:
            revision_data = revision_record["payload"]["revision"]["data"]
        else:
            revision_data = None
        if "metadata" in revision_record["payload"]["revision"]:
            revision_metadata = revision_record["payload"]["revision"]["metadata"]

    return [revision_data, revision_metadata]


def get_table_info_from_revision_record(revision_record):

    if ("payload" in revision_record) and "tableInfo" in revision_record["payload"]:
        return revision_record["payload"]["tableInfo"]

def create_document(fields, revision_data):
    document = {}

    for field in fields:
        document[field] = revision_data[field]

    return document

def fields_are_present(fields_list, revision_data):
    for field in fields_list:
        if not field in revision_data:
            return False
    return True
    
    
    
  