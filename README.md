# Currency Exchange Rate API using AWS CDK, Lambda, Dynamodb and API Gateway
The project implements a *currency exchange rate backend* component that uses 
Amazon API Gateway, AWS Lambda and Amazon DynamoDB to fetch the latest exchange rates from [European Central Bank Website](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html)
and provides basic APIs to:
- Get current exchange rates. 
- How the exchange rate has changed compared to the previous day.

<br>The project uses AWS CDK for deployment. It was set up using the [aws-cdk-project-structure-python](https://github.com/aws-samples/aws-cdk-project-structure-python)
template provided by AWS.

## Components
It has the following components:

### Database
Dynamodb is used to store exchange rates info. The key is formed by concatenating currency and date. An additional index
of `date` is defined to allow querying on date as well. 

### Update Exchange Rates Lambda Function
This Lambda function runs every 12 hours. It fetches the latest exchange rates from [European Central Bank Website](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html)
and stores them in dynamodb. It can be changed to run on a cron schedule as per requirement.

### Get Exchange Rates Lambda Function
This lambda function is tied to API gateway and provides two functionalities. 
- Get exchange rates and change in exchange rates for all currencies.
- Get exchange rates and change in exchange rates for a particular currency.

### API Gateway
It creates an API gateway and ties to lambda function.

### Monitoring
It creates a dashboard in Cloud Watch with two widgets:
- API Gateway metric count
- Dynamodb consumed read capacity unit metric count

## Deployment
Unzip the provided archive file. 
```bash
unzip python-cdk-apigw-lambda-dynamodb-main
cd python-cdk-apigw-lambda-dynamodb-main
```
### Create Python virtual environment and install the dependencies
```bash
python3.8 -m venv .venv
source .venv/bin/activate

pip install pip-tools==6.4.0
pip install pip==21.3.1

./scripts/install-deps.sh
```

### Deploy the component
The `CurrencyExchangeRateBackend` stack uses AWS account and region setup using `CDK_DEFAULT_ACCOUNT` and `CDK_DEFAULT_REGION` environment variables.

```bash
export CDK_DEFAULT_ACCOUNT=<YOUR_ACCOUNT>
export CDK_DEFAULT_REGION=<YOUR_REGION>
npx cdk bootstrap
npx cdk deploy CurrencyExchangeRateBackend
```

Example output for `npx cdk deploy CurrencyExchangeRateBackend`:
```text
 ✅  CurrencyExchangeRateBackend

Outputs:
CurrencyExchangeRateBackend.APIEndpoint = https://afwaatt0j1.execute-api.us-west-2.amazonaws.com/
CurrencyExchangeRateBackend.UpdateCurrencyRateLambdaFunction = CurrencyExchangeRateBacke-LambdaUpdateCurrencyRate-84C3MQPW6KX6
Stack ARN:
arn:aws:cloudformation:us-west-2:007148109666:stack/CurrencyExchangeRateBackend/f95c7500-745d-11ed-a0c1-0612a202de15

```

## Testing the API
The Update Exchange Rates lambda function executes every 12 hours. However, you may invoke it once, before testing. 
Below are examples that show the available resources and how to use them.

```bash
function_name=$(aws cloudformation describe-stacks \
  --stack-name CurrencyExchangeRateBackend \
  --query 'Stacks[*].Outputs[?OutputKey==`UpdateCurrencyRateLambdaFunction`].OutputValue' \
  --region $CDK_DEFAULT_REGION \
  --output text )

aws lambda invoke --function-name ${function_name} out --log-type Tail --region $CDK_DEFAULT_REGION
  
api_endpoint=$(aws cloudformation describe-stacks \
  --stack-name CurrencyExchangeRateBackend \
  --query 'Stacks[*].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --region $CDK_DEFAULT_REGION \
  --output text )

curl "${api_endpoint}/exchange_rates"

curl "${api_endpoint}/exchange_rates/USD"

```

## Delete the stack
**Do not forget to delete the stacks to avoid unexpected charges**
```bash
npx cdk destroy CurrencyExchangeRateBackend
```
