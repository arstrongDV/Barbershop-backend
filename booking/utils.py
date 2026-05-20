import requests
from django.conf import settings

def send_telegram_notification(appointment):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)

    if not token or not chat_id:
        return
    
    services_list = ' ,'.join([s.name for s in appointment.services.all()])

    message = (
        f"🚨 **New Appointment Booking!** 🚨\n\n"
        f"👤 **Customer:** {appointment.customer.fullname}\n"
        f"📞 **Phone:** {appointment.customer.phone}\n"
        f"✉️ **Email:** {appointment.customer.email or 'None'}\n"
        f"🪒 **Barber:** {appointment.barber.name}\n"
        f"💇‍♂️ **Services:** {services_list}\n"
        f"📅 **Date:** {appointment.date}\n"
        f"🕒 **Time:** {appointment.time.strftime('%H:%M')}\n"
        f"💬 **Comment:** {appointment.comment or 'None'}"
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ Approve", 
                    "callback_data": f"approve_{appointment.id}"
                },
                {
                    "text": "❌ Cancel", 
                    "callback_data": f"cancel_{appointment.id}"
                }
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": inline_keyboard
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"Помилка Telegram API: {response.text}")
    except requests.exceptions.RequestException as e:
            print(f"Не вдалося зв'язатися з Telegram: {e}")