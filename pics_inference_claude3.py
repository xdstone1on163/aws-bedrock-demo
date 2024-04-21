#!/usr/bin/python3
import boto3
import json
import os
import sys
import base64
import requests
import time
import pprint
from datetime import datetime
#from prompts import PROMPTS

ASSUME_ROLE = True #可以设置True or False来决定在脚本内部扮演角色还是用脚本外部的aws configure环境
STREAM_ENABLED = False
REGION = 'us-east-1' #设定要使用的Region

# Assume role to get keys and token, the aksk is from a user called: bedrock_caller
def assume_role():
    sts_client = boto3.client(
        service_name = 'sts',
        aws_access_key_id='xxxx',#这里的Key就是你创建的IAM用户的Key
        aws_secret_access_key='xxxx',#这里的Key就是你创建的IAM用户的secret
        region_name = REGION
    )
    print("Your current caller identity(user/role):")
    current_caller_identity = sts_client.get_caller_identity()
    print("Account:", current_caller_identity['Account'], "Arn:", current_caller_identity['Arn'])

    assumed_role_object = sts_client.assume_role(
        RoleArn="arn:aws:iam::xxxxxx:role/bedrock_full_access_role_for_iam_user_to_assume",#这里的ARN就是你创建的IAM角色的ARN
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

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
	
#"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
# non streaming mode
def anthropic_claude_3(modelId,image_path,max_tokens):
    bedrock_runtime = boto3.client('bedrock-runtime')
    base64_image = encode_image(image_path)
    payload = {
        "modelId": modelId,
        "contentType": "application/json",
        "accept": "application/json",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "system": "You are an AI bot",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            #"text": "Write me a detailed description of these two photos, and then a poem talking about it."
                            "text": f"What’s in this image? output {max_tokens} tokens"
                        }
                    ]
                }
            ]
        }
    }
	
    # Convert the payload to bytes
    body_bytes = json.dumps(payload['body']).encode('utf-8')
	
    # Invoke the model
    response = bedrock_runtime.invoke_model(
        body=body_bytes,
        contentType=payload['contentType'],
        accept=payload['accept'],
        modelId=payload['modelId']
    )
	
    # Process the response
    response_body = json.loads(response['body'].read().decode('utf-8'))
    pprint.pprint(response_body)
    #return round(end-start,2),response_body["usage"]["input_tokens"],response_body["usage"]["output_tokens"]
    return round(float(response['ResponseMetadata']['HTTPHeaders']['x-amzn-bedrock-invocation-latency'])/1000,2),int(response['ResponseMetadata']['HTTPHeaders']['x-amzn-bedrock-input-token-count']),int(response['ResponseMetadata']['HTTPHeaders']['x-amzn-bedrock-output-token-count'])
	
#"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
# streaming mode
def anthropic_claude_3_stream(modelId,image_path,max_tokens):
    bedrock_runtime = boto3.client('bedrock-runtime')
    base64_image = encode_image(image_path)
    payload = {
        "modelId": modelId,
        "contentType": "application/json",
        "accept": "application/json",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "system": "You are an AI bot",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            #"text": "Write me a detailed description of these two photos, and then a poem talking about it."
                            "text": f"What’s in this image? output {max_tokens} tokens"
                        }
                    ]
                }
            ],
            "temperature": 1,
            "top_p": 0.999,
            "top_k": 250,
"stop_sequences": ['\n\nHuman:']
        }
    }
	
    # Convert the payload to bytes
    body_bytes = json.dumps(payload['body']).encode('utf-8')
	
    # Invoke the model
    response = bedrock_runtime.invoke_model_with_response_stream(
        body=body_bytes, modelId=payload['modelId'], accept=payload['accept'], contentType=payload['contentType']
    )
    stream = response.get('body')
    chunk_obj = {}
	
    if stream:
        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                chunk_obj = json.loads(chunk.get('bytes').decode())
                pprint.pprint(chunk_obj)
	
    # Process the response
    #response_body = json.loads(response['body'].read().decode('utf-8'))
    #pprint.pprint(response_body)
    {'type': 'message_stop', 'amazon-bedrock-invocationMetrics': {'inputTokenCount': 92, 'outputTokenCount': 277, 'invocationLatency': 3679, 'firstByteLatency': 677}}
	
    return round(float(chunk_obj['amazon-bedrock-invocationMetrics']['firstByteLatency'])/1000,2),round(float(chunk_obj['amazon-bedrock-invocationMetrics']['invocationLatency'])/1000,2),chunk_obj['amazon-bedrock-invocationMetrics']['inputTokenCount'],chunk_obj['amazon-bedrock-invocationMetrics']['outputTokenCount']
	


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
            region_name=REGION
        )
    else:
        bedrock = boto3.client('bedrock-runtime', region_name=REGION)

    #wget https://cats.com/wp-content/uploads/2020/10/tabby-maine-coon-768x384.jpg first in your console
    image_path = "tabby-maine-coon-768x384.jpg"
    max_tokens = 200
    #haiku
    print("Haiku:")
    modelId = "anthropic.claude-3-haiku-20240307-v1:0"
    if STREAM_ENABLED:
        print(anthropic_claude_3_stream(modelId,image_path,max_tokens))
    else:
        print(anthropic_claude_3(modelId,image_path,max_tokens))	
    #sonnet
    print("Sonnet:")
    modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    if STREAM_ENABLED:
        print(anthropic_claude_3_stream(modelId,image_path,max_tokens))
    else:
        print(anthropic_claude_3(modelId,image_path,max_tokens))		

    
if __name__ == '__main__':
    main()
