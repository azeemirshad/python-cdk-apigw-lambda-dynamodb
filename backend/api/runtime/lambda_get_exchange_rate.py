import datetime
import logging
import os
from typing import Any, Dict
import boto3
from aws_lambda_powertools.event_handler import api_gateway
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

dynamodb = boto3.resource('dynamodb')

app = api_gateway.ApiGatewayResolver(
    proxy_type=api_gateway.ProxyEventType.APIGatewayProxyEventV2
)


def lambda_handler(event: Dict[str, Any], context: object) -> Dict[str, Any]:
    return app.resolve(event, context)


@app.get("/exchange_rates")  # type: ignore
def list_exchange_rates():
    """
    Returns exchange rates for all currencies in format
    {"currency": "DKK", "date": "2022-12-04", "rate": "7.537299999999999", "change": "0.0000"}
    """
    data_list = []
    exchange_rates = []
    today = datetime.date.today()
    try:
        # Get the exchange rates data from database
        table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
        query_response = table.query(
            IndexName='date-index',
            KeyConditionExpression=Key('date').eq(today.__str__()),

        )

        data_list = query_response.get("Items")
        # handle pagination if required
        while 'LastEvaluatedKey' in query_response:
            query_response = table.query(ExclusiveStartKey=query_response['LastEvaluatedKey'],
                                   IndexName='date-index',
                                   KeyConditionExpression=Key('date').eq(today.__str__()),
                                   )
            data_list.extend(query_response['Items'])
        # Process retrieved data to produce desired output
        for data_item in data_list:
            # Get yesterday's exchange rate to determine change
            yesterday = today - datetime.timedelta(1)
            key_value = f"{data_item.get('currency')}:{yesterday}"
            yesterday_item = query_table_by_key('currency-date', key_value)
            change = None
            if yesterday_item:
                yesterday_rate = yesterday_item.get('data').get('rate')
                change = float(data_item.get('data').get('rate')) - float(yesterday_rate)
                change = f"{change:.4f}"
            if not change:
                change = "Rate for yesterday not available"
            # Create object to return
            exchange_rates.append(dict(currency=data_item.get('currency'), date=data_item.get('date'),
                                       rate=data_item.get('data').get('rate'), change=change))
    except Exception as e:
        logging.exception(e)

    return exchange_rates


@app.get("/exchange_rates/<currency>")  # type: ignore
def get(currency):
    """
        Returns exchange rates for a specific currency in format
        {"currency": "DKK", "date": "2022-12-04", "rate": "7.537299999999999", "change": "0.0000"}
    """
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(1)
    result = {}
    try:
        # fetch data from the database
        key_value = f"{currency}:{today}"
        today_item = query_table_by_key('currency-date', key_value)
        change = None
        if today_item:
            # Get yesterday's exchange rate to determine change
            key_value = f"{currency}:{yesterday}"
            yesterday_item = query_table_by_key('currency-date', key_value)
            change = None
            if yesterday_item:
                yesterday_rate = yesterday_item.get('data').get('rate')
                change = float(today_item.get('data').get('rate')) - float(yesterday_rate)
                change = f"{change:.4f}"
            if not change:
                change = "Rate for yesterday not available"
            # Create object to return
            result = dict(currency=today_item.get('currency'), date=today_item.get('date'),
                          rate=today_item.get('data').get('rate'), change=change)
    except Exception as e:
        logging.exception(e)

    return result


def query_table_by_key(key, key_value):
    """
    Gets a record from dynamodb
    """
    try:
        if key_value:
            table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
            response = table.get_item(Key={key: key_value})
            if response.get('Item', {}):
                return response['Item']
    except Exception as e:
        logging.exception(e)
    return None
