import json
from pyqldb.config.retry_config import RetryConfig
from pyqldb.driver.qldb_driver import QldbDriver

def lambda_handler(event, context):
    if ('pathParameters' not in event or
            event['httpMethod'] != 'GET'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    user_account_id = event['pathParameters']['id']
    driver = create_qldb_driver(LEDGER_NAME)

    # Check if account already exists
    try:
        document =  driver.execute_lambda(lambda executor: find_account_by_id(executor, user_account_id))
    except StopIteration:
        print("Error")
        document = None

    if document is None:
        return {
        'statusCode': 201,
        'headers': {},
        'body': json.dumps({'msg': 'User account doesnt exists' })
    }
    else :
        balance = driver.execute_lambda(lambda executor: check_balance(executor,user_account_id))
        
        return {
        'statusCode': 201,
        'headers': {},
        'body': json.dumps({'msg': 'Balance for account','Balance': balance['Balance']})  
    }
# Constants
LEDGER_NAME = 'wallet-ledger'
TABLE_NAME = 'user_account'

# Connect to QLDB

def create_qldb_driver(ledger_name):
# Configure retry limit to 3
    retry_config = RetryConfig(retry_limit=3)
# Initialize the driver
    print("Initializing the driver")
    driver = QldbDriver(ledger_name, retry_config=retry_config)
    return driver

# find account by id 
def find_account_by_id (transaction_executor, account_id):
    query = "SELECT p.* FROM "+TABLE_NAME+" AS p BY userAccountId WHERE p.userAccountId = ?"
    cursor = transaction_executor.execute_statement(query , account_id)
    return next(cursor)

def check_balance(transaction_executor, account_id):
    query = "SELECT p.Balance FROM "+TABLE_NAME+" AS p BY userAccountId WHERE  p.userAccountId=?"
    cursor = transaction_executor.execute_statement(query , account_id)
    return next(cursor)
