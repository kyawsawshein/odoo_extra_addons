# API Module Usage Guide for Odoo 19

This guide explains how to use the API module for integrating with external systems like Table.ai.

## Overview

The API module provides REST endpoints for:
1. **Product Management** - Create and search products
2. **Stock Operations** - Create stock moves and update stock quantities by lot
3. **Manufacturing** - Create manufacturing orders
4. **Comprehensive Sync** - Single endpoint that matches the JavaScript example from Table.ai

## Installation

1. Install the module in Odoo:
   - Copy the `api_module` folder to your Odoo addons directory
   - Install the module via Odoo Apps or command line

2. Configure API settings:
   - Go to **Settings > Technical > API Configuration**
   - Create an API configuration record
   - Enable JWT authentication if needed
   - Generate API tokens for external access

## API Endpoints

### Authentication Methods

#### 1. API Key Authentication
Add header: `X-API-Key: <your-api-key>`

#### 2. JWT Authentication
1. First, get a JWT token:
   ```
   POST /jwt/login
   Content-Type: application/json
   
   {
     "login": "admin",
     "password": "admin"
   }
   ```

2. Use the token in subsequent requests:
   ```
   Authorization: Bearer <jwt-token>
   ```

### Available Endpoints

#### 1. Comprehensive Sync (Matches Table.ai JavaScript Example)
```
POST /api/v1/sync/product_by_lot
```

**Payload:**
```json
{
  "part_no": "PART-001",
  "product_code": "PROD-001",
  "qty": 100,
  "unit": "Units",
  "lot_no": "LOT-001",
  "status": "done"
}
```

**Behavior:**
- Only processes when `status` = "done"
- Searches for product by `product_code` first, then by `part_no`
- Creates product if not found
- Creates or finds lot
- Updates stock quantity for the lot

**Response:**
```json
{
  "success": true,
  "message": "Sync completed successfully",
  "data": {
    "product_id": 123,
    "lot_id": 456,
    "part_no": "PART-001",
    "product_code": "PROD-001",
    "lot_no": "LOT-001",
    "qty": 100,
    "status": "success"
  }
}
```

#### 2. Create Product
```
POST /api/v1/products/create
```

**Payload:**
```json
{
  "name": "Product Name",
  "default_code": "PROD-001",
  "type": "product",
  "tracking": "lot",
  "uom_id": 1,
  "list_price": 100.0,
  "standard_price": 80.0
}
```

#### 3. Search or Create Product
```
POST /api/v1/products/search_or_create
```

**Payload:**
```json
{
  "name": "Product Name",
  "default_code": "PROD-001",
  "unit": "Units"
}
```

#### 4. Create Stock Move
```
POST /api/v1/stock/moves/create
```

**Payload:**
```json
{
  "product_id": 1,
  "qty": 10,
  "location_id": 8,
  "location_dest_id": 12,
  "picking_type_id": 1,
  "reference": "MOV-001",
  "lot_id": 1
}
```

#### 5. Create Manufacturing Order
```
POST /api/v1/mrp/production/create
```

**Payload:**
```json
{
  "product_id": 1,
  "product_qty": 10,
  "bom_id": 1,
  "location_src_id": 8,
  "location_dest_id": 12,
  "lot_id": 1,
  "origin": "API Order"
}
```

#### 6. Create/Update Stock Quant by Lot
```
POST /api/v1/stock/quant/by_lot
```

**Payload:**
```json
{
  "product_id": 1,
  "lot_id": 1,
  "qty": 100,
  "location_id": 8
}
```

## Table.ai Integration Example

Here's how to adapt your Table.ai JavaScript script to use the new API:

### Original JavaScript (Updated for New API)
```javascript
// ============================================================
// Sync FG/PL/Production → Odoo (Import Product by Lot)
// ============================================================

const triggerData = input['cmm08y36d0yl0oj2sx8vy93jf'];
const record = triggerData.record;
const fields = record.fields;

// Extract field values
const partNo = fields['fldlCG4sZmUU2hZUC0J'];      // PART No.
const productCode = fields['fldfJr9qaGWlvckZz0n']; // Product code
const qty = fields['fldayZy6VCMZ7M4WLdy'];         // QTY
const unit = fields['fldzKd1LRAmJHiWnSsg'];        // Unit
const lotNo = fields['fld6fElwpRxraJzts1e'];       // Lot
const status = fields['fldEZATexJf5Z8Ezyew'];      // Status

// Only sync when Status = "done"
if (status !== 'done') {
  console.log(`⏭️ Status is "${status}", not "done". Skipping.`);
  output.set('status', 'skipped');
  output.set('reason', `Status is "${status}", not "done"`);
  return;
}

// Validate required fields
if (!partNo) throw new Error('PART No. is empty');
if (!lotNo) throw new Error('Lot is empty');
if (qty === null || qty === undefined) throw new Error('QTY is empty');

// API Configuration
const ODOO_URL = 'https://your-odoo-instance.com';
const API_KEY = 'your-api-key-here'; // Or use JWT token

// Call the comprehensive sync endpoint
async function syncToOdoo() {
  const response = await fetch(`${ODOO_URL}/api/v1/sync/product_by_lot`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      part_no: partNo,
      product_code: productCode,
      qty: qty,
      unit: unit || 'Units',
      lot_no: lotNo,
      status: status
    })
  });

  const result = await response.json();
  
  if (result.success) {
    console.log('✅ Sync successful:', result.message);
    output.set('productId', result.data.product_id);
    output.set('lotId', result.data.lot_id);
    output.set('partNo', result.data.part_no);
    output.set('productCode', result.data.product_code);
    output.set('lotNo', result.data.lot_no);
    output.set('qty', result.data.qty);
    output.set('status', 'success');
  } else {
    console.error('❌ Sync failed:', result.message);
    throw new Error(`API Error: ${result.message}`);
  }
}

// Execute sync
await syncToOdoo();
console.log('=== ✅ Sync Complete ===');
```

## Testing

1. Use the provided test script:
   ```bash
   python extra_addons/api_module/test_api_example.py
   ```

2. Update the configuration variables in the test script:
   - `ODOO_URL`: Your Odoo instance URL
   - `API_KEY`: Your API key or configure JWT authentication

3. Test with curl:
   ```bash
   curl -X POST https://your-odoo-instance.com/api/v1/sync/product_by_lot \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{
       "part_no": "TEST-001",
       "product_code": "TEST-CODE",
       "qty": 100,
       "unit": "Units",
       "lot_no": "TEST-LOT",
       "status": "done"
     }'
   ```

## Error Handling

All endpoints return standardized responses:

**Success:**
```json
{
  "success": true,
  "message": "Operation completed",
  "data": { ... },
  "timestamp": "2024-01-01T12:00:00"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message",
  "timestamp": "2024-01-01T12:00:00"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (validation error)
- `401`: Authentication failed
- `500`: Internal server error

## Security Considerations

1. **API Keys**: Store API keys securely, rotate regularly
2. **JWT Tokens**: Set appropriate expiration times
3. **Rate Limiting**: Implement if needed for production
4. **Input Validation**: All inputs are validated server-side
5. **Access Control**: API tokens are associated with specific users

## Support

For issues or questions:
1. Check Odoo logs for detailed error messages
2. Verify API configuration in Odoo settings
3. Ensure all required modules are installed (stock, mrp)
4. Test with the provided test script first