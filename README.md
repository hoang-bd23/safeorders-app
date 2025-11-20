# SafeOrders Application

Flask-based order management system for the SafeOrders food delivery platform.

## Features

- RESTful API for order management
- Web UI for viewing orders
- Health check endpoint
- Automatic logging to S3
- Environment-aware configuration (dev/prod)

## API Endpoints

### Health Check
```bash
GET /health
```

Returns application health status and configuration.

### Get All Orders
```bash
GET /orders
```

Returns list of all orders with statistics.

### Create Order
```bash
POST /orders
Content-Type: application/json

{
  "customer": "John Doe",
  "item": "Pizza",
  "status": "pending"
}
```

Creates a new order and logs to S3.

### Get Specific Order
```bash
GET /orders/<id>
```

Returns details for a specific order.

## Local Development

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
APP_ENV=dev
S3_LOG_BUCKET=your-log-bucket-name
AWS_REGION=ap-southeast-1
EOF

# Run application
python app.py
```

Application will be available at `http://localhost:8080`

## Deployment to EC2 (Manual)

### Prerequisites

From Terraform outputs, get:
- `log_bucket_name`
- `app_private_ip`
- `bastion_public_ip` (dev only)

### Steps

1. **SSH to bastion (dev) or directly to app (if accessible)**

```bash
ssh -i your-key.pem ec2-user@<bastion_ip>
ssh ec2-user@<app_private_ip>
```

2. **Install dependencies**

```bash
sudo yum update -y
sudo yum install -y python3 git
```

3. **Clone and setup application**

```bash
sudo mkdir -p /srv/safeorders
sudo chown ec2-user:ec2-user /srv/safeorders
cd /srv/safeorders

# Clone (or copy) application files
git clone <your-repo> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cat > .env << EOF
APP_ENV=dev  # or prod
S3_LOG_BUCKET=<log_bucket_name_from_terraform_output>
AWS_REGION=ap-southeast-1
EOF
```

5. **Test application**

```bash
python app.py
# Test: curl http://localhost:8080/health
```

6. **Setup systemd service**

```bash
sudo cp safeorders.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable safeorders
sudo systemctl start safeorders
sudo systemctl status safeorders
```

7. **Verify through ALB**

```bash
# From your local machine
curl http://<alb_dns_name>/health
curl http://<alb_dns_name>/orders

# Test order creation
curl -X POST http://<alb_dns_name>/orders \
  -H "Content-Type: application/json" \
  -d '{"customer":"Test User","item":"Sushi"}'
```

8. **Check S3 logs**

```bash
# From AWS CLI or Console
aws s3 ls s3://<log_bucket_name>/orders/dev/
```

## Configuration

### Environment Variables

- `APP_ENV`: Environment name (dev/prod)
- `S3_LOG_BUCKET`: S3 bucket for logs
- `AWS_REGION`: AWS region

### IAM Requirements

EC2 instance must have IAM role with permissions:
- `s3:PutObject` on log bucket
- `s3:GetObject` on log bucket
- `s3:ListBucket` on log bucket

(This is handled by Terraform IAM module)

## Logs

Application logs to multiple locations:
- Console output: `journalctl -u safeorders -f`
- Access logs: `/var/log/safeorders-access.log`
- Error logs: `/var/log/safeorders-error.log`
- S3 logs: `s3://<bucket>/orders/<env>/`

## Troubleshooting

### Service not starting

```bash
sudo systemctl status safeorders
sudo journalctl -u safeorders -n 50
```

### Port already in use

```bash
sudo netstat -tlnp | grep 8080
```

### S3 permission errors

Verify IAM role attached to EC2 instance:
```bash
curl http://169.254.169.254/latest/meta-data/iam/info
```

### Health check failing

```bash
curl http://localhost:8080/health
# Check ALB target group health in AWS Console
```

## Architecture

```
Internet -> ALB -> App EC2 (private subnet) -> S3 (logs)
```

- App runs on port 8080
- ALB forwards traffic from port 80 to 8080
- App writes JSON logs to S3 on each order creation
- Health check at `/health` for ALB monitoring

## Next Steps (Phase 5)

- CI/CD pipeline for automated deployment
- Auto Scaling Groups
- Multi-AZ deployment
- CloudWatch monitoring
- SNS notifications

## License

Training project for DevOps learning.
