import smtplib, ssl

EMAIL = "raisyawulan04@gmail.com"
APP_PASSWORD = "isi_dengan_app_password_gmail_16_digit"

context = ssl.create_default_context()

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)  # upgrade koneksi jadi TLS
        server.login(EMAIL, APP_PASSWORD)  # login pakai email + app password
        server.sendmail(
            EMAIL,
            EMAIL,  # bisa juga ke email lain
            "Subject: Test SMTP\n\nHalo, ini test kirim email dari Python."
        )
    print("✅ Email terkirim, cek inbox/spam Gmail.")
except Exception as e:
    print("❌ Gagal kirim email:", e)
