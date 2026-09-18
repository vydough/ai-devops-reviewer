import boto3

session = boto3.Session(
    profile_name="ai-devops-sydney",
    region_name="ap-southeast-2"
)

client = session.client("bedrock-runtime")

response = client.converse(
    modelId="global.anthropic.claude-sonnet-4-6",
    messages=[{
        "role": "user",
        "content": [{"text": "Explain what a pull request is in one sentence."}]
    }]
)

print(response["output"]["message"]["content"][0]["text"])
print("Input tokens:", response["usage"]["inputTokens"])
print("Output tokens:", response["usage"]["outputTokens"])
print("Total tokens:", response["usage"]["totalTokens"])