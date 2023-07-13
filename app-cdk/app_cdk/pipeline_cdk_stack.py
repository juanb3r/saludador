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


class PipelineCdkStack(Stack):

    def __init__(
            self,
            scope: Construct,
            id: str,
            secrets,
            lambda_alias,
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

        code_quality_build = codebuild.PipelineProject(
            self, "Code Quality",
            build_spec=codebuild.BuildSpec.from_source_filename("./buildspec_test.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_4,
                privileged=True,
                compute_type=codebuild.ComputeType.LARGE,
            ),
        )

        function_deploy = codedeploy.LambdaDeploymentGroup(
            self, "DeploymentGroup",
            alias=lambda_alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.LINEAR_10_PERCENT_EVERY_10_MINUTES,

        )

        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()

        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="juanb3r",
            repo="saludador",
            oauth_token=SecretValue.secrets_manager(secrets.secret_name),
            output=source_output,
            branch="master"
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Unit-Test",
            project=code_quality_build,
            input=source_output,  # The build action must use the CodeCommitSourceAction output as input.
            outputs=[unit_test_output]
        )

        pipeline.add_stage(
            stage_name="Code-Quality-Testing",
            actions=[build_action]
        )

        artifact_bucket_name = pipeline_bucket.bucket_name

        # create policy for read bucket
        deploy_policy_bucket = iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"arn:aws:s3:::{artifact_bucket_name}/*"],
            effect=iam.Effect.ALLOW
        )
        # create policy for deploy in lambda
        deploy_policy_lambda = iam.PolicyStatement(
            actions=["lambda:*"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        )

        # add policy to the role
        function_deploy.role.add_to_policy(deploy_policy_bucket)
        function_deploy.role.add_to_policy(deploy_policy_lambda)

        deploy_action = codepipeline_actions.CodeDeployServerDeployAction(
            action_name="Deploy",
            deployment_group=function_deploy,
            input=unit_test_output,
        )

        pipeline.add_stage(
            stage_name="Function-Deployment",
            actions=[deploy_action]
        )




