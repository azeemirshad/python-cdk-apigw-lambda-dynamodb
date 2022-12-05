
import pathlib
import aws_cdk as cdk
import aws_cdk.aws_apigatewayv2_alpha as apigatewayv2_alpha
import aws_cdk.aws_apigatewayv2_integrations_alpha as apigatewayv2_integrations_alpha
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as lambda_python_alpha
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct


class API(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        dynamodb_table_name: str,
        lambda_reserved_concurrency: int,
    ):
        super().__init__(scope, id_)
        # Create the lambda function to get currency exchange rates
        self.lambda_function = lambda_python_alpha.PythonFunction(
            self,
            "LambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_7,
            environment={"DYNAMODB_TABLE_NAME": dynamodb_table_name},
            reserved_concurrent_executions=lambda_reserved_concurrency,
            entry=str(pathlib.Path(__file__).parent.joinpath("runtime").resolve()),
            index="lambda_get_exchange_rate.py",
            handler="lambda_handler",
            timeout=cdk.Duration.seconds(30),
            log_retention=RetentionDays.FIVE_DAYS,
        )
        # Integrate lambda function with API gateway
        api_gateway_http_lambda_integration = (
            apigatewayv2_integrations_alpha.HttpLambdaIntegration(
                "APIGatewayHTTPLambdaIntegration", handler=self.lambda_function
            )
        )

        self.api_gateway_http_api = apigatewayv2_alpha.HttpApi(
            self,
            "APIGatewayHTTPAPI",
            default_integration=api_gateway_http_lambda_integration,
        )
