import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from helper_functions import * 

ssm_client = boto3.client('ssm')
cfn_client = boto3.client('cloudformation')
s3_client = boto3.client('s3', region_name=config.region)

logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO)

def main():
    args = parse_args()

    # create and tag bucket
    bucket_name = f'tickit-bootstrap-{config.account_id}-{config.region}'
    create_bucket(bucket_name)

    put_ssm_parameter(bucket_name)

    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    upload_file(f'{dir_path}/scripts/bootstrap_actions.sh', bucket_name, 'bootstrap_actions.sh')

    stack_name = f'emr-{args.environment}'
    cfn_template_path = f'{dir_path}/cloudformation/emr.yml'
    cfn_params_path = f'{dir_path}/config/emr_params.json'
    ec2_key_name = args.ec2_key_name
    create_stack(stack_name, cfn_template_path, cfn_params_path, ec2_key_name, bucket_name)

def create_bucket(bucket_name):
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        logging.info(f'New bucket name: {bucket_name}')
    except ClientError as e:
        logging.error(e)

def put_ssm_parameter(bucket_name):
    try:
        response = ssm_client.put_parameter(
            Name='/tickit/bootstrap_bucket',
            Description='Bootstrap scripts bucket',
            Value=bucket_name,
            Type='String',
            Tags=[
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        )
        logging.info(f'Response: {response}')
    except ClientError as e:
        logging.error(e)

def upload_file(file_name, bucket, object_name):
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        logging.info(f'File {file_name} uploaded to bucket {bucket} as object {object_name}')
    except ClientError as e:
        logging.error(e)

def create_stack(stack_name, cfn_template, cfn_params_path, ec2_key_name, bucket_name):
    template_data = _parse_template(cfn_template)
    cfn_params = _parse_parameters(cfn_params_path)
    cfn_params.append({'ParameterKey': 'Ec2KeyName', 'ParameterValue': ec2_key_name})
    cfn_params.append({'ParameterKey': 'BootstrapBucket', 'ParameterValue': bucket_name})

    create_stack_params = {
        'StackName': stack_name,
        'TemplateBody': template_data,
        'Parameters': cfn_params,
        'TimeoutInMinutes': 60,
        'Capabilities': [
            'CAPABILITY_NAMED_IAM',
        ],
        'Tags': [
            {
                'Key': 'Project',
                'Value': 'tickit'
            },
        ]
    }

    try:
        response = cfn_client.create_stack(**create_stack_params)
        logging.info(f'Response: {response}')
    except ClientError as e:
        logging.error(e)

def _parse_template(template):
    with open(template) as template_file_obj:
        template_data = template_file_obj.read()
    cfn_client.validate_template(TemplateBody=template_data)
    return template_data


def _parse_parameters(parameters):
    with open(parameters) as parameter_file_obj:
        cfn_params = json.load(parameter_file_obj)
    return cfn_params


def parse_args():
    """Parse argument values from command-line"""

    parser = argparse.ArgumentParser(description='Arguments required for script.')
    parser.add_argument('-e', '--environment', required=True, choices=['dev', 'test', 'prod'], help='Environment')
    parser.add_argument('-k', '--ec2-key-name', required=True, help='Name of EC2 Keypair')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()