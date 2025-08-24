import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_taller.cdk_taller_stack import CdkTallerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_taller/cdk_taller_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkTallerStack(app, "cdk-taller")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
