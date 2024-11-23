# Project Name: MoonActive Odd Application with CI/CD Pipeline

## Description
This project automates the CI/CD process for a Flask application using GitHub Actions, AWS ECR, Helm, and AWS EKS. The pipeline includes automated linting with `pylint`, building and pushing Docker images to ECR, running tests of the application endpoints, and deploying the application to AWS EKS using Helm. Prometheus and Grafana are also set up for monitoring and observability using helm.

## Table of Contents
- [Prerequisites](#prerequisites)
- [AWS Setup](#aws-setup)
  - [Create EKS Cluster](#create-eks-cluster)
  - [Create IAM Roles and Policies](#create-iam-roles-and-policies)
  - [Create an IAM OIDC provider for your cluster](#create-an-iam-oidc-provider-for-your-cluster) 
  - [Install AWS Load Balancer Controller](#install-aws-load-balancer-controller)
  - [Install EBS CSI controller for your cluster](#install-ebs-csi-controller-for-your-cluster) 
  - [Set up Prometheus and Grafana](#set-up-prometheus-and-grafana)
- [GitHub Actions Workflow](#github-actions-workflow)
- [Accessing the Application](#accessing-the-application)
  - [Port Forwarding](#port-forwarding)
  - [Using Ingress](#using-ingress)
- [Deployment](#deployment)

## Prerequisites

Ensure you have the following setup before running the pipeline:
- **AWS Account** with necessary permissions to create EKS, IAM roles, ECR, VPC.
- **kubectl**: Command-line tool to interact with the Kubernetes cluster.
- **GitHub Account**: For the GitHub Actions CI/CD pipeline.

## AWS Setup

### Create EKS Cluster

To create an EKS cluster, follow these steps:
1. **Create VPC**: Ensure you have a VPC configured with subnets for both public and private access, if you will use ALB make sure to add `kubernetes.io/role/internal-elb = 1` for the private subnets and `kubernetes.io/cluster/my-cluster = shared` `kubernetes.io/role/elb = 1` for the public subnets to let the ALB find and use these subnets.
2. **Create EKS Cluster**:
   - Use AWS Management Console or AWS CLI to create an EKS cluster.
   - Example using AWS CLI:
     ```bash
     aws eks create-cluster --name my-cluster --role-arn arn:aws:iam::123456789012:role/EKSClusterRole --resources-vpc-config subnetIds=subnet-12345,subnet-67890,securityGroupIds=sg-012345
     ```
   - After creating the cluster, update your kubeconfig:
     ```bash
     aws eks update-kubeconfig --name my-cluster --region your-region
     ```
Or use the aws console, make sure to add IAM access entries for the github runner role to be able to deploy the helm of the application, and to add the assumed role for your user to access the cluster as well
For this project Ive used 1 nodegroup containing 3 ec2 machines due to the capacity of ip`s that each machine can assign vs my workload (ALB controller and promethus and grafana number of pods)
### Create IAM Roles and Policies

Ensure you have the necessary IAM roles and policies for EKS and AWS services. These roles include permissions for creating and managing resources like ECR and EKS clusters, as well as for interacting with the Kubernetes cluster.

1. **Create IAM Role for EKS Worker Nodes**:
   - Attach the `AmazonEKSWorkerNodePolicy`, `AmazonEC2ContainerRegistryReadOnly`, and `AmazonEKS_CNI_Policy` policies.
   - Use the AWS Management Console or AWS CLI to create the role.

2. **Create IAM Role for GitHub Actions**:
   - Create an IAM role that GitHub Actions can assume, allowing it to deploy to EKS, push images to ECR, any other if needed.
   - Attach the following policies to this role:
     - `AmazonECRFullAccess`
     - `AmazonEKSWorkerNodePolicy`
     - `AmazonEC2ContainerRegistryPowerUser`
     - `AmazonEKSClusterPolicy`

### Create an IAM OIDC provider for your cluster 
To be able to connect GitHub actions and other resources to your cluster you must create an IAM OIDC(openID Connect)
this can be able to achieve using the console or the cli
```https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html```

### Install AWS Load Balancer Controller
Once you have OIDC installed you can proceed to this step
To manage ingress resources, you need to install the AWS Load Balancer Controller on your EKS cluster.

1. Install using Helm:
First create IAM Role using eksctl (replace cluster name and the AccoundID with the correct values, also make sure you have the policy which can be downloaded from here `curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json`
```$ eksctl create iamserviceaccount \
  --cluster=my-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::111122223333:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```
   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm repo update
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     --set clusterName=my-cluster \
     --set serviceAccount.create=false \
     --set serviceAccount.name=aws-load-balancer-controller \
     --namespace kube-system
verify that the controller has been installed `kubectl get deployment -n kube-system aws-load-balancer-controller`

### Install EBS CSI controller for your cluster
The EBS CSI is an addon that can be added to the eks cluster, dont forget to add a IAM role so that the CSI plugin will be able to make AWS API calls on your behalf
```https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html```
Create an IAM role and attach it to the cluster(we will be using eksctl) Make sure to change the cluster name with your cluster name
```eksctl create iamserviceaccount \
        --name ebs-csi-controller-sa \
        --namespace kube-system \
        --cluster my-cluster \
        --role-name AmazonEKS_EBS_CSI_DriverRole \
        --role-only \
        --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
        --approve
```
### Set up Prometheus and Grafana
For that step I have used prometheus grafana stack which comes with an grafana stack embeded which consists of several components
Prometheus - To scape metrics from multiple sources
Alertmanager - To handle alerts from prometheus and send notifications
Grafana - To visualize the metrics with dashboards
Kube-state-metrics and Node Exporter - To provide metrics of pods and nodes in the cluster
Metrics Server - To provide resource usage metrics (like HPA)

```helm install stable prometheus-community/kube-prometheus-stack -n monitoring --create-namespace```

To access the grafana Ive used port-forward, If you have a DNS provider you can access it via the ingress, but will need to change the values in the values file to ingress true and the host name.
1. get the password for first login ```kubectl get secret --namespace prometheus stable-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo```
2. user name is admin by default

For this exercise Ive used a imported dashboard by the number 15760, Because the stack comes imbedded your prometheus stream is already configured, but other wise you should first go to the data Source -> Add new connection -> Prometheus -> Insert promethus server URL

##### Insert image here of Dashboard

### GitHub Actions Workflow
In this project ive used github secrets to save the following secrets to run the github actions workflow:
AWS_REGION, AWS_ROLE_TO_ASSUME, EKS_CLUSTER_NAME, REPOSITORY.

The CI/CD pipeline is automated using GitHub Actions. When a commit is pushed to the main branch, the following steps occur:
1. Runs pylint on the Python code to ensure code quality.
2. The application is built into a Docker image.
3. The application is tested for enpoints using pytest.
4. The application is pushed to ECR.
5. The application is deployed to EKS using Helm with the new tags.

### Accessing the Application
### Using Ingress
If you have a DNS provider you can access it using the ingress, just change the host: to your host name, you also need to point the traffic from the provider to the ALB dns name.

### Using Port Forwarding

Login to the cluster ```aws eks --region your-cluster-region update-kubeconfig --name cluster-name``` if not configured already
To access the application locally you can use portforwarding ```kubectl port-forward -n moonactive svc/moonactive-service 8090:80``` (it will forward the traffic to port 5000 inside the container)
Then you are able to access the container locally on localhost:8090/ready or any other endpoint 

### Deployment
The deployment is using helm, it changes the tag to the build number and creates the namespace if it doesnt already exists
You need to make sure that the github runner has access to the eks cluster with the correct roles.

The deployment consist of the following:
1. HPA that scales based on cpu and memory utilization and can scale up to 5 pods (can be modified)
2. Ingress resource for the application
3. Service
4. Deployment with 2 containers:
   1. The first container contains the app itself
   2. The second container consists of the following logic: If the file odd-logs.txt exists on the container it will be created and tail that file to stdout, It has a liveness probe that will restart that container if the file gets deleted, and will recreate only if the file will be creatd again
      To achive that we need to mount a volume (For this purpose ive used emprtyDir that lives only as long as the pods lives) and mounted both pods to the same dir
   3. Rolling update with 0 maxUnavaiable to be as resiliant as possible during updates 
      


