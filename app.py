
import os

import aws_cdk as cdk
import aws_cdk.aws_dynamodb as dynamodb

import constants
from backend.component import Backend

app = cdk.App()

# Component sandbox stack
Backend(
    app,
    constants.APP_NAME,
    env=cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
    api_lambda_reserved_concurrency=1,
    database_dynamodb_billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
)

app.synth()
