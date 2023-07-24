from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_codedeploy as codedeploy,
    aws_s3 as s3
)
from constructs import Construct


class AppCdkStack(Stack):

    @property
    def alias_data(self):
        return self.alias
    
    @property
    def lambda_code_data(self):
        return self.lambda_code
    
    @property
    def lambda_layer_data(self):
        return self.lambda_layer

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code = _lambda.Code.from_cfn_parameters()
        lambda_layer = _lambda.Code.from_cfn_parameters()

        saludador = _lambda.Function(
            self, 'SaludadorHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=lambda_code,
            handler='saludador.handler',
        )

        saludador_layer = _lambda.LayerVersion(
            self, 'SaludadorLayer',
            code=lambda_layer,
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_7],
            description='Saludador layer'
            )
        
        saludador.add_layers(saludador_layer)
        saludador_version = saludador.current_version

        saludador_alias_dev = _lambda.Alias(
            self, 'SaludadorAliasDev',
            alias_name='dev',
            version=saludador_version
        )

        self.alias = saludador_alias_dev
        self.lambda_code = lambda_code
        self.lambda_layer = lambda_layer
