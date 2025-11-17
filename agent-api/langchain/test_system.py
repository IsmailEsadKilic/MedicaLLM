"""
Hızlı Test Scripti
Sistemin çalışıp çalışmadığını test eder
"""

import os
import sys



def test_ollama():
    """Ollama bağlantısını test et"""
    print("\n🔗 Ollama bağlantı testi...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            print(f"✓ Ollama çalışıyor")
            print(f"  Mevcut modeller: {', '.join(models)}")
            
            if 'llama2:latest' in models or 'llama2' in [m.split(':')[0] for m in models]:
                print("✓ llama2 modeli bulundu")
                return True
            else:
                print("⚠ llama2 modeli bulunamadı")
                print("  Çalıştırın: ollama pull llama2:latest")
                return False
        else:
            print(f"✗ Ollama yanıt vermiyor (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"✗ Ollama bağlantı hatası: {e}")
        print("  Ollama çalışıyor mu? Çalıştırın: ollama serve")
        return False

def test_pdfs():
    """PDF dosyalarını kontrol et"""
    print("\n📄 PDF dosyaları kontrol ediliyor...")
    
    data_dir = './data'
    if not os.path.exists(data_dir):
        print(f"✗ {data_dir} klasörü bulunamadı")
        return False
    
    pdfs = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    if pdfs:
        print(f"✓ {len(pdfs)} PDF bulundu:")
        for pdf in pdfs:
            pdf_path = os.path.join(data_dir, pdf)
            size = os.path.getsize(pdf_path) / 1024
            print(f"  - {pdf} ({size:.2f} KB)")
        return True
    else:
        print("✗ PDF bulunamadı")
        return False

def test_simple_llm():
    """Basit LLM testi"""
    print("\n🤖 LLM testi...")
    
    try:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            model="llama2:latest",
            temperature=0.7,
            base_url="http://localhost:11434"
        )
        
        print("  Sorgu gönderiliyor: 'Hello, say hi!'")
        response = llm.invoke("Hello, say hi in one sentence!")
        
        print(f"✓ LLM yanıt verdi")
        print(f"  Yanıt: {response.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"✗ LLM testi başarısız: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("="*60)
    print("🧪 LangChain RAG & Agent Sistem Testi")
    print("="*60 + "\n")
    
    tests = [
        ("Ollama Bağlantısı", test_ollama),
        ("PDF Dosyaları", test_pdfs),
        ("LLM Testi", test_simple_llm)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} hatası: {e}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print("\n" + "="*60)
    print("📊 TEST SONUÇLARI")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"Sonuç: {passed}/{total} test başarılı")
    print("="*60)
    
    if passed == total:
        print("\n✨ Tüm testler başarılı! main.py'yi çalıştırabilirsiniz.")
        print("   Çalıştır: python main.py")
    else:
        print("\n⚠️  Bazı testler başarısız. Lütfen hataları düzeltin.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test kullanıcı tarafından durduruldu.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
