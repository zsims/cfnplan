# cfnplan
cfnplan (CloudFormation Plan) is a simple tool to help you plan for AWS CloudFormation stack updates. It's inspired
by the (awesome) [terraform](https://terraform.io/) plan mode.

## Goal
The goal of cfnplan is to:

 1. Avoid having to read your CloudFormation template to work out resource dependencies
 2. Avoid having to apply the "update" vs "replace" rules manually, which you need to [read the docs to learn](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks.html)

## Example
Currently cfnplan only lists dependencies for parameters and resources, an example of the AWS "[WordPress scalable and durable](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/sample-templates-applications-ap-southeast-2.html)" template:

```
$ python.exe scripts/cfnplan.py -d "tests/templates/WordPress_Multi_AZ.template"
<== AWS::AccountId
<== AWS::NotificationARNs
<== AWS::NoValue
<== AWS::Region
<== AWS::StackId
<== AWS::StackName
<== DBClass
<== DBAllocatedStorage
<== DBName
<== SSHLocation
<== KeyName
<== DBPassword
<== DBUser
<== MultiAZDatabase
<== InstanceType
<== WebServerCapacity
<== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
    <== SSHLocation
    <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
  <== SSHLocation
  <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== WebServerGroup (AWS::AutoScaling::AutoScalingGroup)
  <== WebServerCapacity
  <== LaunchConfig (AWS::AutoScaling::LaunchConfiguration)
    <== AWS::StackName
    <== DBName
    <== DBInstance (AWS::RDS::DBInstance)
      <== DBAllocatedStorage
      <== DBPassword
      <== DBUser
      <== MultiAZDatabase
      <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
        <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
          <== SSHLocation
          <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
      <== AWS::NoValue
      <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
      <== DBClass
    <== KeyName
    <== InstanceType
    <== AWS::Region
    <== AWS::StackId
<== LaunchConfig (AWS::AutoScaling::LaunchConfiguration)
  <== AWS::StackName
  <== DBName
  <== DBInstance (AWS::RDS::DBInstance)
    <== DBAllocatedStorage
    <== DBPassword
    <== DBUser
    <== MultiAZDatabase
    <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
      <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
        <== SSHLocation
        <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
    <== AWS::NoValue
    <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
    <== DBClass
  <== KeyName
  <== InstanceType
  <== AWS::Region
  <== AWS::StackId
<== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
  <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
    <== SSHLocation
    <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
<== DBInstance (AWS::RDS::DBInstance)
  <== DBAllocatedStorage
  <== DBName
  <== DBPassword
  <== DBUser
  <== MultiAZDatabase
  <== DBSecurityGroup (AWS::RDS::DBSecurityGroup)
    <== WebServerSecurityGroup (AWS::EC2::SecurityGroup)
      <== SSHLocation
      <== ElasticLoadBalancer (AWS::ElasticLoadBalancing::LoadBalancer)
  <== AWS::NoValue
  <== DBEC2SecurityGroup (AWS::EC2::SecurityGroup)
  <== DBClass
```

