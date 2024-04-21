#!/usr/bin/python3
import boto3
import json
#from prompts import PROMPTS

ASSUME_ROLE = False
STREAM_ENABLED = True

# Assume role to get keys and token
def assume_role():
    sts_client = boto3.client(
        service_name = 'sts',
        aws_access_key_id='123',
        aws_secret_access_key='123',
    )
    print("Your current caller identity(user/role):")
    current_caller_identity = sts_client.get_caller_identity()
    print("Account:", current_caller_identity['Account'], "Arn:", current_caller_identity['Arn'])

    assumed_role_object = sts_client.assume_role(
        RoleArn="arn:aws:iam::123456789012:role/bedrock-test",
        RoleSessionName="Bedrock-Test"
    )
    print("Get credentials: ")
    access_key = assumed_role_object['Credentials']['AccessKeyId']
    secret_key = assumed_role_object['Credentials']['SecretAccessKey']
    session_token = assumed_role_object['Credentials']['SessionToken']
    print("AccessKey:", access_key)
    print("SecretKey:", secret_key)
    print("SessionToken:", session_token)

    return access_key, secret_key, session_token

def main():

    if ASSUME_ROLE:
        access_key, secret_key, session_token = assume_role()
        # Use keys and token to invoke bedrock
        # set to us-east-1 region
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name='us-east-1'
        )
    else:
        bedrock = boto3.client('bedrock-runtime')

    modelId = 'anthropic.claude-3-sonnet-20240229-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100000,
        "messages":[
            {"role": "user", "content": "What is nvlink and nvswitch?"},
            #{"role": "user", "content": PROMPTS[7]}
        ]

    })

    if STREAM_ENABLED:
        response = bedrock.invoke_model_with_response_stream(
            body=body,
            modelId=modelId,
            accept=accept,
            contentType=contentType,
        )
        stream = response['body']
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_obj = json.loads(chunk.get("bytes").decode())
                    if chunk_obj['type'] == 'content_block_delta':
                        print(chunk_obj['delta']['text'], end='')
        print()
    else:
        response = bedrock.invoke_model(
            body=body,
            modelId=modelId,
            accept=accept,
            contentType=contentType
        )
        response_body = json.loads(response.get('body').read())
        for content in response_body['content']:
            print(content['text'])

if __name__ == '__main__':
    main()
