
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
const ODOO_URL     = 'https://6d39-101-109-242-92.ngrok-free.app';  // ← Change this
const ODOO_DB      = 'odoo';                    // ← Change this
const ODOO_USER    = 'admin';               // ← Change this
const ODOO_API_KEY = '5911e9febe3211fc664a606017b179b9df338b38';              // ← Change this
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


//
output.set("product code : ", productCode)
const productIds = await odooApi(
  'product.product',
  'search',
  [[['default_code', '=', productCode]]]
);

console.log("====== Product ids : ", productids)

//

console.log('=== ✅ Sync Complete ===');
console.log(`Product: ${partNo} | Code: ${productCode} | Lot: ${lotNo} | Qty: ${qty} | Unit: ${unit}`);

output.set('productId', productId);
output.set('lotId', lotId);
output.set('partNo', partNo);
output.set('productCode', productCode);
output.set('lotNo', lotNo);
output.set('qty', qty);
output.set('status', 'success');
