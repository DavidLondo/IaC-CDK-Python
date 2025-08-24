from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class BastionHostSG(ec2.SecurityGroup):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs):
        super().__init__(
            scope,
            id,
            vpc=vpc,
            description="Enable SSH Access",
            **kwargs
        )

        ssh_port = int(scope.node.try_get_context("bastionSshPort") or 22)

        self.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(ssh_port),
            description=f"Allow SSH traffic on port {ssh_port}"
        )


class DatabaseSG(ec2.SecurityGroup):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs):
        super().__init__(
            scope,
            id,
            vpc=vpc,
            description="Allow SQL Access",
            **kwargs
        )

        mysql_port = int(scope.node.try_get_context("dbPort") or 3306)
        ssh_port = int(scope.node.try_get_context("dbSshPort") or 22)

        az1_cidr = scope.node.try_get_context("dbAz1Cidr") or "172.16.2.0/24"
        az2_cidr = scope.node.try_get_context("dbAz2Cidr") or "172.16.5.0/24"
        bastion_cidr = scope.node.try_get_context("bastionCidr") or "172.16.1.0/24"

        self.add_ingress_rule(
            peer=ec2.Peer.ipv4(az1_cidr),
            connection=ec2.Port.tcp(mysql_port),
            description=f"Allow MySQL from CMS AZ1 ({az1_cidr})"
        )
        self.add_ingress_rule(
            peer=ec2.Peer.ipv4(az2_cidr),
            connection=ec2.Port.tcp(mysql_port),
            description=f"Allow MySQL from CMS AZ2 ({az2_cidr})"
        )
        self.add_ingress_rule(
            peer=ec2.Peer.ipv4(bastion_cidr),
            connection=ec2.Port.tcp(ssh_port),
            description=f"Allow SSH from Bastion ({bastion_cidr})"
        )


class LoadBalancerSG(ec2.SecurityGroup):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs):
        super().__init__(
            scope,
            id,
            vpc=vpc,
            description="Allow HTTP/HTTPS to ALB",
            **kwargs
        )

        http_port = int(scope.node.try_get_context("lbHttpPort") or 80)

        self.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(http_port),
            description="Allow HTTP from anywhere"
        )
        self.add_ingress_rule(
            peer=ec2.Peer.any_ipv6(),
            connection=ec2.Port.tcp(http_port),
            description="Allow HTTP from IPv6"
        )


class CmsSecurityGroups(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs):
        super().__init__(scope, id, **kwargs)

        cms_http_port = int(scope.node.try_get_context("cmsHttpPort") or 80)
        cms_ssh_port = int(scope.node.try_get_context("cmsSshPort") or 22)

        cms_az1_cidr = scope.node.try_get_context("cmsAz1Cidr") or "172.16.1.0/24"
        cms_az2_cidr = scope.node.try_get_context("cmsAz2Cidr") or "172.16.4.0/24"
        bastion_cidr = scope.node.try_get_context("bastionCidr") or "172.16.1.0/24"

        self.cms_sg = ec2.SecurityGroup(
            self, "WebCMS",
            vpc=vpc,
            description="Enable HTTP Access",
            allow_all_outbound=True
        )
        self.cms_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(cms_az1_cidr),
            connection=ec2.Port.tcp(cms_http_port),
            description=f"Permit Web Requests from AZ1 ({cms_az1_cidr})"
        )
        self.cms_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(cms_az2_cidr),
            connection=ec2.Port.tcp(cms_http_port),
            description=f"Permit Web Requests from AZ2 ({cms_az2_cidr})"
        )
        self.cms_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(bastion_cidr),
            connection=ec2.Port.tcp(cms_ssh_port),
            description=f"Permit SSH from Bastion ({bastion_cidr})"
        )
