#!/usr/bin/env python3
from datetime import datetime, timedelta
import boto3
import argparse

def get_ec2_list(vpc_id, az_id, status=[], tagkey=None):
    ec2 = boto3.client('ec2')
    filter=[
      {
         'Name': "vpc-id",
         'Values': [vpc_id]
      },
      {
         'Name': 'instance-state-name',
         'Values': status
      },
      {
        'Name': 'availability-zone',
        'Values': [az_id]
      }
    ]
    if tagkey:
        filter.append(
            {
                'Name': 'tag-key',
                'Values': [tagkey]
            }
        )
    paginator = ec2.get_paginator('describe_instances')
    response_iterator = paginator.paginate(Filters=filter)
    instances = []
    for page in response_iterator:
      for res in page['Reservations']:
          instances = instances + res['Instances']
    return instances

def get_rds_list(vpc_id, az_id):
    rds = boto3.client('rds')
    paginator = rds.get_paginator('describe_db_instances')
    response_iterator = paginator.paginate()
    rds_list = []
    for page in response_iterator:
        for db in page['DBInstances']:
            if db['DBSubnetGroup']['VpcId'] == vpc_id:
                if db['AvailabilityZone'] == az_id:
                    if db['MultiAZ'] == True:
                        rds_list.append(db)
    return rds_list

def failover_rds(dbinstance_id):
    rds = boto3.client('rds')
    response = rds.reboot_db_instance(
        DBInstanceIdentifier=dbinstance_id,
        ForceFailover=True
    )

def stop_instance(instance_id):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)
    instance.stop()

def start_instance(instance_id):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)
    instance.start()

def add_stopped_tag(instance_id, tagkey):
    ec2 = boto3.client('ec2')
    ec2.create_tags(
        Resources=[
            instance_id,
        ],
        Tags=[
            {
                'Key': tagkey,
                'Value': 'yes'
            },
        ]
    )

def remove_stopped_tag(instance_id, tagkey):
    ec2 = boto3.client('ec2')
    ec2.delete_tags(
        Resources=[
            instance_id,
        ],
        Tags=[
            {
                'Key': tagkey,
                'Value': 'yes'
            },
        ]
    )

def get_args():
    parser = argparse.ArgumentParser(description='Simulate an AWS AZ fail')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--restore', action="store_true",
        help="Restart the instances stopped by this script")
    group.add_argument('-d', '--destroy', action="store_true",
        help="Force a fail of an Availability Zone (Default)")
    parser.add_argument('-n', '--vpcid', type=str, required=True,
        help="VPC ID")
    parser.add_argument('-a', '--azid', type=str, required=True,
        help="Availability Zone ID")
    parser.add_argument('-b', '--rdsid', type=str,
        help="Comma separated list of RDS IDs. Use this argument if you want \
        to limit the failover to specific RDS")
    parser.add_argument('--dry', action="store_true", help="Dry run")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()

    AZ = args.azid
    VPC = args.vpcid
    RDS = args.rdsid
    STOPPED_TAG = "stoppedByHAtest"
    DRY = args.dry

    if args.restore:
        print (f"Restarting the instances in the AZ {AZ}")
        ec2_list = get_ec2_list(VPC, AZ, ['stopped'], STOPPED_TAG)
        # start the instances stopped by this script previously
        for instance in ec2_list:
            instance_id = instance['InstanceId']
            print(f"Starting the instance {instance_id}")
            if not DRY:
                start_instance(instance_id)
            print(f"Removing stopped tag for instance {instance_id}")
            if not DRY:
                remove_stopped_tag(instance_id, STOPPED_TAG)
    else:
        print (f"Simulating the down of the AZ {AZ}")
        ec2_list = get_ec2_list(VPC, AZ, ['running', 'pending'])
        if not RDS:
            rds_list = get_rds_list(VPC, AZ)
            # Force failover of all rds in the given vpc/AZ
            for rds in rds_list:
                rds_id = rds['DBInstanceIdentifier']
                print(f"Triggering a Failover of the rds {rds_id}")
                if not DRY:
                    failover_rds(rds_id)
        else:
            for rds_id in RDS.split(","):
                print(f"Triggering a Failover of the rds {rds_id}")
                failover_rds(rds_id)
        # stop all instances in the given vpc/AZ
        for instance in ec2_list:
            instance_id = instance['InstanceId']
            print(f"Stopping the instance {instance_id}")
            if not DRY:
                stop_instance(instance_id)
            print(f"Adding stopped tag for instance {instance_id}")
            if not DRY:
                add_stopped_tag(instance_id, STOPPED_TAG)
