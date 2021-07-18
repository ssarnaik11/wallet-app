import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user_account_history')

def lambda_handler(event, context):
    if ('pathParameters' not in event or
            event['httpMethod'] != 'GET'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    user_account_id = event['pathParameters']['id']
    
    response = table.query(
        KeyConditionExpression=Key('userAccountId').eq(user_account_id),
        ScanIndexForward = True,
        Limit = 100
    )
    return {
        'statusCode': 200,
        'headers': {},
        'body': json.dumps(response['Items'])
    }