import json
from pyqldb.config.retry_config import RetryConfig
from pyqldb.driver.qldb_driver import QldbDriver

def lambda_handler(event, context):
    print(event)
    if ('body' not in event or
            event['httpMethod'] != 'PUT'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    inputs = json.loads(event['body'])
    amount = inputs['Amount']
    user_account_id = inputs['userAccountId']
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
        balance_py = balance['Balance']
        new_balance = balance_py + amount
        driver.execute_lambda(lambda executor: update_account(executor, user_account_id, new_balance))
        return {
        'statusCode': 201,
        'headers': {},
        'body': json.dumps({'msg': 'Amount added'})  
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

def update_account(transation_executore, account_id, add_amount):
    query = "UPDATE "+TABLE_NAME+" AS p SET p.Balance = ? WHERE p.userAccountId = ?"
    transation_executore.execute_statement(query, add_amount, account_id)