// Email service - SMTP ile gerçek email gönderimi
import nodemailer from "nodemailer";

// SMTP transporter oluştur
function createTransporter() {
  const smtpConfig = {
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || "587"),
    secure: process.env.SMTP_SECURE === "true", // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASSWORD,
    },
  };

  // Tüm SMTP ayarları varsa transporter oluştur
  if (smtpConfig.host && smtpConfig.auth.user && smtpConfig.auth.pass) {
    return nodemailer.createTransport(smtpConfig);
  }

  return null;
}

export async function sendVerificationEmail(
  email: string,
  code: string
): Promise<boolean> {
  try {
    const transporter = createTransporter();

    // SMTP yapılandırılmamışsa console'a yazdır (development)
    if (!transporter) {
      console.log("\n📧 ===== EMAIL DOĞRULAMA KODU =====");
      console.log(`📬 Alıcı: ${email}`);
      console.log(`🔐 Doğrulama Kodu: ${code}`);
      console.log(`⏰ Kod 10 dakika geçerlidir`);
      console.log("=====================================\n");
      console.log("⚠️ SMTP yapılandırılmamış - Email gönderilmedi");
      return true; // Development için true döndür
    }

    // Email içeriği
    const mailOptions = {
      from: process.env.SMTP_FROM || process.env.SMTP_USER,
      to: email,
      subject: "MedicaLLM - Email Doğrulama Kodu",
      html: `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
              }
              .container {
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 30px;
                margin: 20px 0;
              }
              .code {
                background-color: #4F46E5;
                color: white;
                font-size: 32px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                border-radius: 8px;
                letter-spacing: 8px;
                margin: 20px 0;
              }
              .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>MedicaLLM Email Doğrulama</h1>
              <p>Merhaba,</p>
              <p>MedicaLLM hesabınızı oluşturmak için aşağıdaki doğrulama kodunu kullanın:</p>
              
              <div class="code">${code}</div>
              
              <p>Bu kod <strong>10 dakika</strong> geçerlidir.</p>
              <p>Eğer bu işlemi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.</p>
              
              <div class="footer">
                <p>Bu email MedicaLLM tarafından otomatik olarak gönderilmiştir.</p>
              </div>
            </div>
          </body>
        </html>
      `,
      text: `
MedicaLLM Email Doğrulama

Merhaba,

MedicaLLM hesabınızı oluşturmak için aşağıdaki doğrulama kodunu kullanın:

${code}

Bu kod 10 dakika geçerlidir.

Eğer bu işlemi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.

---
Bu email MedicaLLM tarafından otomatik olarak gönderilmiştir.
      `,
    };

    // Email gönder
    const info = await transporter.sendMail(mailOptions);
    console.log("✅ Email gönderildi:", info.messageId);
    return true;
  } catch (error: any) {
    console.error("❌ Email gönderme hatası:", error);
    // Hata olsa bile development modunda true döndür
    if (!process.env.SMTP_HOST) {
      return true;
    }
    return false;
  }
}
