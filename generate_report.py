#!/usr/bin/env python3
"""
Neuroelectrics Material Cost Report — generate_report.py
Queries Odoo via XML-RPC, generates full 2025+2026 dashboard HTML.
Runs via GitHub Actions (scheduled + manual) or locally.

Usage:
  export ODOO_URL=https://neuroelectrics.cloudodoo.com
  export ODOO_DB=neuro_pro
  export ODOO_USERNAME=lucio.boretto@neuroelectrics.com
  export ODOO_PASSWORD=<api_key>
  python generate_report.py
"""

import os, json, datetime
import xmlrpc.client

# ── Odoo connection ───────────────────────────────────────────────────────────
URL  = os.environ.get('ODOO_URL',      'https://neuroelectrics.cloudodoo.com')
DB   = os.environ.get('ODOO_DB',       'neuro_pro')
USER = os.environ.get('ODOO_USERNAME', 'lucio.boretto@neuroelectrics.com')
PASS = os.environ.get('ODOO_PASSWORD', '')

print('Connecting to Odoo...')
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
if not uid:
    raise SystemExit('ERROR: Odoo authentication failed. Check credentials.')
print(f'  OK  uid={uid}')
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=500):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def sr_batched(model, id_field, ids, fields, batch=200, limit=2000):
    """search_read across large id lists in batches."""
    results = []
    for i in range(0, len(ids), batch):
        results.extend(models.execute_kw(
            DB, uid, PASS, model, 'search_read',
            [[['id', 'in', ids[i:i+batch]]]],
            {'fields': fields, 'limit': limit}
        ))
    return results

# ── Static config ─────────────────────────────────────────────────────────────
EXCLUDE_PICKINGS = {'INT/13409', 'INT/13411'}
EXCLUDE_PRODUCTS = ['engineering tools']
STOCK_LOCS = {12, 232, 233}
POOL_LOCS  = {95, 43}
ENG_LOCS   = {92, 281, 282, 283}
PM_LOCS    = {122, 290, 291, 292}

SO_AREA_MAP = {
    "SO20260122-0036":"Customer Support","SO20260212-0086":"Sales",
    "SO20260304-0142":"Customer Support","SO20260313-0175":"Sales",
    "SO20260311-0159":"Brain Modeling","SO20260312-0161":"Brain Modeling",
    "SO20260312-0162":"Brain Modeling","SO20260312-0163":"Brain Modeling",
    "SO20260312-0164":"Brain Modeling","SO20260312-0165":"Brain Modeling",
    "SO20260312-0166":"Brain Modeling","SO20260312-0167":"Brain Modeling",
    "SO20260312-0168":"Brain Modeling","SO20260312-0169":"Brain Modeling",
    "SO20260317-0183":"Sales","SO20260402-0228":"Sales",
    "SO20260422-0272":"Sales","SO20260428-0288":"Sales",
    "SO20260430-0295":"Sales","SO20260514-0341":"Customer Support",
    "SO20260602-0380":"Sales","SO20260619-0446":"Sales",
    "RTI/00389":"Sales","RTI/00399":"Customer Support","RTI/00400":"Sales",
    "RTI/00434":"Sales","RTI/00467":"Sales","RTI/00543":"Sales",
    "RTI/00544":"Sales","RTI/00546":"Customer Support","RTI/00549":"Customer Support",
    "RTI/00557":"Customer Support","RTI/00566":"Sales","RTI/00569":"Sales",
    "RTI/00572":"Customer Support","RTI/00579":"Customer Support",
    "RTI/00580":"Customer Support","RTI/00594":"Customer Support",
    "RTI/00611":"Sales","RTI/00616":"Sales","RTI/00626":"Sales",
    "RTI/00636":"Customer Support","RTI/00638":"Sales",
    "RTI/00648":"Customer Support","RTI/00675":"Customer Support",
    "RTI/00707":"Customer Support","RTI/00730":"Sales",
    "RTI/00736":"Product","RTI/00737":"Customer Support",
    "RTI/00753":"Customer Support","RTI/00791":"Customer Support",
    "RTI/00842":"Customer Support","RTI/00880":"Customer Support",
    "RTI/00882":"Sales","RTI/00897":"Sales","RTI/00915":"Sales",
    "RTI/00933":"Customer Support","RTI/00946":"Customer Support",
    "RTI/00995":"Customer Support","RTI/01004":"Sales",
    "RTI/01071":"Customer Support","RTI/01082":"Customer Support",
    "RTI/01085":"Sales","RTI/01092":"Sales","RTI/01128":"Customer Support",
    "RTI/01130":"Sales","RTI/01148":"Sales","RTI/01153":"Customer Support",
    "RTI/01200":"Customer Support"
}

PRICES_FB = {378:559.27465,2021:0.38294,5440:65.1792,2947:0.6786,201:3.84923,
 13:1.34915,2514:1.45559,286:6.54568,26:7.7,125:38.70904,2071:8.4197,
 23:24.9173,2088:35.111,2521:0.9538,2086:36.9374,2085:44.303,20:39.16286,
 4737:32.53746,285:9.88934,2117:0.07361,3257:0.45,5374:0.11,5513:39.5045,
 5069:0.37,5103:2.51,5303:0.11,5666:1064.80393,4755:79.58913,4757:82.05189,
 4758:97.03432,202:24.95169,335:35.9954,301:95.18276,8052:37.39458,779:31.2153,
 131:9.82679,5894:124.11296,267:0.81696,266:0.78062,56:0.09,55:0.08608,
 92:6.18531,8048:0.6,8047:0.97,8045:6.0,8042:7.0,8043:7.0,3310:66.10206,
 97:80.46048,371:5.77736,789:414.49526,759:763.51762,766:4.16531,4335:2.2365,
 16:1.08669,22:68.82199,790:41.98537,3088:4.50531,19:26.8025,380:461.55724,
 21:22.87667,387:69.66627,507:3.83,4642:2.26035,379:336.44836,5670:1130.28167,
 418:2359.78205,757:756.49228,1036:3232.77912,4390:39.47759,5680:1258.44598,
 2515:2.38772,29:6.27497,350:22.29551,4641:2.60319,393:2359.78205,792:88.63141,
 134:4.06346,352:27.81299,351:40.84301,349:27.81301,14:1.47528,519:37.21728,
 32:1.02216,3311:105.75109,1051:1349.9476,2519:0.59301,414:25.40141,415:15.52231,
 417:19.62139,4385:50.52545,395:17.25566,3218:4.51,4527:69.98178,190:28.79638,
 4738:34.5449,2811:2.91105,15:1.7016,4383:62.53149,4529:89.52501,4386:25.8824,
 3216:6.41878,377:767.726,3219:2.87,5423:6.41878,5660:344.4679,3073:0.04188,
 2424:0.7,2637:1.3,3078:20.0863,2635:1.3,5925:4.39,3082:36.93104,3076:14.3176,
 3084:238.24329,186:5.14458,107:0.54402,3074:0.92925,158:1.94875,5055:0.05,
 43:0.02974,756:6.23284,799:14.2993,2034:0.26491,35:434.32886,36:117.50478,
 3085:45.92985,3080:50.50829,3077:5.5036,3075:4.70506,4948:1934.6932,
 3079:11.16298,3081:25.3545,8019:2134.41715,33:19.77045,3064:0.23491,
 2380:0.85925,2020:0.19882,2022:0.29175,2453:0.15,6111:85.52783}

# ── Helpers ───────────────────────────────────────────────────────────────────
def pdate(s):
    if not s: return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try: return datetime.datetime.strptime(str(s)[:19], fmt)
        except: pass
    return None

def unwrap(v):
    """Odoo many2one fields return [id, name] — extract id."""
    return v[0] if isinstance(v, (list, tuple)) and v else (v or 0)

def get_price(pid):
    p = products.get(pid, {})
    return p.get('standard_price') or PRICES_FB.get(pid, 0)

def is_eng_tool(name):
    return any(e in (name or '').lower() for e in EXCLUDE_PRODUCTS)

def get_area(rtin, so):
    for key in [so, rtin]:
        if key and SO_AREA_MAP.get(key):
            return SO_AREA_MAP[key], '—'
    return 'Sales', '—'

# ── STEP 1 — RTI pickings ─────────────────────────────────────────────────────
print('Step 1: RTI pickings...')
pk_fields = ['id', 'name', 'origin', 'state', 'date_done', 'location_id', 'location_dest_id']
all_src = list(POOL_LOCS | STOCK_LOCS)

rti25_raw = sr('stock.picking', [
    ['location_id', 'in', all_src], ['state', '=', 'done'],
    ['date_done', '>=', '2025-01-01'], ['date_done', '<', '2026-01-01']
], pk_fields)

rti26_raw = sr('stock.picking', [
    ['location_id', 'in', all_src], ['state', '=', 'done'],
    ['date_done', '>=', '2026-01-01']
], pk_fields)

print(f'  2025: {len(rti25_raw)} | 2026: {len(rti26_raw)}')

# ── STEP 2 — Move lines for RTI ───────────────────────────────────────────────
print('Step 2: RTI move lines...')
ml_fields = ['id', 'picking_id', 'product_id', 'lot_id', 'qty_done', 'date',
             'location_id', 'location_dest_id']
all_pk_ids = [p['id'] for p in rti25_raw + rti26_raw]

rti_moves_raw = []
for i in range(0, len(all_pk_ids), 200):
    rti_moves_raw.extend(sr('stock.move.line',
        [['picking_id', 'in', all_pk_ids[i:i+200]], ['state', '=', 'done']],
        ml_fields, limit=2000))

# Lot names
lot_ids = list({unwrap(m['lot_id']) for m in rti_moves_raw if m.get('lot_id')})
lots = {}
if lot_ids:
    for l in sr_batched('stock.lot', 'id', lot_ids, ['id', 'name']):
        lots[l['id']] = l['name']

# Picking name index
pk_names = {p['id']: p['name'] for p in rti25_raw + rti26_raw}

# Normalize move lines
def norm_ml(m):
    return {
        'picking_id':   unwrap(m['picking_id']),
        'picking_name': pk_names.get(unwrap(m['picking_id']), ''),
        'product_id':   unwrap(m['product_id']),
        'lot_id':       unwrap(m['lot_id']),
        'lot_name':     lots.get(unwrap(m['lot_id']), ''),
        'qty_done':     m['qty_done'],
        'date':         m.get('date', '') or '',
        'location_id':  unwrap(m['location_id']),
        'location_dest_id': unwrap(m['location_dest_id']),
    }

rti_moves = [norm_ml(m) for m in rti_moves_raw]
print(f'  {len(rti_moves)} move lines, {len(lots)} lots')

# Group moves by picking
moves_by_pk = {}
for m in rti_moves:
    moves_by_pk.setdefault(m['picking_id'], []).append(m)

def pk_dict(pk):
    return {
        'picking_id':   pk['id'],
        'picking_name': pk['name'],
        'origin':       pk.get('origin', '') or '',
        'date_done':    pk.get('date_done', '') or '',
        'location_id':  unwrap(pk['location_id']),
        'state':        pk.get('state', 'done'),
        'moves':        moves_by_pk.get(pk['id'], [])
    }

rti25 = [pk_dict(p) for p in rti25_raw]
rti26 = [pk_dict(p) for p in rti26_raw]

# ── STEP 3 — INT pool moves (48h candidates) ──────────────────────────────────
print('Step 3: INT pool moves...')
all_lots = list({m['lot_id'] for m in rti_moves if m['lot_id']})
int_pool = []
if all_lots:
    for i in range(0, len(all_lots), 200):
        batch = all_lots[i:i+200]
        ms = sr('stock.move.line', [
            ['lot_id', 'in', batch], ['state', '=', 'done'],
            ['location_id', 'in', list(STOCK_LOCS)],
            ['location_dest_id', 'in', list(POOL_LOCS)]
        ], ml_fields, limit=2000)
        int_pool.extend(ms)

# Get picking names for pool INT moves
ip_pk_ids = list({unwrap(m['picking_id']) for m in int_pool})
ip_pk_names = {}
if ip_pk_ids:
    for p in sr_batched('stock.picking', 'id', ip_pk_ids, ['id', 'name']):
        ip_pk_names[p['id']] = p['name']

int_pool = [{
    'picking_id':   unwrap(m['picking_id']),
    'picking_name': ip_pk_names.get(unwrap(m['picking_id']), ''),
    'product_id':   unwrap(m['product_id']),
    'lot_id':       unwrap(m['lot_id']),
    'qty_done':     m['qty_done'],
    'date':         m.get('date', '') or '',
} for m in int_pool]

print(f'  {len(int_pool)} pool INT moves')

# ── STEP 4 — Engineering/PM INT pickings ─────────────────────────────────────
print('Step 4: Engineering/PM pickings...')
ep_dest = list(ENG_LOCS | PM_LOCS)
ep_pks_raw = sr('stock.picking', [
    ['location_dest_id', 'in', ep_dest], ['state', '=', 'done']
], pk_fields, limit=500)

ep_ml_raw = []
ep_pk_ids = [p['id'] for p in ep_pks_raw]
for i in range(0, len(ep_pk_ids), 200):
    ep_ml_raw.extend(sr('stock.move.line',
        [['picking_id', 'in', ep_pk_ids[i:i+200]], ['state', '=', 'done']],
        ml_fields, limit=2000))

ep_moves_by_pk = {}
for m in ep_ml_raw:
    pk_id = unwrap(m['picking_id'])
    ep_moves_by_pk.setdefault(pk_id, []).append({
        'product_id': unwrap(m['product_id']),
        'qty_done':   m['qty_done'],
        'lot_id':     unwrap(m['lot_id']),
        'lot_name':   lots.get(unwrap(m['lot_id']), ''),
    })

eng_pm_raw = []
for pk in ep_pks_raw:
    dest = unwrap(pk['location_dest_id'])
    area = 'Engineering' if dest in ENG_LOCS else 'Product'
    dd = pk.get('date_done', '') or ''
    yr = int(dd[:4]) if dd else 2025
    eng_pm_raw.append({
        'picking_name': pk['name'],
        'date_done':    dd,
        'location_id':  unwrap(pk['location_id']),
        'area': area, 'year': yr,
        'moves': ep_moves_by_pk.get(pk['id'], [])
    })

print(f'  {len(eng_pm_raw)} Eng/PM pickings')

# ── STEP 5 — Return-to-stock exclusions ──────────────────────────────────────
print('Step 5: Detecting return-to-stock exclusions...')
ret_pks = sr('stock.picking', [
    ['origin', 'like', 'Return of INT/'],
    ['state', '=', 'done'],
    ['location_dest_id', 'in', list(STOCK_LOCS)]
], ['id', 'name', 'origin'], limit=200)

returns = set()
for pk in ret_pks:
    orig = pk.get('origin', '') or ''
    if orig.startswith('Return of '):
        returns.add(orig[len('Return of '):].strip())

all_exc = EXCLUDE_PICKINGS | returns
print(f'  Excluded: {sorted(all_exc)}')

# ── STEP 6 — Products & prices ────────────────────────────────────────────────
print('Step 6: Product prices...')
all_pids = list({
    m['product_id']
    for m in rti_moves + int_pool + ep_ml_raw
    if unwrap(m.get('product_id'))
})

products = {}
for p in sr_batched('product.product', 'id', all_pids,
                    ['id', 'default_code', 'name', 'standard_price']):
    products[p['id']] = p

print(f'  {len(products)} products')

# ── Processing ────────────────────────────────────────────────────────────────
ibl = {}  # lot_id → [INT pool moves]
for m in int_pool:
    ibl.setdefault(m['lot_id'], []).append(m)

def proc_rti(rti_list, year):
    rows = []
    for pk in rti_list:
        pn = pk['picking_name']
        so = pk['origin'].strip()
        rd = pdate(pk['date_done'])
        rs = pk['location_id']
        if pn in all_exc: continue
        cls = []
        for mv in pk['moves']:
            pid = mv['product_id']; lid = mv['lot_id']; qty = mv['qty_done']
            pr  = products.get(pid, {}); nm = pr.get('name', '')
            p   = get_price(pid)
            if is_eng_tool(nm) or not p: continue
            cl = dict(picking='', product_id=pid, product_name=nm,
                      default_code=pr.get('default_code','?') or '?',
                      lot=mv['lot_name'], qty=qty, unit_price=p,
                      line_cost=round(qty*p, 4), location_origin='WH/IM/Stock')
            if rs in STOCK_LOCS:
                cl['picking'] = 'RTI (direct stock)'; cls.append(cl)
            elif lid and lid in ibl and rd:
                cs = [m for m in ibl[lid]
                      if pdate(m['date']) and pdate(m['date']) <= rd
                      and (rd - pdate(m['date'])).total_seconds() <= 48*3600]
                if cs:
                    b = max(cs, key=lambda m: pdate(m['date']))
                    bn = ip_pk_names.get(b['picking_id'], b.get('picking_name','INT'))
                    if bn not in all_exc:
                        cl['picking'] = bn; cls.append(cl)
        tot = round(sum(c['line_cost'] for c in cls), 2)
        ct  = ('direct_stock' if rs in STOCK_LOCS and tot > 0
               else 'no_cost' if rs in STOCK_LOCS
               else 'hidden_lot' if cls else 'no_cost')
        at, fr = get_area(pn, so)
        rt = 'Loan' if rs == 43 else 'Demo'
        tr = pn if year == 2025 else (so or pn)
        rows.append(dict(
            transfer=tr, status=pk['state'], customer=(so if year==2025 else ''),
            cost_lines=cls, total_cost=tot, cost_type=ct,
            note=f'48h window before RTI {rd.strftime("%Y-%m-%d") if rd else ""}',
            rti_date=rd.strftime('%Y-%m-%d') if rd else '',
            rti_src=rs, responsible=fr, project='General',
            rti_picking=pn, request_type=rt, area=at, form_requester=fr, year=year
        ))
    return rows

def proc_pool():
    ibp = {}
    for m in int_pool:
        ibp.setdefault(m['picking_name'], []).append(m)
    rows = []
    for pn, mvs in ibp.items():
        if pn in all_exc: continue
        cls = []
        for mv in mvs:
            pid = mv['product_id']; pr = products.get(pid, {})
            nm = pr.get('name',''); p = get_price(pid); qty = mv['qty_done']
            if is_eng_tool(nm) or not p: continue
            cls.append(dict(picking=pn, product_id=pid, product_name=nm,
                            default_code=pr.get('default_code','?') or '?',
                            lot='', qty=qty, unit_price=p,
                            line_cost=round(qty*p,4), location_origin='WH/IM/Stock'))
        tot = round(sum(c['line_cost'] for c in cls), 2)
        yr  = int(mvs[0]['date'][:4]) if mvs and mvs[0].get('date') else 2026
        rows.append(dict(transfer=pn, status='done', customer='',
                         cost_lines=cls, total_cost=tot,
                         cost_type='hidden_lot' if tot>0 else 'no_cost',
                         note='', area='', year=yr))
    return rows

def proc_ep():
    rows = []
    for pk in eng_pm_raw:
        pn = pk['picking_name']
        if pn in all_exc: continue
        area = pk['area']; yr = pk['year']
        rd   = pdate(pk['date_done'])
        cls  = []
        for mv in pk['moves']:
            pid = mv['product_id']; pr = products.get(pid, {})
            nm = pr.get('name',''); p = get_price(pid); qty = mv['qty_done']
            if is_eng_tool(nm) or not p: continue
            cls.append(dict(picking=pn, product_id=pid, product_name=nm,
                            default_code=pr.get('default_code','?') or '?',
                            lot=mv.get('lot_name',''), qty=qty, unit_price=p,
                            line_cost=round(qty*p,4), location_origin='WH/IM/Stock'))
        tot = round(sum(c['line_cost'] for c in cls), 2)
        dt  = rd.strftime('%Y-%m-%d') if rd else pk['date_done'][:10]
        rows.append(dict(transfer=pn, status='done', customer='',
                         cost_lines=cls, total_cost=tot,
                         cost_type='direct_stock' if tot>0 else 'zero',
                         note=f'{area} direct stock', area=area, year=yr,
                         rti_date=dt, form_requester='—', responsible='—',
                         project='—', request_type=area, rti_picking=pn,
                         rti_src=pk['location_id']))
    return rows

print('Processing...')
sr25 = proc_rti(rti25, 2025)
sr26 = proc_rti(rti26, 2026)
ir   = proc_pool()
ep   = proc_ep()

gs = round(sum(r['total_cost'] for r in sr25 + sr26), 2)
gi = round(sum(r['total_cost'] for r in ir + ep), 2)
g  = round(gs + gi, 2)
today = datetime.date.today().strftime('%d/%m/%Y')

print(f'  Grand total: EUR {g}')
print(f'  2025 SOs: {len(sr25)}  2026 SOs: {len(sr26)}  Pool INTs: {len(ir)}  Eng/PM: {len(ep)}')

# ── HTML ──────────────────────────────────────────────────────────────────────
D_pay  = json.dumps({'grand':g,'grand_so':gs,'grand_int':gi,'so_rows':sr26,'int_rows':ir},
                    ensure_ascii=False, separators=(',',':'))
D25_pay = json.dumps({'so_rows':sr25}, ensure_ascii=False, separators=(',',':'))
EP_pay  = json.dumps(ep, ensure_ascii=False, separators=(',',':'))

HEADER = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Material Cost Report 2025-2026 - Neuroelectrics</title>
<style>
:root{--bk:#4b4c4a;--gy:#898d8d;--bg:#f6f5f4;--wh:#fff;--bl:#3b82f6;--gn:#10b981;--am:#f59e0b;--pu:#8b5cf6;--sh:0 1px 3px rgba(0,0,0,.12);--r:8px;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Roboto,sans-serif;background:var(--bg);color:var(--bk);font-size:14px;}
header{background:var(--wh);border-bottom:1px solid #e5e7eb;padding:14px 28px;display:flex;align-items:center;gap:14px;}
header h1{font-size:16px;font-weight:700;}header p{font-size:11px;color:var(--gy);margin-top:2px;}
.main{padding:22px 28px;max-width:1420px;margin:0 auto;}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;}
.refresh-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:var(--bl);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;text-decoration:none;}
.refresh-btn:hover{background:#2563eb;}
.refresh-btn svg{width:14px;height:14px;}
.refresh-status{font-size:11px;color:var(--gy);margin-top:4px;}
.filters{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;align-items:flex-end;background:var(--wh);padding:12px 16px;border-radius:var(--r);box-shadow:var(--sh);}
.filters label{font-size:10px;font-weight:600;color:var(--gy);text-transform:uppercase;letter-spacing:.05em;}
.fg{display:flex;flex-direction:column;gap:4px;}
select{border:1px solid #e5e7eb;border-radius:6px;padding:6px 10px;font-size:12px;color:var(--bk);background:var(--bg);cursor:pointer;}
select:focus{outline:none;border-color:var(--bl);}
.breset{padding:7px 14px;border-radius:6px;border:none;background:var(--bk);color:#fff;font-size:12px;font-weight:600;cursor:pointer;margin-left:auto;}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;margin-bottom:20px;}
.kpi{background:var(--wh);border-radius:var(--r);padding:18px 20px;box-shadow:var(--sh);border-left:4px solid var(--bl);}
.kpi.g{border-color:var(--gn);}.kpi.a{border-color:var(--am);}.kpi.p{border-color:var(--pu);}
.kpi-lbl{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--gy);margin-bottom:5px;}
.kpi-val{font-size:24px;font-weight:700;}.kpi-sub{font-size:11px;color:var(--gy);margin-top:3px;}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px;}
.cc{background:var(--wh);border-radius:var(--r);padding:16px 18px;box-shadow:var(--sh);}
.ct{font-size:12px;font-weight:600;margin-bottom:12px;}canvas{max-height:210px;}
.section{background:var(--wh);border-radius:var(--r);box-shadow:var(--sh);margin-bottom:20px;overflow:hidden;}
.sh{padding:12px 18px;background:var(--bk);color:#fff;font-size:12px;font-weight:600;display:flex;align-items:center;gap:8px;}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;background:rgba(255,255,255,.2);}
table{width:100%;border-collapse:collapse;font-size:12.5px;}
th{padding:8px 12px;text-align:left;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:var(--gy);background:var(--bg);border-bottom:1px solid #e5e7eb;white-space:nowrap;}
td{padding:8px 12px;border-bottom:1px solid #f0f0f0;vertical-align:middle;}
tr:last-child td{border-bottom:none;}tr:hover td{background:#fafafa;}
.cr{font-weight:600;text-align:right;}.zero{color:var(--gy);}
.pill{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;white-space:nowrap;}
.p-sales{background:#dbeafe;color:#1d4ed8;}.p-cs{background:#d1fae5;color:#065f46;}
.p-bm{background:#ede9fe;color:#5b21b6;}.p-eng{background:#fef3c7;color:#92400e;}
.p-prod{background:#fce7f3;color:#9d174d;}.p-dir{background:#dbeafe;color:#1d4ed8;}
.p-hid{background:#fef3c7;color:#92400e;}.p-zer{background:#f3f4f6;color:#6b7280;}
.p-int{background:#ede9fe;color:#5b21b6;}
.p-demo{background:#dcfce7;color:#166534;}.p-loan{background:#fce7f3;color:#9d174d;}
.mtag{display:inline-block;background:#f0f4ff;border:1px solid #c7d7f9;color:#1e40af;border-radius:4px;padding:1px 6px;font-size:10.5px;font-family:monospace;margin:1px 2px 1px 0;white-space:nowrap;}
.xbtn{background:none;border:none;cursor:pointer;color:var(--bl);font-size:11px;font-weight:700;padding:0 2px;}
.det-row{display:none;}.det-row td{background:#f8faff;padding:0;border-bottom:1px solid #e8edf8;}
.det-inner{padding:10px 14px 10px 28px;}
.det-info{display:grid;grid-template-columns:1fr 1fr;gap:5px 24px;background:#eef4ff;padding:10px 12px;border-radius:6px;border:1px solid #dbeafe;margin-bottom:10px;font-size:11px;color:var(--gy);}
.det-info b{color:var(--bk);}
.prd-hdr{display:grid;grid-template-columns:130px 1fr 45px 90px 80px;gap:0 10px;padding:3px 0 5px;font-size:10px;color:var(--gy);font-weight:600;text-transform:uppercase;border-bottom:1px solid #e5e7eb;margin-top:8px;}
.prd-row{display:grid;grid-template-columns:130px 1fr 45px 90px 80px;gap:3px 10px;align-items:center;padding:4px 0;font-size:12px;border-bottom:1px dashed #f0f0f0;}
.prd-row:last-child{border-bottom:none;}
.prd-code{font-weight:700;font-family:monospace;font-size:11px;color:var(--bl);}
.prd-tot{font-weight:700;text-align:right;}
.det-sum{display:flex;gap:20px;margin-top:8px;padding-top:8px;border-top:1px solid #e8edf8;font-size:11px;}
.det-sum span{color:var(--gy);}.det-sum b{color:var(--bk);}
.banner{background:#fff7ed;border:1px solid #fed7aa;border-radius:var(--r);padding:10px 14px;margin-bottom:18px;font-size:11.5px;color:#9a3412;}
.foot{text-align:right;font-size:12px;color:var(--gy);padding:4px 0 12px;}
.foot b{color:var(--bk);font-size:15px;}
@media(max-width:900px){.chart-row{grid-template-columns:1fr;}}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
</head>
<body>
<header>
  <svg width="130" height="38" viewBox="0 0 200 45" xmlns="http://www.w3.org/2000/svg">
    <rect width="6" height="45" rx="3" fill="#4b4c4a"/>
    <rect x="10" width="6" height="30" rx="3" fill="#4b4c4a"/>
    <rect x="20" width="6" height="45" rx="3" fill="#4b4c4a"/>
    <text x="34" y="30" font-family="Roboto,sans-serif" font-size="18" font-weight="700" fill="#4b4c4a">neuroelectrics</text>
  </svg>
  <div>
    <h1>Material Cost Report &mdash; Demo/Loan Pool 2025&ndash;2026</h1>
    <p>Costes de material (stock&rarr;pool) no facturados &middot; Ventana 48h antes RTI &middot; Actualizado: TODAY_PH</p>
  </div>
</header>
<div class="main">
<div class="topbar">
  <div class="banner" style="margin-bottom:0;flex:1">
    <strong>Criterio:</strong> INT desde stock al pool en las <strong>48h anteriores al RTI</strong>. Engineering/PM: INT directo desde stock.
  </div>
  <div style="margin-left:16px;text-align:right">
    <a class="refresh-btn" href="https://github.com/lucioboretto-oss/ne-material-cost-report/actions/workflows/refresh.yml" target="_blank">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
      Actualizar ahora
    </a>
    <div class="refresh-status">Abre GitHub Actions &rarr; Run workflow</div>
  </div>
</div>
<br>
<div class="filters">
  <div class="fg"><label>Area</label><select id="f-area" onchange="applyFilters()"><option value="">Todas las areas</option></select></div>
  <div class="fg"><label>Tipo</label><select id="f-type" onchange="applyFilters()"><option value="">Todos</option><option value="Demo">Demo</option><option value="Loan">Loan</option></select></div>
  <div class="fg"><label>Anio</label><select id="f-year" onchange="applyFilters()"><option value="">2025+2026</option><option value="2025">2025</option><option value="2026">2026</option></select></div>
  <button class="breset" onclick="resetFilters()">Limpiar</button>
</div>
<div id="kpi-grid" class="kpi-grid"></div>
<div class="chart-row">
  <div class="cc"><div class="ct">Coste por Area</div><canvas id="cArea"></canvas></div>
  <div class="cc"><div class="ct">Coste por Mes</div><canvas id="cMonth"></canvas></div>
</div>
<div class="section">
  <div class="sh">Pedidos de Material (SOs) <span class="badge" id="so-badge"></span><span style="margin-left:auto;font-size:10px;font-weight:400;opacity:.75">&#9654; detalle</span></div>
  <table><thead><tr><th></th><th>SO / RTI</th><th>Solicitante</th><th>Area</th><th>Tipo</th><th>RTI Date</th><th>Coste</th><th>Materiales</th><th style="text-align:right">Total (EUR)</th></tr></thead>
  <tbody id="so-tbody"></tbody>
  <tfoot><tr style="background:var(--bg)"><td colspan="8" style="font-weight:700;padding:10px 12px">SUBTOTAL SOs</td><td class="cr" id="so-foot" style="padding:10px 12px"></td></tr></tfoot></table>
</div>
<div class="section">
  <div class="sh">Internal Transfers (INT) <span class="badge" id="int-badge"></span></div>
  <table><thead><tr><th></th><th>Transfer</th><th>Descripcion</th><th>Area</th><th>Tipo coste</th><th style="text-align:right">Total (EUR)</th></tr></thead>
  <tbody id="int-tbody"></tbody>
  <tfoot><tr style="background:var(--bg)"><td colspan="5" style="font-weight:700;padding:10px 12px">SUBTOTAL INTs</td><td class="cr" id="int-foot" style="padding:10px 12px"></td></tr></tfoot></table>
</div>
<div class="foot">GRAND TOTAL (SOs + INTs): <b id="grand-foot"></b> &nbsp;&middot;&nbsp; 48h window &middot; 2025&ndash;2026</div>
</div>
<script>
"""

FOOTER = r"""
const fmt=n=>'EUR '+(n||0).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g,',');
const fmtD=s=>s?s.split('-').reverse().join('/'):'--';
const sel=id=>document.getElementById(id);
const AREA_C={'Sales':'#3b82f6','Customer Support':'#10b981','Brain Modeling':'#8b5cf6','Engineering':'#f59e0b','Product':'#ec4899'};
const AREA_CLS={'Sales':'p-sales','Customer Support':'p-cs','Brain Modeling':'p-bm','Engineering':'p-eng','Product':'p-prod'};
const MLBL=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
let cA,cM;
function buildCharts(rows,ir){
  const all=[...(rows||[]),...(ir||[])];
  if(!all.length){if(cA)cA.destroy();if(cM)cM.destroy();return;}
  const bA={},bM={};
  all.forEach(r=>{if(!r.total_cost)return;bA[r.area]=(bA[r.area]||0)+r.total_cost;const dt=r.rti_date||r.date;if(dt){const m=dt.slice(0,7);bM[m]=(bM[m]||0)+r.total_cost;}});
  const aL=Object.keys(bA).sort((a,b)=>bA[b]-bA[a]);
  const mK=Object.keys(bM).sort();
  const mL=mK.map(m=>{const[y,mo]=m.split('-');return MLBL[parseInt(mo)-1]+' '+y.slice(2);});
  if(cA)cA.destroy();
  cA=new Chart(sel('cArea').getContext('2d'),{type:'bar',data:{labels:aL,datasets:[{data:aL.map(k=>bA[k]),backgroundColor:aL.map(k=>AREA_C[k]||'#9ca3af'),borderRadius:5}]},options:{indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmt(c.parsed.x)}}},scales:{x:{ticks:{callback:v=>fmt(v)},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});
  if(cM)cM.destroy();
  cM=new Chart(sel('cMonth').getContext('2d'),{type:'bar',data:{labels:mL,datasets:[{data:mK.map(k=>bM[k]),backgroundColor:'#3b82f6',borderRadius:5}]},options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmt(c.parsed.y)}}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}}});
}
function buildKPIs(rows,ir){
  const iT=ir.reduce((s,r)=>s+r.total_cost,0),sT=rows.reduce((s,r)=>s+r.total_cost,0);
  const kpis=[{l:'Grand Total',v:fmt(sT+iT),s:rows.length+' SOs + '+ir.length+' INTs',c:''},{l:'SOs con coste',v:fmt(sT),s:rows.filter(r=>r.total_cost>0).length+' de '+rows.length,c:'g'},{l:'INTs con coste',v:fmt(iT),s:ir.filter(r=>r.total_cost>0).length+' de '+ir.length,c:'a'},{l:'SOs sin coste',v:rows.filter(r=>r.total_cost===0).length,s:'Pool ya tenia material',c:'p'}];
  const g=sel('kpi-grid');g.innerHTML='';
  kpis.forEach(k=>{const d=document.createElement('div');d.className='kpi '+k.c;d.innerHTML='<div class="kpi-lbl">'+k.l+'</div><div class="kpi-val">'+k.v+'</div><div class="kpi-sub">'+k.s+'</div>';g.appendChild(d);});
  sel('so-foot').textContent=fmt(sT);sel('grand-foot').textContent=fmt(sT+iT);
}
function matTags(cls){
  if(!cls||!cls.length)return '<span style="color:var(--gy);font-size:11px">--</span>';
  const mp={};cls.forEach(l=>{mp[l.default_code]=(mp[l.default_code]||0)+(l.qty||1);});
  const it=Object.entries(mp),MAX=5;
  let h=it.slice(0,MAX).map(([c,q])=>'<span class="mtag">'+c+' x'+q+'</span>').join('');
  if(it.length>MAX)h+='<span style="font-size:10px;color:var(--gy)">+'+(it.length-MAX)+' mas</span>';
  return h;
}
function buildSOTable(rows){
  const tb=sel('so-tbody');tb.innerHTML='';sel('so-badge').textContent=rows.length+' SOs';
  rows.forEach((r,i)=>{
    const cls=r.cost_lines||[],hasL=cls.length>0;
    const tP=r.request_type==='Loan'?'<span class="pill p-loan">Loan</span>':'<span class="pill p-demo">Demo</span>';
    const cP=r.cost_type==='direct_stock'?'<span class="pill p-dir">Direct</span>':r.cost_type==='hidden_lot'?'<span class="pill p-hid">Hidden</span>':'<span class="pill p-zer">Sin coste</span>';
    const ac=AREA_CLS[r.area]||'p-zer',xb=hasL?'<button class="xbtn" onclick="tog('+i+')">&#9654;</button>':'';
    const tr=document.createElement('tr');
    tr.innerHTML='<td>'+xb+'</td><td style="font-weight:600;font-family:monospace;font-size:12px">'+r.transfer+'</td><td style="font-size:11px">'+r.form_requester+'</td><td><span class="pill '+ac+'">'+r.area+'</span></td><td>'+tP+'</td><td>'+fmtD(r.rti_date||'')+'</td><td>'+cP+'</td><td>'+matTags(cls)+'</td><td class="cr '+(r.total_cost===0?'zero':'')+'">'+fmt(r.total_cost)+'</td>';
    tb.appendChild(tr);
    if(hasL){
      const ints=[...new Set(cls.map(l=>l.picking))];
      const pR=cls.map(l=>'<div class="prd-row"><span class="prd-code">'+l.default_code+'</span><span style="color:var(--gy)">'+l.product_name+'</span><span style="text-align:center">'+l.qty+'x</span><span style="color:var(--gy)">'+fmt(l.unit_price)+'</span><span class="prd-tot">'+fmt(l.line_cost)+'</span></div>').join('');
      const dt=document.createElement('tr');dt.className='det-row';dt.id='det-'+i;
      dt.innerHTML='<td colspan="9"><div class="det-inner"><div class="det-info"><div>SO: <b>'+r.transfer+'</b></div><div>RTI: <b>'+(r.rti_picking||'--')+'</b> | '+fmtD(r.rti_date||'')+'</div><div>INT: <b>'+ints.join(', ')+'</b></div><div>Solicitante: <b>'+r.form_requester+'</b> | '+r.area+'</div></div><div class="prd-hdr" style="margin-top:8px"><span>Codigo</span><span>Producto</span><span>Cant</span><span>Precio unit</span><span style="text-align:right">Total</span></div>'+pR+'<div class="det-sum"><span>Total: <b>'+fmt(r.total_cost)+'</b></span><span>INT: <b>'+ints.join(', ')+'</b></span></div></div></td>';
      tb.appendChild(dt);
    }
  });
}
function buildINTTable(ir){
  const tb=sel('int-tbody');tb.innerHTML='';sel('int-badge').textContent=ir.length+' INTs';let tot=0;
  ir.forEach(function(r){
    const i=ALL_INT.indexOf(r);tot+=r.total_cost;const hasL=r.cost_lines&&r.cost_lines.length>0;
    const xb=hasL?'<button class="xbtn" data-i="'+i+'" onclick="togI(this.dataset.i)">&#9654;</button>':'';
    const area=r.area||'--',ac=AREA_CLS[area]||'p-int';
    const ctCls=r.cost_type==='direct_stock'?'p-dir':r.cost_type==='hidden_lot'?'p-hid':'p-zer';
    const ctLbl=r.cost_type==='direct_stock'?'Directo':r.cost_type==='hidden_lot'?'Hidden':'Sin coste';
    const tr=document.createElement('tr');
    tr.innerHTML='<td>'+xb+'</td><td style="font-weight:600;font-family:monospace;font-size:12px">'+r.transfer+'</td><td style="font-size:11px;color:var(--gy)">'+(r.customer||r.note||'--')+'</td><td><span class="pill '+ac+'">'+area+'</span></td><td><span class="pill '+ctCls+'">'+ctLbl+'</span></td><td class="cr'+(r.total_cost===0?' zero':'')+'">'+fmt(r.total_cost)+'</td>';
    tb.appendChild(tr);
    if(hasL){
      const pR=(r.cost_lines||[]).filter(l=>(l.line_cost||0)>0).map(l=>'<div class="prd-row"><span class="prd-code">'+(l.default_code||'')+'</span><span style="color:var(--gy)">'+(l.product_name||'')+'</span><span style="text-align:center">'+(l.qty||1)+'x</span><span style="color:var(--gy)">'+fmt(l.unit_price||0)+'</span><span class="prd-tot">'+fmt(l.line_cost||0)+'</span></div>').join('');
      const dt=document.createElement('tr');dt.className='det-row';dt.id='deti-'+i;
      dt.innerHTML='<td colspan="6"><div class="det-inner"><div class="prd-hdr" style="margin-top:4px"><span>Codigo</span><span>Producto</span><span>Cant</span><span>Precio unit</span><span style="text-align:right">Total</span></div>'+pR+'</div></td>';
      tb.appendChild(dt);
    }
  });
  sel('int-foot').textContent=fmt(tot);
}
function tog(i){const e=sel('det-'+i);if(!e)return;const b=e.previousElementSibling.querySelector('.xbtn');const s=e.style.display!=='table-row';e.style.display=s?'table-row':'none';if(b)b.innerHTML=s?'&#9660;':'&#9654;';}
function togI(i){const e=sel('deti-'+i);if(!e)return;const b=e.previousElementSibling.querySelector('.xbtn');const s=e.style.display!=='table-row';e.style.display=s?'table-row':'none';if(b)b.innerHTML=s?'&#9660;':'&#9654;';}
function getFiltered(){const a=sel('f-area').value,t=sel('f-type').value,y=sel('f-year').value;return ALL_SO.filter(r=>{if(a&&r.area!==a)return false;if(t&&r.request_type!==t)return false;if(y&&String(r.year)!==y)return false;return true;});}
function getIntFiltered(){const a=sel('f-area').value,y=sel('f-year').value;return ALL_INT.filter(r=>{if(a&&r.area!==a)return false;if(y&&String(r.year)!==y)return false;return true;});}
function applyFilters(){const f=getFiltered(),fi=getIntFiltered();buildSOTable(f);buildINTTable(fi);buildKPIs(f,fi);buildCharts(f,fi);}
function resetFilters(){['f-area','f-type','f-year'].forEach(id=>sel(id).value='');applyFilters();}
applyFilters();
(function(){const areas=new Set([...ALL_SO.map(r=>r.area),...ALL_INT.map(r=>r.area)]);[...areas].sort().forEach(a=>{const o=document.createElement('option');o.value=a;o.textContent=a;sel('f-area').appendChild(o);});})();
</script></body></html>"""

html = (HEADER.replace('TODAY_PH', today)
        + f'const D={D_pay};\n'
        + f'const D25={D25_pay};\n'
        + 'const ALL_SO=[...D25.so_rows,...D.so_rows];\n'
        + f'const ENG_PM_ROWS={EP_pay};\n'
        + 'const ALL_INT=[...D.int_rows,...ENG_PM_ROWS];\n'
        + FOOTER)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'index.html written  ({len(html):,} bytes)')
