
from typing import Any
import pathlib
import aws_cdk as cdk
import aws_cdk.aws_dynamodb as dynamodb
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
import aws_cdk.aws_lambda_python_alpha as lambda_python_alpha
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from backend.api.infrastructure import API
from backend.database.infrastructure import Database
from backend.monitoring.infrastructure import Monitoring


class Backend(cdk.Stack):
    def __init__(
            self,
            scope: Construct,
            id_: str,
            *,
            database_dynamodb_billing_mode: dynamodb.BillingMode,
            api_lambda_reserved_concurrency: int,
            **kwargs: Any,
    ):
        super().__init__(scope, id_, **kwargs)
        # Create the dynamodb tier components
        database = Database(
            self,
            "Database",
            dynamodb_billing_mode=database_dynamodb_billing_mode,
        )
        # Create the Lambda function to update currency exchange rates
        lambda_update_currency_rates = lambda_python_alpha.PythonFunction(
            self,
            "LambdaUpdateCurrencyRates",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={"DYNAMODB_TABLE_NAME": database.dynamodb_table.table_name},
            reserved_concurrent_executions=api_lambda_reserved_concurrency,
            entry=str(pathlib.Path(__file__).parent.joinpath("api/runtime").resolve()),
            index="lambda_update_exchange_rates.py",
            handler="lambda_handler",
            timeout=cdk.Duration.seconds(30),
            log_retention=RetentionDays.FIVE_DAYS,
        )
        # Create an event rule to run Lambda function at a specific rate. It can be defined as cron schedule also
        schedule_event_rule = events.Rule(self, "scheduleUpdateCurrencyRates",
                                          schedule=events.Schedule.rate(cdk.Duration.hours(12))
                                          )
        # Add lambda function to schedule event rule
        schedule_event_rule.add_target(targets.LambdaFunction(lambda_update_currency_rates,
                                                              max_event_age=cdk.Duration.hours(2),
                                                              ))
        # Create the REST API to get currency exchange rates
        api = API(
            self,
            "API",
            dynamodb_table_name=database.dynamodb_table.table_name,
            lambda_reserved_concurrency=api_lambda_reserved_concurrency,
        )
        # Setup monitoring dashboard in cloud watch
        Monitoring(self, "Monitoring", database=database, api=api)
        # Add permissions to lambda functions
        database.dynamodb_table.grant_read_write_data(lambda_update_currency_rates)
        database.dynamodb_table.grant_read_data(api.lambda_function)

        self.update = cdk.CfnOutput(
            self,
            "APIEndpoint",
            # API doesn't disable create_default_stage, hence URL will be defined
            value=api.api_gateway_http_api.url,  # type: ignore
        )

        self.lambda_update_currency_rates = cdk.CfnOutput(
            self,
            "UpdateCurrencyRateLambdaFunction",
            value=lambda_update_currency_rates.function_name,  # type: ignore
        )
