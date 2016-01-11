# cfnplan
cfnplan (CloudFormation Plan) is a simple tool to help you plan for AWS CloudFormation stack updates. It's inspired
by the (awesome) [terraform](https://terraform.io/) plan mode.

[![Build Status](https://travis-ci.org/zsims/cfnplan.svg?branch=master)](https://travis-ci.org/zsims/cfnplan)
[![PyPI version](https://badge.fury.io/py/cfnplan.svg)](https://badge.fury.io/py/cfnplan)

## Goal
The goal of cfnplan is to:

 1. Avoid having to read your CloudFormation template to work out resource dependencies
 2. Avoid having to apply the "update" vs "replace" rules manually, which you need to [read the docs to learn](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks.html)

# Install
cfnplan is available via PyPi:
```
$ pip install cfnplan
```

# Example
Currently cfnplan only lists dependencies between parameters, mappings, outputs, conditions and resources, an example of the AWS "[WordPress scalable and durable](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/sample-templates-applications-ap-southeast-2.html)" template:

```
$ cfnplan describe "tests/templates/WordPress_Multi_AZ.template"
DBSecurityGroup (AWS::RDS::DBSecurityGroup)
  <== AWS::Region
  <== SSHLocation
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
  <== Is-EC2-Classic
  <== Is-EC2-VPC
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
WebServerSecurityGroup (AWS::EC2::SecurityGroup)
  <== SSHLocation
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)

# ... snip ...
```

Or with the full dependency tree:
```
$ cfnplan describe "tests/templates/WordPress_Multi_AZ.template" --verbose
DBSecurityGroup (AWS::RDS::DBSecurityGroup)
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
    <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
    <== SSHLocation
  <== SSHLocation
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
  <== Is-EC2-VPC
    <== AWS::Region
  <== Is-EC2-Classic
    <== Is-EC2-VPC
      <== AWS::Region
    <== AWS::Region
  <== AWS::Region
WebServerSecurityGroup (AWS::EC2::SecurityGroup)
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
  <== SSHLocation

# ... snip ...
```

