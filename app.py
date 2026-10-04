from flask import Flask, request
import requests
import os
import sqlite3

app = Flask(__name__)

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "sufara123")
GRAPH_API_VERSION = "v20.0"
WEBSITE = "https://sufaraulhuda.com"
CONTACT = "0329-4526681"
DATABASE = "/tmp/users.db"

def init_database():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, language TEXT DEFAULT 'en')")
    conn.commit()
    conn.close()
init_database()

def get_language(phone):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE phone =?", (phone,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None

def save_language(phone, language):
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT INTO users (phone, language) VALUES (?,?) ON CONFLICT(phone) DO UPDATE SET language = excluded.language", (phone, language))
    conn.commit()
    conn.close()

def whatsapp_url():
    return f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"

def send_request(data):
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    try:
        requests.post(whatsapp_url(), headers=headers, json=data, timeout=15)
    except Exception as e:
        print("Error:", e)

def send_text(to, text):
    send_request({"messaging_product": "whatsapp","to": to,"type": "text","text": {"body": text}})

def send_language_menu(to):
    send_request({"messaging_product": "whatsapp","to": to,"type": "interactive","interactive": {"type": "button","body": {"text": "🌙 Assalamu Alaikum!\nWelcome to Sufara-ul-Huda Online Quran Academy 📖\nPlease select your language:"},"action": {"buttons": [{"type": "reply","reply": {"id": "lang_urdu","title": "اردو"}},{"type": "reply","reply": {"id": "lang_english","title": "English"}}]}}})

def send_urdu_menu(to):
    send_request({"messaging_product": "whatsapp","to": to,"type": "interactive","interactive": {"type": "list","body": {"text": "🌙 *السلام علیکم!*\nسفراء الہدیٰ میں خوش آمدید 📖\nبراہِ کرم ایک option منتخب کریں:"},"action": {"button": "Menu کھولیں","sections": [{"title": "Academy Services","rows": [{"id": "ur_fees","title": "💰 فیس","description": "کورسز اور فیس"},{"id": "ur_trial","title": "🎁 مفت ٹرائل","description": "3 دن Free Trial"},{"id": "ur_admission","title": "📝 داخلہ","description": "Admission"},{"id": "ur_courses","title": "📚 کورسز","description": "Quran Courses"},{"id": "ur_ceo","title": "👤 CEO سے رابطہ"},{"id": "ur_website","title": "🌐 ویب سائٹ"}]}]}}})

def send_english_menu(to):
    send_request({"messaging_product": "whatsapp","to": to,"type": "interactive","interactive": {"type": "list","body": {"text": "🌙 *Assalamu Alaikum!*\nWelcome to Sufara-ul-Huda 📖\nPlease select an option:"},"action": {"button": "Open Menu","sections": [{"title": "Academy Services","rows": [{"id": "en_fees","title": "💰 Fees"},{"id": "en_trial","title": "🎁 Free Trial"},{"id": "en_admission","title": "📝 Admission"},{"id": "en_courses","title": "📚 Courses"},{"id": "en_ceo","title": "👤 Contact CEO"},{"id": "en_website","title": "🌐 Website"}]}]}}})

def urdu_fees(): return f"💰 *فیس* 3000 PKR / $25 USD\n🎁 3 دن FREE TRIAL\n🌐 {WEBSITE}"
def urdu_trial(): return "🎁 *3 دن کا مفت ٹرائل*\nنام، عمر، کورس، ملک، ٹائم بھیجیں"
def urdu_admission(): return f"📝 *داخلہ*\nنام، عمر، کورس، ملک، وقت بھیجیں\n🌐 {WEBSITE}\n📞 {CONTACT}"
def urdu_courses(): return "📚 *کورسز*\n1️⃣ ناظرہ 2️⃣ حفظ 3️⃣ تجوید 4️⃣ اسلامیات"
def urdu_ceo(): return f"👤 *CEO Abdullah Arif* دستیاب نہیں، پیغام موصول ہو گیا\n🌐 {WEBSITE}"
def urdu_website(): return f"🌐 {WEBSITE}"
def english_fees(): return f"💰 *Fees* 3000 PKR / $25 USD\n🎁 Free Trial\n🌐 {WEBSITE}"
def english_trial(): return "🎁 *3-Day FREE TRIAL*\nSend Name, Age, Course, Country, Time"
def english_admission(): return f"📝 *Admission*\nSend Name, Age, Course\n🌐 {WEBSITE}\n📞 {CONTACT}"
def english_courses(): return "📚 *Courses*\n1️⃣ Nazra 2️⃣ Hifz 3️⃣ Tajweed 4️⃣ Islamic Studies"
def english_ceo(): return f"👤 *CEO Abdullah Arif* unavailable, message received\n🌐 {WEBSITE}"
def english_website(): return f"🌐 {WEBSITE}"

def get_interactive_id(msg):
    if msg.get("type") == "interactive":
        inter = msg.get("interactive", {})
        if inter.get("type") == "button_reply": return inter.get("button_reply", {}).get("id")
        if inter.get("type") == "list_reply": return inter.get("list_reply", {}).get("id")
    return None

@app.route("/")
def home(): return "Sufara-ul-Huda Bot Running! ✅"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        if data.get("object")!= "whatsapp_business_account": return "OK", 200
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if not messages: continue
                msg = messages[0]
                from_number = msg.get("from")
                iid = get_interactive_id(msg)
                if iid:
                    if iid == "lang_urdu": save_language(from_number, "ur"); send_text(from_number, "اردو منتخب"); send_urdu_menu(from_number); continue
                    if iid == "lang_english": save_language(from_number, "en"); send_text(from_number, "English selected"); send_english_menu(from_number); continue
                    lang = get_language(from_number) or "en"
                    mp = {"ur_fees": urdu_fees, "ur_trial": urdu_trial, "ur_admission": urdu_admission, "ur_courses": urdu_courses, "ur_ceo": urdu_ceo, "ur_website": urdu_website, "en_fees": english_fees, "en_trial": english_trial, "en_admission": english_admission, "en_courses": english_courses, "en_ceo": english_ceo, "en_website": english_website}
                    if iid in mp: send_text(from_number, mp[iid]())
                    continue
                if msg.get("type") == "text":
                    if not get_language(from_number): send_language_menu(from_number)
                    else:
                        l = get_language(from_number)
                        if l == "ur": send_urdu_menu(from_number)
                        else: send_english_menu(from_number)
    except Exception as e: print(e)
    return "OK", 200
