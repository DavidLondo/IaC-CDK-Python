from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    SecretValue,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class RdsDatabase(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        instance_class = scope.node.try_get_context("dbInstanceClass") or "t3.micro"
        db_username = scope.node.try_get_context("dbMasterUser") or "wpuser"
        db_password = scope.node.try_get_context("dbMasterPassword") or "wppassword"
        db_identifier = scope.node.try_get_context("dbIdentifier") or "drupal"
        allocated_storage = int(scope.node.try_get_context("dbAllocatedStorage") or 20)
        storage_type = rds.StorageType.GP2

        private_subnets = vpc.private_subnets
        if len(private_subnets) < 2:
            raise ValueError("El VPC debe tener al menos 2 subredes privadas para el DB Subnet Group.")

        subnet_selection = ec2.SubnetSelection(subnets=[private_subnets[0], private_subnets[1]])

        db_subnet_group = rds.SubnetGroup(
            self, "DbSubnetGroup",
            vpc=vpc,
            description="Subnet group for RDS",
            subnet_group_name="db-subnet-group",
            vpc_subnets=subnet_selection,
            removal_policy=RemovalPolicy.DESTROY
        )

        secret_arn = scope.node.try_get_context("dbSecretArn")
        if secret_arn:
            db_secret = secretsmanager.Secret.from_secret_arn(self, "ImportedDbSecret", secret_arn)
            credentials = rds.Credentials.from_secret(db_secret)
        else:
            db_secret = secretsmanager.Secret(
                self, "DbCredentialsSecret",
                secret_name=f"{db_identifier}-credentials",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=f'{{"username":"{db_username}"}}',
                    generate_string_key="password",
                    exclude_punctuation=True,
                    password_length=16
                )
            )
            credentials = rds.Credentials.from_secret(db_secret)

        engine = rds.DatabaseInstanceEngine.maria_db(
            version=rds.MariaDbEngineVersion.VER_10_5
        )

        try:
            instance_type = ec2.InstanceType(instance_class)
        except Exception:
            instance_type = ec2.InstanceType("t3.micro")

        db_instance = rds.DatabaseInstance(
            self, "DrupalRDS",
            engine=engine,
            credentials=credentials,
            instance_identifier=db_identifier,
            instance_type=instance_type,
            vpc=vpc,
            vpc_subnets=subnet_selection,
            security_groups=[security_group],
            multi_az=True,
            allocated_storage=allocated_storage,
            storage_type=storage_type,
            publicly_accessible=False, 
            database_name="drupal",
            deletion_protection=False,
            backup_retention=Duration.days(0),
            enable_performance_insights=False,
            removal_policy=RemovalPolicy.DESTROY 
        )

        db_instance.node.add_dependency(db_subnet_group)

        self.db_instance = db_instance
        self.db_secret = db_secret
        self.db_subnet_group = db_subnet_group
