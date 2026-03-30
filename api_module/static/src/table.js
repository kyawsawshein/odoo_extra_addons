
// ============================================================
// Sync FG/PL/Production → Odoo (Import Product by Lot)
// ============================================================
// Field Mapping:
//   PART No.      (fldlCG4sZmUU2hZUC0J) → product name
//   Product code  (fldfJr9qaGWlvckZz0n) → product default_code
//   QTY           (fldayZy6VCMZ7M4WLdy) → stock quantity
//   Unit          (fldzKd1LRAmJHiWnSsg) → UoM
//   Lot           (fld6fElwpRxraJzts1e) → stock.lot name
//   Status        (fldEZATexJf5Z8Ezyew) → trigger condition
// ============================================================

const triggerData = input['cmm08y36d0yl0oj2sx8vy93jf'];
const record = triggerData.record;
const fields = record.fields;

// --- Extract field values using field IDs ---
const partNo      = fields['fldlCG4sZmUU2hZUC0J'];  // PART No. → Product Name
const productCode = fields['fldfJr9qaGWlvckZz0n'];  // Product code
const qty         = fields['fldayZy6VCMZ7M4WLdy'];  // QTY
const unit        = fields['fldzKd1LRAmJHiWnSsg'];  // Unit
const lotNo       = fields['fld6fElwpRxraJzts1e'];  // Lot → Lot Number
const status      = fields['fldEZATexJf5Z8Ezyew'];  // Status

console.log('=== FG/PL/Production → Odoo Sync ===');
console.log('PART No.:', partNo);
console.log('Product code:', productCode);
console.log('QTY:', qty);
console.log('Unit:', unit);
console.log('Lot:', lotNo);
console.log('Status:', status);

// --- Only sync when Status = "done" ---
// output.set("Status ", status)
// if (status !== 'done') {
//   console.log(`⏭️ Status is "${status || '(empty)'}", not "done". Skipping.`);
//   output.set('status', 'skipped');
//   output.set('reason', `Status is "${status || '(empty)'}", not "done"`);
//   return;
// }

// --- Validate required fields ---
if (!partNo) throw new Error('PART No. is empty, cannot sync');
if (!lotNo) throw new Error('Lot is empty, cannot create Lot in Odoo');
if (qty === null || qty === undefined) throw new Error('QTY is empty, cannot sync');

// ============================================================
// ⚠️ CONFIGURATION - UPDATE THESE WITH YOUR ODOO CREDENTIALS
// ============================================================
const ODOO_URL     = 'https://441e-101-109-242-92.ngrok-free.app';  // ← Change this
const ODOO_DB      = 'odoo';                    // ← Change this
const ODOO_USER    = 'admin';               // ← Change this
const ODOO_API_KEY = '5a736359abf3c13904686109517589c930a382fd';              // ← Change this
// ============================================================

async function odooApi(model, method, args = [], kwargs = {}) {
  const response = await fetch(`${ODOO_URL}/api/${model}/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Database': ODOO_DB,
      'Authorization': `Bearer ${ODOO_API_KEY}`,
    },
    body: JSON.stringify({
      args: args,
      kwargs: kwargs
    })
  });

  const result = await response.json();

  if (!response.ok) {
    console.error('Odoo API Error:', result);
    throw new Error(result.message || 'Odoo API error');
  }

  return result;
}

// --- Odoo JSON-RPC Helper ---
async function odooRpc(url, params) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'call',
      params: params
    })
  });
  const result = await response.json();
  if (result.error) {
    console.error('Odoo RPC Error:', JSON.stringify(result.error));
    throw new Error(`Odoo Error: ${result.error.data?.message || result.error.message}`);
  }
  return result.result;
}

// --- Authenticate ---
async function authenticate() {
  const uid = await odooRpc(`${ODOO_URL}/jsonrpc`, {
    service: 'common',
    method: 'authenticate',
    args: [ODOO_DB, ODOO_USER, ODOO_API_KEY, {}]
  });
  if (!uid) throw new Error('Odoo authentication failed. Check credentials.');
  console.log('✅ Authenticated, uid:', uid);
  return uid;
}

// --- Execute Odoo model method ---
async function execute(uid, model, method, args, kwargs = {}) {
  return await odooRpc(`${ODOO_URL}/jsonrpc`, {
    service: 'object',
    method: 'execute_kw',
    args: [ODOO_DB, uid, ODOO_API_KEY, model, method, args, kwargs]
  });
}

// --- Map Teable Unit → Odoo UoM ---
function mapUoM(unitName) {
  const mapping = {
    'Unit': 'Units',
    'Set':  'Units',
    'Pair': 'Units',
  };
  return mapping[unitName] || 'Units';
}

// ============================================================
// MAIN LOGIC
// ============================================================
console.log('🚀 Starting Odoo sync...');

// Step 1: Authenticate
const uid = await authenticate();

// Step 2: Search or Create Product by PART No. / Product code
// First try to find by product code (default_code), then by name
let productIds = [];

if (productCode) {
  productIds = await execute(uid, 'product.product', 'search', [
    [['default_code', '=', productCode]]
  ]);
  if (productIds.length > 0) {
    console.log('📦 Found product by code:', productCode, '(ID:', productIds[0], ')');
  }
}

if (productIds.length === 0) {
  productIds = await execute(uid, 'product.product', 'search', [
    [['name', '=', partNo]]
  ]);
  if (productIds.length > 0) {
    console.log('📦 Found product by name:', partNo, '(ID:', productIds[0], ')');
  }
}

let productId;
if (productIds.length > 0) {
  productId = productIds[0];
} else {
  // Find UoM ID
  const uomName = mapUoM(unit);
  const uomIds = await execute(uid, 'uom.uom', 'search', [
    [['name', '=', uomName]]
  ]);
  const uomId = uomIds.length > 0 ? uomIds[0] : 1;

  const productData = {
    name: partNo,
    type: 'product',       // Storable product
    tracking: 'lot',       // Enable lot tracking
    uom_id: uomId,
    uom_po_id: uomId,
  };

  // Add product code if available
  if (productCode) {
    productData.default_code = productCode;
  }

  productId = await execute(uid, 'product.product', 'create', [productData]);
  console.log('📦 Created product:', partNo, '| Code:', productCode, '(ID:', productId, ')');
}

// Step 3: Get company_id
const companyIds = await execute(uid, 'res.company', 'search', [[]], { limit: 1 });
const companyId = companyIds[0] || 1;

// Step 4: Search or Create Lot
let lotIds = await execute(uid, 'stock.lot', 'search', [
  [['name', '=', lotNo], ['product_id', '=', productId]]
]);

let lotId;
if (lotIds.length > 0) {
  lotId = lotIds[0];
  console.log('🏷️ Found existing lot:', lotNo, '(ID:', lotId, ')');
} else {
  lotId = await execute(uid, 'stock.lot', 'create', [{
    name: lotNo,
    product_id: productId,
    company_id: companyId,
  }]);
  console.log('🏷️ Created lot:', lotNo, '(ID:', lotId, ')');
}

// Step 5: Update stock quantity
const quantIds = await execute(uid, 'stock.quant', 'search', [
  [['product_id', '=', productId], ['lot_id', '=', lotId], ['location_id.usage', '=', 'internal']]
]);

if (quantIds.length > 0) {
  await execute(uid, 'stock.quant', 'write', [quantIds, { inventory_quantity: qty }]);
  await execute(uid, 'stock.quant', 'action_apply_inventory', [quantIds]);
  console.log('📊 Updated stock qty:', qty);
} else {
  // Get default warehouse stock location
  const warehouses = await execute(uid, 'stock.warehouse', 'search_read', [[]],
    { fields: ['lot_stock_id'], limit: 1 }
  );
  const locationId = warehouses[0]?.lot_stock_id?.[0] || 8;

  const newQuantId = await execute(uid, 'stock.quant', 'create', [{
    product_id: productId,
    lot_id: lotId,
    location_id: locationId,
    inventory_quantity: qty,
  }]);
  await execute(uid, 'stock.quant', 'action_apply_inventory', [[newQuantId]]);
  console.log('📊 Created stock quant (ID:', newQuantId, ') qty:', qty);
}

console.log('=== ✅ Sync Complete ===');
console.log(`Product: ${partNo} | Code: ${productCode} | Lot: ${lotNo} | Qty: ${qty} | Unit: ${unit}`);

output.set('productId', productId);
output.set('lotId', lotId);
output.set('partNo', partNo);
output.set('productCode', productCode);
output.set('lotNo', lotNo);
output.set('qty', qty);
output.set('status', 'success');
