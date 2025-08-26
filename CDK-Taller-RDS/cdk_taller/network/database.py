from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class DatabaseInstance(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Parametrización desde context
        instance_type = scope.node.try_get_context("dbInstanceType") or "t2.micro"
        key_name = scope.node.try_get_context("dbKeyName") or "default-db-key"
        role_name = scope.node.try_get_context("dbRoleName") or "LabRole"
        volume_size = int(scope.node.try_get_context("dbVolumeSize") or 8)
        volume_type = scope.node.try_get_context("dbVolumeType") or "gp2"

        # AMI parametrizada
        ami_ssm = scope.node.try_get_context("dbAmiParameter") or \
            "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"

        ubuntu_ami = ec2.MachineImage.from_ssm_parameter(
            ami_ssm,
            os=ec2.OperatingSystemType.LINUX
        )

        key_pair = ec2.KeyPair.from_key_pair_name(
            self, "DBKeyPair",
            key_pair_name=key_name
        )

        lab_role = iam.Role.from_role_name(self, "ImportedDbRole", role_name)

        isolated_subnet = vpc.isolated_subnets[0]

        self.instance = ec2.Instance(
            self, "Instance",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ubuntu_ami,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[isolated_subnet]),
            security_group=security_group,
            role=lab_role,
            key_pair=key_pair,
            **kwargs
        )

        self.instance.instance.add_property_override(
            "BlockDeviceMappings", [
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {
                        "VolumeSize": volume_size,
                        "VolumeType": volume_type
                    }
                }
            ]
        )