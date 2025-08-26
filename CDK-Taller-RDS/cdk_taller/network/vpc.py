from aws_cdk import aws_ec2 as ec2, CfnParameter
from constructs import Construct
from aws_cdk import Stack


class CmsVpc(ec2.Vpc):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        # Leer parámetros del contexto
        vpc_cidr = scope.node.try_get_context("vpcCidr") or "172.16.0.0/16"
        max_azs = int(scope.node.try_get_context("maxAzs") or 2)
        nat_gateways = int(scope.node.try_get_context("natGateways") or 2)

        super().__init__(
            scope,
            id,
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=max_azs,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    map_public_ip_on_launch=True,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="IsolatedSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            nat_gateways=nat_gateways,
            restrict_default_security_group=False,
            **kwargs
        )

        self._assign_explicit_cidrs()

    def _assign_explicit_cidrs(self):
        cidrs = {
            'PublicSubnet': ['172.16.1.0/24', '172.16.4.0/24'],
            'PrivateSubnet': ['172.16.2.0/24', '172.16.5.0/24'],
            'IsolatedSubnet': ['172.16.3.0/24', '172.16.6.0/24']
        }

        for subnet in self.public_subnets:
            subnet.node.add_metadata("CidrBlock", cidrs['PublicSubnet'].pop(0))
        for subnet in self.private_subnets:
            subnet.node.add_metadata("CidrBlock", cidrs['PrivateSubnet'].pop(0))
        for subnet in self.isolated_subnets:
            subnet.node.add_metadata("CidrBlock", cidrs['IsolatedSubnet'].pop(0))
