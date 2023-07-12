from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    SecretValue,
)


class PipelineCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, secrets, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline = codepipeline.Pipeline(
            self, "CICD_Pipeline",
            cross_account_keys=False
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




