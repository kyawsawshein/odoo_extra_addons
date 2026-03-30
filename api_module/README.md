# API Integration Module for Odoo 19

This module provides integration with external API for syncing contacts and products between Odoo and an external system. It includes automatic cron jobs for regular data synchronization.

## Features

- **API Configuration Management**: Configure multiple API endpoints with authentication
- **Contact Synchronization**: Sync contacts from external API to Odoo
- **Product Synchronization**: Sync products from external API to Odoo  
- **Automatic Cron Jobs**: Scheduled sync operations
- **Job History**: Track all sync operations with detailed logs
- **REST API Endpoints**: Manual sync triggers via API
- **User Interface**: Easy-to-use configuration and monitoring interface

## Installation

1. Copy the `api_module` folder to your Odoo `extra_addons` directory
2. Install the module through Odoo Apps or using the command line:
   ```bash
   odoo-bin -d your_database -i api_module --addons-path=./extra_addons
   ```

## Configuration

### 1. Create API Configuration

1. Go to **API Integration > Configuration > API Configurations**
2. Click **Create**
3. Fill in the configuration details:
   - **Name**: Descriptive name for the configuration
   - **API Base URL**: Base URL of your external API (e.g., `http://localhost:8000`)
   - **Authentication URL**: URL for token authentication (e.g., `http://localhost:8000/api/v1/auth/token`)
   - **GraphQL URL**: URL for GraphQL endpoint (e.g., `http://localhost:8000/graphql`)
   - **Username**: API username
   - **Password**: API password
   - **Sync Contacts**: Enable/disable contact synchronization
   - **Sync Products**: Enable/disable product synchronization
   - **Sync Interval**: Interval in minutes for automatic sync

### 2. Test Connection

1. After creating the configuration, click **Test Connection** to authenticate
2. If successful, the access token will be stored

### 3. Manual Sync

You can manually trigger sync operations:
- **Sync Contacts**: Sync only contacts
- **Sync Products**: Sync only products  
- **Sync All**: Sync all enabled data types

## Automatic Sync

The module includes three cron jobs that run hourly:

1. **Sync Contacts**: Syncs contacts from all active configurations
2. **Sync Products**: Syncs products from all active configurations  
3. **Sync All Data**: Syncs all data types from all active configurations

You can modify the cron job intervals in **Settings > Technical > Scheduled Actions**.

## API Endpoints

The module provides REST API endpoints for external integration:

### Authentication Required Endpoints

All endpoints require user authentication.

#### Test Connection
```http
POST /api_module/test_connection
Content-Type: application/json

{
  "config_id": 1
}
```

#### Sync Contacts
```http
POST /api_module/sync_contacts
Content-Type: application/json

{
  "config_id": 1
}
```

#### Sync Products
```http
POST /api_module/sync_products
Content-Type: application/json

{
  "config_id": 1
}
```

#### Sync All Data
```http
POST /api_module/sync_all
Content-Type: application/json

{
  "config_id": 1
}
```

#### Get Job History
```http
POST /api_module/job_history
Content-Type: application/json

{
  "config_id": 1,
  "limit": 10
}
```

#### Get Configurations
```http
GET /api_module/configurations
```

## Monitoring

### Sync Jobs

View all sync operations in **API Integration > Monitoring > Sync Jobs**:
- Job type (contacts/products/all)
- Status (success/failed/running/pending)
- Records processed
- Error messages
- Timestamps

### Dashboard

The dashboard provides an overview of recent sync activities.

## Dependencies

- Odoo 19.0
- Python `requests` library (included in Odoo)
- External API with GraphQL endpoints for `sync_contacts_from_odoo` and `sync_products_from_odoo` mutations

## External API Requirements

Your external API must provide:

1. **Authentication Endpoint**: `/api/v1/auth/token` (POST with username/password)
2. **GraphQL Endpoint**: `/graphql` with the following mutations:
   - `sync_contacts_from_odoo`
   - `sync_products_from_odoo`

Example GraphQL mutation response format:
```json
{
  "data": {
    "sync_contacts_from_odoo": {
      "success": true,
      "message": "Contacts synced successfully",
      "odoo_id": 123,
      "local_id": 456,
      "errors": []
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check username/password and authentication URL
2. **Connection Timeout**: Verify API server is running and accessible
3. **GraphQL Errors**: Check if required mutations are available
4. **Permission Errors**: Ensure user has appropriate permissions

### Logs

Check Odoo server logs for detailed error information:
```bash
tail -f /var/log/odoo/odoo-server.log
```

## Support

For issues and questions, contact your system administrator or refer to the module documentation.