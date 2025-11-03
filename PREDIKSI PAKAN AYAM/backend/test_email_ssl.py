import smtplib, ssl

EMAIL = "raisyawulan04@gmail.com"
APP_PASSWORD = "sizr qxvt xgem ikin"

context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(
            EMAIL,
            EMAIL,
            "Subject: Test SMTP via SSL\n\nHalo, ini test kirim email via port 465."
        )
    print("✅ Email terkirim via SSL (465), cek inbox/spam Gmail.")
except Exception as e:
    print("❌ Gagal kirim email:", e)
