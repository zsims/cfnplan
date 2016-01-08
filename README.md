# cfnplan
cfnplan (CloudFormation Plan) is a simple tool to help you plan for AWS CloudFormation stack updates. It's inspired
by the (awesome) [terraform](https://terraform.io/) plan mode.

[![Build Status](https://travis-ci.org/zsims/cfnplan.svg?branch=master)](https://travis-ci.org/zsims/cfnplan)

## Goal
The goal of cfnplan is to:

 1. Avoid having to read your CloudFormation template to work out resource dependencies
 2. Avoid having to apply the "update" vs "replace" rules manually, which you need to [read the docs to learn](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks.html)

## Example
Currently cfnplan only lists dependencies between parameters, mappings, outputs, conditions and resources, an example of the AWS "[WordPress scalable and durable](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/sample-templates-applications-ap-southeast-2.html)" template:

```
$ cfnplan describe "tests/templates/WordPress_Multi_AZ.template"
<== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
    <== SSHLocation
    <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
  <== Is-EC2-Classic
    <== Is-EC2-VPC
      <== AWS::Region
<== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
  <== SSHLocation
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== WebServerGroup (AWS::AutoScaling::AutoScalingGroup)
  <== LaunchConfig (AWS::AutoScaling::LaunchConfiguration)
    <== AWS::Region
    <== AWS::StackId
    <== AWS::StackName
    <== DBName
    <== KeyName
    <== DBPassword
    <== DBUser
    <== InstanceType
    <== DBInstance (AWS::RDS::DBInstance)
      <== Is-EC2-VPC
      <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
        <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
          <== SSHLocation
          <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
        <== Is-EC2-Classic
      <== DBAllocatedStorage
      <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
      <== MultiAZDatabase
      <== DBClass
      <== AWS::NoValue
  <== WebServerCapacity
<== LaunchConfig (AWS::AutoScaling::LaunchConfiguration)
  <== AWS::Region
  <== AWS::StackId
  <== AWS::StackName
  <== DBName
  <== KeyName
  <== DBPassword
  <== DBUser
  <== InstanceType
  <== DBInstance (AWS::RDS::DBInstance)
    <== Is-EC2-VPC
    <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
      <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
        <== SSHLocation
        <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
      <== Is-EC2-Classic
    <== DBAllocatedStorage
    <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
    <== MultiAZDatabase
    <== DBClass
    <== AWS::NoValue
<== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
  <== Is-EC2-VPC
    <== AWS::Region
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
    <== SSHLocation
    <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== DBInstance (AWS::RDS::DBInstance)
  <== Is-EC2-VPC
    <== AWS::Region
  <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
    <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
      <== SSHLocation
      <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
    <== Is-EC2-Classic
  <== DBAllocatedStorage
  <== DBName
  <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
  <== DBPassword
  <== DBUser
  <== MultiAZDatabase
  <== DBClass
  <== AWS::NoValue
```

