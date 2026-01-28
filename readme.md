# AWS Bedrock 演示和工具集

本仓库包含AWS Bedrock相关的演示代码和实用工具。

## 📂 项目结构

### 🚀 [bedrock_stress_test/](bedrock_stress_test/) - Bedrock大模型性能测试工具
一个专业的性能测试工具，用于测量AWS Bedrock上大语言模型的TTFT（Time To First Token）和吞吐量。

**主要特性**：
- ✅ 支持多模型：DeepSeek V3、MiniMax M2
- ✅ 多梯度上下文测试：8K/32K/64K/128K/256K/360K
- ✅ 统计分析：P50/P95/P99等性能指标
- ✅ RAG场景模拟：真实的文档检索场景测试

**快速开始**：
```bash
cd bedrock_stress_test
pip install -r requirements.txt
python cli.py --mode quick --model deepseek --user "你好"
```

详细文档见：[bedrock_stress_test/README.md](bedrock_stress_test/README.md)

---

### 📚 其他示例

#### 使用boto3时的aws权限获取

boto3的权限获取，如果不是根据当前环境中通过awscli已经配置好的profile，就需要在代码里调用sts服务来获取临时的aksk。
本文通过bedrcok里调用大模型的例子来解释这个过程。


### 在aws控制台创建一个IAM角色

这个角色用来给之前创建的用户扮演，这个扮演的过程是在python的脚本里通过boto3支持的STS服务来完成，具体过程在代码里有注释，这里只说明创建的角色应该被赋予的基本权限。过程如下：

1. 在IAM控制台找到Roles菜单，点击右上角的‘Create role'

![Image1](screenshots/Screenshot%202024-04-19%20at%2009.50.21.png)
2. 设定这个role的扮演者是本账号的用户

![Image2](screenshots/Screenshot%202024-04-19%20at%2009.50.35.png)
3. 给这个角色设定权限，这里是给了Bedrock的full access

![Image3](screenshots/Screenshot%202024-04-19%20at%2010.23.17.png)
从最佳实践的角度出发，如果只需要角色可以调用模型，请创建如下最小权限的Policy并赋予角色：

```
{
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "bedrock",
        "Effect": "Allow",
        "Action": [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream"
        ],
        "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
}
```

4. 保证该角色的信任对象是本账户的用户：

![Image4](screenshots/Screenshot%202024-04-19%20at%2009.51.56.png)
5. 然后就可以给角色起名字，并完成创建。创建之后角色会有一个ARN，会在代码的部分需要：

![Image5](screenshots/Screenshot%202024-04-19%20at%2009.57.35.png)
### 在aws控制台创建一个IAM用户

具体如下图，需要用户具备一个基本的能力：扮演上面那个特定的角色，对应的policy设置如下：
![Image6](screenshots/Screenshot%202024-04-19%20at%2010.30.35.png)
同时，为该用户创建一个AKSK，并妥善保存：
![Image7](screenshots/Screenshot%202024-04-19%20at%2009.46.33.png)

### 配置Python代码text_inference_claude3.py: 文本推理

```
#!/usr/bin/python3
import boto3
import json
#from prompts import PROMPTS

ASSUME_ROLE = True #可以设置True or False来决定在脚本内部扮演角色还是用脚本外部的aws configure环境
STREAM_ENABLED = False #可以设置True or False来决定是否启动流方式输出
REGION = 'us-east-1' #设定要使用的Region

# Assume role to get keys and token, the aksk is from a user called: bedrock_caller
def assume_role():
    sts_client = boto3.client(
        service_name = 'sts',
        aws_access_key_id='xxxxxxxxxx',#这里的Key就是你创建的IAM用户的Key
        aws_secret_access_key='xxxxxxxxxxx',#这里的Key就是你创建的IAM用户的secret
        region_name = REGION
    )
    print("Your current caller identity(user/role):")
    current_caller_identity = sts_client.get_caller_identity()
    print("Account:", current_caller_identity['Account'], "Arn:", current_caller_identity['Arn'])

    assumed_role_object = sts_client.assume_role(
        RoleArn="arn:aws:iam::8xxxxxxxxx:role/bedrock_full_access_role_for_iam_user_to_assume",#这里的ARN就是你创建的IAM角色的ARN
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
            region_name=REGION
        )
    else:
        bedrock = boto3.client('bedrock-runtime', region_name=REGION)

    modelId = 'anthropic.claude-3-sonnet-20240229-v1:0' #可以根据需要设定不同的modelID，但是注意claude3的opus目前只在us-west-2可用
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
```

启动角色扮演的执行过程如下：
![Image8](screenshots/Screenshot%202024-04-19%20at%2010.08.33.png)
直接使用环境里的aws configure的profile的执行过程如下：
![Image9](screenshots/Screenshot%202024-04-19%20at%2010.10.18.png)
### 配置Python代码pics_inference_claude3.py: 图片多模态推理

```
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
```



