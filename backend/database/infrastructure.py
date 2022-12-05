
import aws_cdk as cdk
import aws_cdk.aws_dynamodb as dynamodb
from constructs import Construct


class Database(Construct):
    def __init__(
            self, scope: Construct, id_: str, *, dynamodb_billing_mode: dynamodb.BillingMode
    ):
        super().__init__(scope, id_)

        partition_key = dynamodb.Attribute(
            name="currency-date", type=dynamodb.AttributeType.STRING
        )
        self.dynamodb_table = dynamodb.Table(
            self,
            "DynamoDBTable",
            billing_mode=dynamodb_billing_mode,
            partition_key=partition_key,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.dynamodb_table.add_global_secondary_index(index_name="date-index",
                                                       partition_key=dynamodb.Attribute(
                                                           name="date",
                                                           type=dynamodb.AttributeType.STRING
                                                       ),
                                                       projection_type=dynamodb.ProjectionType.ALL)
