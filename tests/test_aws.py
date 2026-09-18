import boto3

sts = boto3.client("sts")

identity = sts.get_caller_identity()

print("AWS connection successful")
print("User ID:", identity["UserId"])
print("Account:", identity["Account"])
print("ARN:", identity["Arn"])