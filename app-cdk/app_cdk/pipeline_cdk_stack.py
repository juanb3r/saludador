from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_codedeploy as codedeploy,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    SecretValue,
    aws_iam as iam,
)
from aws_cdk.aws_lambda import Code


class PipelineCdkStack(Stack):

    def __init__(
            self,
            scope: Construct,
            id: str,
            secrets,
            lambda_code,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline_bucket = s3.Bucket(
            self, "PipelineBucket",
        )

        print(f"pipeline_bucket: {pipeline_bucket.bucket_name}")

        pipeline = codepipeline.Pipeline(
            self, "CICD_Pipeline",
            cross_account_keys=False,
            artifact_bucket=pipeline_bucket,
        )

        cdk_source_output = codepipeline.Artifact()
        lambda_source_output = codepipeline.Artifact()
        cdk_build_output = codepipeline.Artifact()
        lambda_build_output = codepipeline.Artifact()
        
        cdk_source_action = codepipeline_actions.GitHubSourceAction(
            action_name="CDK_GitHub_Source",
            owner="juanb3r",
            repo="saludador",
            oauth_token=SecretValue.secrets_manager(secrets.secret_name),
            output=cdk_source_output,
            branch="dev"
        )
        lambda_source_action = codepipeline_actions.GitHubSourceAction(
            action_name="LambdaCode_GitHub_Source",
            owner="juanb3r",
            repo="saludador_lambda",
            oauth_token=SecretValue.secrets_manager(secrets.secret_name),
            output=lambda_source_output,
            branch="master"
        )
        pipeline.add_stage(
            stage_name="Source",
            actions=[cdk_source_action, lambda_source_action]
        )   
        cdk_build_project = codebuild.Project(self, "CdkBuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_4
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": "npm install -g aws-cdk"
                    },
                    "build": {
                        "commands": [
                            "pip install -r requirements.txt",
                            "cd app-cdk && cdk synth AppCdkStack -- -o .",
                            "cdk synth AppCdkStack > ./AppCdkStack.template.yaml",
                            "ls"
                        ]
                    }
                },
                "artifacts": {
                    "files": "./AppCdkStack.template.yaml"
                }
            })
        )

        cdk_build_action = codepipeline_actions.CodeBuildAction(
            action_name="CDK_Build",
            project=cdk_build_project,
            input=cdk_source_output,
            outputs=[cdk_build_output]
        )

        lambda_build_project = codebuild.Project(self, "LambdaBuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_4
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": "pip install -r requirements.txt"
                    },
                    "build": {
                        "commands": "pip install -r requirements.txt"
                    }
                },
                "artifacts": {
                    "files": ["saludador.py"]
                }
            })
        )
        lambda_build_action = codepipeline_actions.CodeBuildAction(
            action_name="Lambda_Build",
            project=lambda_build_project,
            input=lambda_source_output,
            outputs=[lambda_build_output]
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[cdk_build_action, lambda_build_action]
        )
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Lambda_CFN_Deploy",
                    template_path=cdk_build_output.at_path("LambdaStack.template.yaml"),
                    stack_name="LambdaStackDeployedName",
                    admin_permissions=True,
                    parameter_overrides=lambda_code.assign(
                        bucket_name=pipeline_bucket.bucket_name,
                        object_key=lambda_build_output.object_key
                        ),
                    extra_inputs=[lambda_build_output]
                )
            ]
        )
