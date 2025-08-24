from aws_cdk import (
    Duration,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct
from .security_groups import CmsSecurityGroups


class CmsAutoScaling(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Parametrización desde context
        instance_type = scope.node.try_get_context("asgInstanceType") or "t2.micro"
        role_name = scope.node.try_get_context("asgRoleName") or "LabRole"
        min_capacity = int(scope.node.try_get_context("asgMinCapacity") or 2)
        max_capacity = int(scope.node.try_get_context("asgMaxCapacity") or 4)
        health_grace_minutes = int(scope.node.try_get_context("asgHealthGraceMinutes") or 3)

        # AMI parametrizada (default: la que tenías fija)
        ami_id = scope.node.try_get_context("asgAmiId") or "ami-0c02fb55956c7d316"

        security_groups = CmsSecurityGroups(self, "CmsSecurityGroups", vpc=vpc)

        custom_ami = ec2.MachineImage.generic_linux({
            'us-east-1': ami_id
        })

        lab_role = iam.Role.from_role_name(self, "ImportedAsgRole", role_name)

        # Crear Launch Template
        launch_template = ec2.LaunchTemplate(
            self, "CmsLaunchTemplate",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=custom_ami,
            security_group=security_groups.cms_sg,
            role=lab_role,
            user_data=ec2.UserData.for_linux()
        )

        self.asg = autoscaling.AutoScalingGroup(
            self, "CmsASG",
            vpc=vpc,
            launch_template=launch_template,
            min_capacity=min_capacity,
            max_capacity=max_capacity,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            health_check=autoscaling.HealthCheck.elb(
                grace=Duration.minutes(health_grace_minutes)
            )
        )
