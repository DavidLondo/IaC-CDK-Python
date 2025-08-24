from aws_cdk import Stack, Duration, aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from .network.vpc import CmsVpc
from .network.security_groups import BastionHostSG, DatabaseSG, LoadBalancerSG, CmsSecurityGroups
from .network.bastion_host import BastionHost
from .network.database import DatabaseInstance
from .network.auto_scaling import CmsAutoScaling

class CdkTallerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = CmsVpc(self, "CMSVPC")

        self.bastion_sg = BastionHostSG(self, "BastionHostSG", vpc=self.vpc)
        self.db_sg = DatabaseSG(self, "DatabaseSG", vpc=self.vpc)
        self.lb_sg = LoadBalancerSG(self, "LoadBalancerSG", vpc=self.vpc)
        self.cms_sgs = CmsSecurityGroups(self, "CmsSecurityGroups", vpc=self.vpc)

        self.bastion_host = BastionHost(
            self, "BastionHost",
            vpc=self.vpc,
            security_group=self.bastion_sg
        )

        self.database = DatabaseInstance(
            self, "DatabaseInstance",
            vpc=self.vpc,
            security_group=self.db_sg
        )

        cms_asg = CmsAutoScaling(
            self, "CmsAutoScaling",
            vpc=self.vpc
        )

        alb = elbv2.ApplicationLoadBalancer(
            self, "WebCMSALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="lb-WebCMS",
            security_group=self.lb_sg,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )

        listener = alb.add_listener(
            "HttpListener",
            port=80,
            open=True
        )

        listener.add_targets(
            "CmsTargets",
            port=80,
            targets=[cms_asg.asg],
            health_check={
                "path": "/",
                "interval": Duration.seconds(60),
                "healthy_threshold_count": 2,
                "unhealthy_threshold_count": 3
            }
        )