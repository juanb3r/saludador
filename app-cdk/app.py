#!/usr/bin/env python3
import os

import aws_cdk as cdk

from app_cdk.app_cdk_stack import AppCdkStack
from app_cdk.pipeline_cdk_stack import PipelineCdkStack
from app_cdk.secrets_cdk_stack import SecretsCdkStack


app = cdk.App()
AppCdkStack(app, "AppCdkStack",)
secrets = SecretsCdkStack(app, "secrets-stack")
pipeline = PipelineCdkStack(
    app, 
    "pipeline-stack",
    secrets= secrets.secret_data
    )

app.synth()
