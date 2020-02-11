# simulate_aws_az_down
Simple script that aim to test the HA support of application deploy in AWS EC2

## Requirements

boto3

## Help

```
usage: aws-ha-test.py [-h] [-r | -d] -n VPCID -a AZID [--dry]

Simulate an AWS AZ fail

optional arguments:
  -h, --help            show this help message and exit
  -r, --restore         Restart the instances stopped by this script
  -d, --destroy         Force a fail of an Availability Zone (Default)
  -n VPCID, --vpcid VPCID
                        VPC ID
  -a AZID, --azid AZID  Availability Zone ID
  --dry                 Dry run
```

## Usage examples

### Simulate the down of eu-west-1a

It force a failover of all RDS and it stops all EC2 instances in that (vpc, AZ).

```
AWS_REGION=eu-west-1
AWS_PROFILE=myawsprofile
python3 aws-ha-test.py --destroy --vpcid vpc-c9ee2dad --azid eu-west-1a
```


### Recover instances from eu-west-1a 

Basically it restarts all instances that had been previously stopped by this script.

```
AWS_REGION=eu-west-1
AWS_PROFILE=myawsprofile
python3 aws-ha-test.py --restore --vpcid vpc-c9ee2dad --azid eu-west-1a
```
