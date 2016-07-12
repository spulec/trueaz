from collections import defaultdict
import datetime
import json

import boto3
S3_BUCKET = 'spotprices'

INSTANCE_TYPES = [
    't1.micro', 't2.nano', 't2.micro', 't2.small', 't2.medium', 't2.large',
    'm1.small', 'm1.medium', 'm1.large', 'm1.xlarge', 'm3.medium',
    'm3.large', 'm3.xlarge', 'm3.2xlarge', 'm4.large', 'm4.xlarge',
    'm4.2xlarge', 'm4.4xlarge', 'm4.10xlarge', 'm2.xlarge', 'm2.2xlarge',
    'm2.4xlarge', 'cr1.8xlarge', 'r3.large', 'r3.xlarge', 'r3.2xlarge',
    'r3.4xlarge', 'r3.8xlarge', 'x1.4xlarge', 'x1.8xlarge', 'x1.16xlarge',
    'x1.32xlarge', 'i2.xlarge', 'i2.2xlarge', 'i2.4xlarge', 'i2.8xlarge',
    'hi1.4xlarge', 'hs1.8xlarge', 'c1.medium', 'c1.xlarge', 'c3.large',
    'c3.xlarge', 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge', 'c4.large',
    'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge', 'c4.8xlarge', 'cc1.4xlarge',
    'cc2.8xlarge', 'g2.2xlarge', 'g2.8xlarge', 'cg1.4xlarge', 'd2.xlarge',
    'd2.2xlarge', 'd2.4xlarge', 'd2.8xlarge',
]

REGION_NAME = 'us-east-1'
client = boto3.client('ec2', region_name=REGION_NAME)

regions = [region['RegionName'] for region in client.describe_regions()['Regions']]

s3_client = boto3.resource('s3', region_name='us-east-1')


def find_distinct_prices(region_name):
    client = boto3.client('ec2', region_name=region_name)

    zones = client.describe_availability_zones()
    zone_names = [x['ZoneName'] for x in zones['AvailabilityZones']]

    for instance_type in INSTANCE_TYPES:
        mapping = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))
        response = client.describe_spot_price_history(
            StartTime=datetime.datetime.today() - datetime.timedelta(days=30),
            EndTime=datetime.datetime.today() - datetime.timedelta(hours=1),
            InstanceTypes=[instance_type],
            ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
        )
        for result in response['SpotPriceHistory']:
            time = result['Timestamp'].strftime("%Y/%m/%d-%H:%M:%S")
            mapping[result['AvailabilityZone']] = time, result['SpotPrice']

            if len(mapping) == len(zone_names):
                # This means they are all unique
                return {
                    instance_type: dict(mapping)
                }

import datetime
def lambda_handler(event, context):
    for region_name in regions:
        print datetime.datetime.now()
        print "Checking", region_name
        prices = find_distinct_prices(region_name)
        print prices
        filename = '{}.txt'.format(region_name)
        obj = s3_client.Object(S3_BUCKET, filename)
        obj.put(Body=json.dumps(prices))
        obj.Acl().put(ACL='public-read')

if __name__ == '__main__':
    lambda_handler({}, {})
