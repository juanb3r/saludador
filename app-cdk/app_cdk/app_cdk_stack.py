from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_codedeploy as codedeploy,
)
from constructs import Construct

class AppCdkStack(Stack):

    @property
    def alias_data(self):
        return self.alias

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        saludador = _lambda.Function(
            self, 'SaludadorHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('../functions'),
            handler='saludador.handler',
        )

        saludador_layer = _lambda.LayerVersion(
            self, 'SaludadorLayerPytest',
            code=_lambda.Code.from_asset('../functions/layers'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_7],
            description='Saludador layer'
            )
        
        saludador.add_layers(saludador_layer)
        saludador_version = saludador.current_version

        saludador_alias_prod = _lambda.Alias(
            self, 'SaludadorAliasProd',
            alias_name='prod',
            version=saludador.current_version
        )

        saludador_alias_dev = _lambda.Alias(
            self, 'SaludadorAliasDev',
            alias_name='dev',
            version=saludador_version
        )

        self.alias = saludador_alias_dev