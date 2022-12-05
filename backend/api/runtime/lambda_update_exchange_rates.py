import datetime
import os
import logging
from typing import Dict, Any

import boto3
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


dynamodb = boto3.resource("dynamodb", "us-west-2")
client = boto3.client("dynamodb", "us-west-2")
table_name = os.environ["DYNAMODB_TABLE_NAME"]
key = 'currency-date'


def save_currency_exchange_rate(key_value, data):
    """
    Saves the date in dynamodb table
    """
    logging.info(f'Adding element: key = {key_value}, date: {data}')
    table = dynamodb.Table(table_name)

    table.put_item(
        Item={key: key_value, "currency": data.get('currency'), "date": data.get('date'), "data": data})


def run_update():
    """
    Gets the latest forex rates and saves in database
    """
    today = datetime.date.today()
    # Get the latest exchange rates from
    # https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
    base_address = 'https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html'
    # Create the request
    raw_request = Request(base_address)
    # Add User agent header
    raw_request.add_header('User-Agent',
                           'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0')
    raw_request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    # Get the response in raw html
    response = urlopen(raw_request)
    raw_html = response.read()
    # Initialize soup
    soup = BeautifulSoup(raw_html, 'html.parser')
    # Get the forex rates table
    forex_table = soup.find_all('table', {"class": 'forextable'})
    for edition_elem in forex_table:
        forex_table_body = edition_elem.find('tbody')
        # Get individual rows for each currency
        table_rows = forex_table_body.find_all('tr')
        for table_row in table_rows:
            # Process and save in dynamodb
            currency = table_row.find('td', {"class", "currency"}).text

            rate = table_row.find('span', {"class", "rate"}).text
            rate = str(float(rate) + 0.1)
            key_value = f'{currency}:{today}'
            data = {
                "currency": currency, "date": today.__str__(), "rate": rate
            }
            save_currency_exchange_rate(key_value, data)


def lambda_handler(event: Dict[str, Any], context: object):
    run_update()
