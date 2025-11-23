#!/bin/bash
# Quick start script for AWS infrastructure deployment

set -e

echo "🚀 Newton Demo - AWS Infrastructure Setup"
echo "=========================================="
echo ""
echo "💡 This setup will REUSE Newton's existing VPC infrastructure"
echo "   to save ~\$40/month on networking costs!"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    echo "Install: brew install awscli"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found${NC}"
    echo "Install: brew install terraform"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites installed${NC}"
echo ""

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: $AWS_ACCOUNT${NC}"
echo ""

# Prompt for domain
echo "🌐 Domain Configuration"
read -p "Enter your domain name (e.g., demo.yourdomain.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}❌ Domain name required${NC}"
    exit 1
fi

# Prompt for DB password
echo ""
echo "🔒 Database Configuration"
echo "Generate secure password? (y/n)"
read -p "> " GENERATE_PASSWORD

if [ "$GENERATE_PASSWORD" = "y" ]; then
    DB_PASSWORD=$(openssl rand -base64 32)
    echo -e "${GREEN}✅ Generated secure password${NC}"
else
    read -sp "Enter database password: " DB_PASSWORD
    echo ""
fi

# Create terraform.tfvars
echo ""
echo "📝 Creating Terraform configuration..."
cat > terraform/environments/staging/terraform.tfvars <<EOF
aws_region  = "us-east-1"
environment = "staging"
domain_name = "$DOMAIN_NAME"
db_password = "$DB_PASSWORD"
EOF

echo -e "${GREEN}✅ Configuration created${NC}"
echo ""

# Create S3 bucket for state
echo "🪣 Creating S3 bucket for Terraform state..."
BUCKET_NAME="salesagent-demo-terraform-state-$AWS_ACCOUNT"

if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://$BUCKET_NAME" --region us-east-1
    
    # Enable versioning
    aws s3api put-bucket-versioning \
      --bucket "$BUCKET_NAME" \
      --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
      --bucket "$BUCKET_NAME" \
      --server-side-encryption-configuration '{
        "Rules": [{
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }]
      }'
    
    echo -e "${GREEN}✅ S3 bucket created: $BUCKET_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  Bucket already exists: $BUCKET_NAME${NC}"
fi

# Update backend configuration
sed -i.bak "s/salesagent-demo-terraform-state/$BUCKET_NAME/" terraform/environments/staging/main.tf
rm terraform/environments/staging/main.tf.bak

echo ""

# Initialize Terraform
echo "🏗️  Initializing Terraform..."
cd terraform/environments/staging
terraform init

echo -e "${GREEN}✅ Terraform initialized${NC}"
echo ""

# Plan
echo "📊 Creating infrastructure plan..."
terraform plan -out=tfplan

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review the plan above"
echo "2. Run: cd terraform/environments/staging && terraform apply tfplan"
echo "3. Wait ~15 minutes for infrastructure to create"
echo "4. Follow the AWS_SETUP_GUIDE.md for Phase 3 onwards"
echo ""
echo "📝 Configuration saved to:"
echo "   terraform/environments/staging/terraform.tfvars"
echo ""
echo "🔒 Database password: $DB_PASSWORD"
echo "   (Save this - you'll need it for GitHub secrets!)"
echo ""

