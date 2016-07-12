from collections import defaultdict
import datetime
import json
import pprint
import sys

import boto3
S3_BUCKET = 'spotprices'

REGION_NAME = 'us-east-1'
client = boto3.client('ec2', region_name=REGION_NAME)
regions = [region['RegionName'] for region in client.describe_regions()['Regions']]

s3_client = boto3.resource('s3', region_name='us-east-1')

pretty_printer = pprint.PrettyPrinter(indent=4)


def print_matches(region_name):
    res = s3_client.Object(S3_BUCKET, '{}.txt'.format(region_name)).get()
    client = boto3.client('ec2', region_name=region_name)

    spot_data = json.loads(res['Body'].read())

    instance_type = spot_data.keys()[0]
    values = spot_data.values()

    matches = {}
    for az, (time, price) in spot_data.values()[0].items():

        from dateutil import parser
        start_time = parser.parse(time + " UTC")
        # start_time = datetime.datetime.strptime(time, "%Y/%m/%d-%H:%M:%S")

        response = client.describe_spot_price_history(
            StartTime=start_time,
            EndTime=start_time + datetime.timedelta(minutes=1),
            InstanceTypes=[instance_type],
            ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
        )
        matching_prices = [x for x in response['SpotPriceHistory'] if x['SpotPrice'] == price]
        try:
            matching_az = matching_prices[0]['AvailabilityZone']
        except IndexError:
            import pdb;pdb.set_trace()
            print "Could not match up AZs", region_name
            sys.exit(1)

        matches[matching_az] = az

    print "Your AZ,", "True AZ"
    pretty_printer.pprint(matches)

def main():
    for region_name in regions:
        print_matches(region_name)

if __name__ == '__main__':
    main()
