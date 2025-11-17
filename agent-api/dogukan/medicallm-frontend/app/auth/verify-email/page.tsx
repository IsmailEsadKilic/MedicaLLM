"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function VerifyEmail() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (code.length !== 6) {
      setError("Kod 6 haneli olmalıdır");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/auth/verify-email`
          : "http://localhost:5000/api/auth/verify-email",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, code }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Doğrulama başarısız");
        setLoading(false);
        return;
      }

      // Email doğrulandı, kayıt sayfasına geri dön
      router.push(`/auth/signup?email=${encodeURIComponent(email)}&verified=true`);
    } catch (error) {
      setError("Bir hata oluştu. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError("");

    try {
      const response = await fetch(
        process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/auth/send-verification`
          : "http://localhost:5000/api/auth/send-verification",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Kod gönderilemedi");
      } else {
        setCountdown(60); // 60 saniye bekle
        setError(""); // Hata mesajını temizle
      }
    } catch (error) {
      setError("Bir hata oluştu. Lütfen tekrar deneyin.");
    } finally {
      setResending(false);
    }
  };

  if (!email) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="w-full max-w-md space-y-8 rounded-lg border bg-card p-8 shadow-lg">
          <div className="text-center">
            <h1 className="text-3xl font-bold">MedicaLLM</h1>
            <p className="mt-2 text-muted-foreground">Email adresi bulunamadı</p>
            <Link href="/auth/signup" className="text-primary hover:underline mt-4 inline-block">
              Kayıt sayfasına dön
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-8 rounded-lg border bg-card p-8 shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold">MedicaLLM</h1>
          <p className="mt-2 text-muted-foreground">Email Doğrulama</p>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-center text-muted-foreground">
            <strong>{email}</strong> adresine gönderilen 6 haneli doğrulama kodunu girin.
          </p>

          <form onSubmit={handleVerify} className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="code" className="text-sm font-medium">
                Doğrulama Kodu
              </label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="w-full rounded-md border bg-background px-3 py-2 text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="000000"
                maxLength={6}
                required
                disabled={loading}
                autoFocus
              />
              <p className="text-xs text-center text-muted-foreground">
                Kod 10 dakika geçerlidir
              </p>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={loading || code.length !== 6}
            >
              {loading ? "Doğrulanıyor..." : "Doğrula"}
            </Button>
          </form>

          <div className="text-center space-y-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleResend}
              disabled={resending || countdown > 0}
              className="w-full"
            >
              {resending
                ? "Gönderiliyor..."
                : countdown > 0
                ? `Tekrar gönder (${countdown}s)`
                : "Kodu Tekrar Gönder"}
            </Button>

            <Link
              href="/auth/signup"
              className="text-sm text-muted-foreground hover:text-foreground inline-block"
            >
              Email adresini değiştir
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

