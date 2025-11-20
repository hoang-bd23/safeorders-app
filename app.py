"""
SafeOrders - Order Management API
Flask application for managing food orders
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)

# Configuration
APP_ENV = os.getenv('APP_ENV', 'dev')
S3_LOG_BUCKET = os.getenv('S3_LOG_BUCKET', '')
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-1')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# S3 client
s3_client = boto3.client('s3', region_name=AWS_REGION) if S3_LOG_BUCKET else None

# In-memory order storage (demo)
orders = [
    {'id': 1, 'customer': 'John Doe', 'item': 'Pizza', 'status': 'delivered', 'timestamp': '2025-11-18T10:00:00'},
    {'id': 2, 'customer': 'Jane Smith', 'item': 'Burger', 'status': 'pending', 'timestamp': '2025-11-18T11:30:00'},
    {'id': 3, 'customer': 'Bob Wilson', 'item': 'Salad', 'status': 'preparing', 'timestamp': '2025-11-18T12:15:00'}
]
next_id = 4


def log_to_s3(log_data):
    """Write log data to S3 bucket"""
    if not s3_client or not S3_LOG_BUCKET:
        logger.warning("S3 logging not configured")
        return False
    
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        key = f"orders/{APP_ENV}/{timestamp}_{log_data.get('order_id', 'unknown')}.json"
        
        s3_client.put_object(
            Bucket=S3_LOG_BUCKET,
            Key=key,
            Body=json.dumps(log_data, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Logged to S3: s3://{S3_LOG_BUCKET}/{key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to log to S3: {e}")
        return False


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'environment': APP_ENV,
        's3_logging': S3_LOG_BUCKET != '',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/')
def index():
    """Web UI for viewing orders"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SafeOrders - {{ env }}</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            .header h1 { margin: 0; }
            .env-badge {
                display: inline-block;
                padding: 5px 15px;
                background: rgba(255,255,255,0.2);
                border-radius: 20px;
                font-size: 14px;
                margin-left: 10px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stat-card h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; }
            .stat-card .value { font-size: 32px; font-weight: bold; color: #667eea; }
            table {
                width: 100%;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            th, td { padding: 15px; text-align: left; }
            th { background: #667eea; color: white; }
            tr:nth-child(even) { background: #f9f9f9; }
            .status {
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-pending { background: #ffd700; color: #333; }
            .status-preparing { background: #87ceeb; color: #333; }
            .status-delivered { background: #90ee90; color: #333; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🍕 SafeOrders <span class="env-badge">{{ env|upper }}</span></h1>
            <p>Order Management System</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>TOTAL ORDERS</h3>
                <div class="value">{{ total }}</div>
            </div>
            <div class="stat-card">
                <h3>PENDING</h3>
                <div class="value">{{ pending }}</div>
            </div>
            <div class="stat-card">
                <h3>PREPARING</h3>
                <div class="value">{{ preparing }}</div>
            </div>
            <div class="stat-card">
                <h3>DELIVERED</h3>
                <div class="value">{{ delivered }}</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Item</th>
                    <th>Status</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                {% for order in orders %}
                <tr>
                    <td>{{ order.id }}</td>
                    <td>{{ order.customer }}</td>
                    <td>{{ order.item }}</td>
                    <td><span class="status status-{{ order.status }}">{{ order.status|upper }}</span></td>
                    <td>{{ order.timestamp }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    
    stats = {
        'total': len(orders),
        'pending': len([o for o in orders if o['status'] == 'pending']),
        'preparing': len([o for o in orders if o['status'] == 'preparing']),
        'delivered': len([o for o in orders if o['status'] == 'delivered'])
    }
    
    return render_template_string(html, orders=orders, env=APP_ENV, **stats)


@app.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    return jsonify({
        'success': True,
        'count': len(orders),
        'orders': orders,
        'environment': APP_ENV
    })


@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    global next_id
    
    data = request.get_json()
    
    if not data or 'customer' not in data or 'item' not in data:
        return jsonify({'success': False, 'error': 'Missing customer or item'}), 400
    
    new_order = {
        'id': next_id,
        'customer': data['customer'],
        'item': data['item'],
        'status': data.get('status', 'pending'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    orders.append(new_order)
    next_id += 1
    
    # Log to S3
    log_data = {
        'event': 'order_created',
        'environment': APP_ENV,
        'order_id': new_order['id'],
        'order': new_order,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    log_to_s3(log_data)
    logger.info(f"Created order: {new_order['id']}")
    
    return jsonify({
        'success': True,
        'order': new_order
    }), 201


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order"""
    order = next((o for o in orders if o['id'] == order_id), None)
    
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'order': order
    })


if __name__ == '__main__':
    logger.info(f"Starting SafeOrders in {APP_ENV} environment")
    logger.info(f"S3 Logging: {'Enabled' if S3_LOG_BUCKET else 'Disabled'}")
    app.run(host='0.0.0.0', port=8080, debug=(APP_ENV == 'dev'))
