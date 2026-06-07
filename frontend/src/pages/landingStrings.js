// All Landing-page copy lives here so the page itself stays markup-only.
// Adding a third language is just a new key alongside `en` and `tr`.
//
// Why a flat strings module instead of i18next? The Landing page is the
// only public-facing localised surface; pulling in a full i18n framework
// for one page is overkill. When (if) we localise the in-app pages we
// can graduate this to react-intl or i18next without touching markup.

export const STRINGS = {
  en: {
    nav: {
      links: [
        { id: 'features', label: 'Features' },
        { id: 'how-it-works', label: 'How It Works' },
        { id: 'pricing', label: 'Pricing' },
        { id: 'why-us', label: 'Why Us' },
        { id: 'contact', label: 'Contact' },
      ],
      signIn: 'Sign In',
      getStarted: 'Get Started',
      languageLabel: 'Language',
    },
    hero: {
      badge: 'AI-Powered Medical Intelligence',
      titleLine1: 'Your Intelligent',
      titleLine2: 'Medical Companion',
      subtitle:
        'MedicaLLM combines a comprehensive drug database, real-time PubMed research, and a privacy-first AI agent to deliver evidence-based medical insights — instantly.',
      ctaPrimary: 'Start For Free',
      ctaSecondary: 'See Features',
      note: 'No credit card required · Free tier available',
      labelYou: 'You',
      labelAI: 'MedicaLLM',
      // The terminal mock cycles through these example dialogues. Each
      // entry is one full round (user prompt + assistant reply with
      // optional intermediate "thinking" line). The component types the
      // text out one character at a time, pauses, then moves on.
      conversations: [
        {
          question: 'Does Warfarin interact with Ibuprofen?',
          thinking: 'Searching for safe alternatives…',
          answer: {
            pre: 'Yes — concurrent use significantly raises bleeding risk. Consider ',
            strong: 'Acetaminophen',
            post: ' as a safer analgesic; it doesn\u2019t affect platelet function or anticoagulant activity.',
          },
        },
        {
          question: 'What\u2019s the recommended dose for amoxicillin in adults?',
          thinking: 'Pulling dosing data…',
          answer: {
            pre: 'For most uncomplicated infections: ',
            strong: '500 mg every 8 hours',
            post: ' or 875 mg every 12 hours. Adjust for renal impairment when CrCl < 30 mL/min.',
          },
        },
        {
          question: 'Latest research on SGLT2 inhibitors and heart failure?',
          thinking: 'Querying PubMed…',
          answer: {
            pre: 'Recent meta-analyses (',
            strong: 'EMPEROR-Reduced, DAPA-HF',
            post: ') show a ~25% reduction in cardiovascular death or HF hospitalisation across both diabetic and non-diabetic patients.',
          },
        },
        {
          question: 'My patient is on Lisinopril — can they take Ibuprofen?',
          thinking: 'Checking interaction matrix…',
          answer: {
            pre: 'Caution. NSAIDs reduce ACE inhibitor efficacy and can ',
            strong: 'worsen renal function',
            post: ', especially in dehydrated or elderly patients. Prefer Acetaminophen for short-term pain relief.',
          },
        },
      ],
    },
    features: {
      titleLine1: 'Everything You Need for',
      titleLine2: 'Smarter Medical Decisions',
      subtitle:
        'From quick drug lookups to full patient safety analyses — MedicaLLM has you covered.',
      items: [
        { title: 'Drug Information', desc: 'Access comprehensive drug data — indications, mechanisms, side effects, metabolism, and more.' },
        { title: 'Interaction Checker', desc: 'Instantly check drug-drug and drug-food interactions with severity levels and safe alternative recommendations.' },
        { title: 'PubMed Research', desc: 'Search published medical literature with confidence scoring based on citations, recency, and evidence level.' },
        { title: 'RAG-Powered Docs', desc: 'Upload and query medical guidelines and PDFs using retrieval-augmented generation for precise answers.' },
        { title: 'Patient Analysis', desc: 'Healthcare professionals can run full medication safety analyses — pairwise interactions and allergy conflicts.' },
        { title: 'AI Conversational Agent', desc: 'Chat naturally with MedicaLLM. It understands context, remembers your conversation, and cites its sources.' },
      ],
    },
    steps: {
      title: 'How It Works',
      subtitle: 'Get from question to answer in four simple steps.',
      items: [
        { title: 'Create Your Account', desc: 'Sign up in seconds as a general user or healthcare professional.' },
        { title: 'Ask a Question', desc: 'Type a drug name, describe symptoms, or ask about interactions — just like talking to a colleague.' },
        { title: 'Get Evidence-Based Answers', desc: 'MedicaLLM searches its drug database, PubMed, and your uploaded documents to deliver cited, reliable responses.' },
        { title: 'Take Action', desc: 'Review alternatives, export reports, and make informed clinical or personal health decisions.' },
      ],
    },
    pricing: {
      title: 'Simple, Transparent Pricing',
      subtitle: 'Start free. Upgrade when you\u2019re ready.',
      plans: [
        {
          name: 'Starter',
          price: 'Free',
          period: '',
          features: ['Drug information lookup', 'Basic interaction checks', '20 queries / day', 'Community support'],
          cta: 'Get Started',
          status: 'live',
        },
        {
          name: 'Professional',
          price: '$29',
          period: '/month',
          features: ['Everything in Starter', 'Unlimited queries', 'PubMed research access', 'Patient management', 'PDF document upload', 'Priority support'],
          cta: 'Notify Me',
          status: 'coming-soon',
        },
        {
          name: 'Enterprise',
          price: 'Custom',
          period: '',
          features: ['Everything in Professional', 'Dedicated instance', 'Custom LLM fine-tuning', 'SSO & KVKK compliance', 'API access', 'Dedicated account manager'],
          cta: 'Contact Sales',
          status: 'contact',
        },
      ],
      popularBadge: 'Most Popular',
      comingSoonBadge: 'Coming Soon',
    },
    why: {
      title: 'Why MedicaLLM?',
      subtitle: 'Built different — by design.',
      items: [
        { title: 'Privacy First', desc: 'Runs on local LLMs via Ollama — your data never leaves your infrastructure.' },
        { title: 'Evidence-Based', desc: 'Every answer is grounded in our drug database, PubMed literature, and your own documents.' },
        { title: 'Real-Time Streaming', desc: "See answers as they're generated with live token streaming — no waiting for full responses." },
        { title: 'Context-Aware', desc: 'Role-aware prompts adapt language for clinicians vs. general users. Patient context is injected per query.' },
      ],
    },
    contact: {
      title: 'Get In Touch',
      subtitle:
        "Have questions, need a demo, or want to discuss enterprise plans? We'd love to hear from you.",
      emailLabel: 'Email',
      emailValue: 'contact@medicallm.com.tr',
      locationLabel: 'Location',
      locationValue: 'Istanbul, Turkey',
      formNamePlaceholder: 'Your Name',
      formEmailPlaceholder: 'Your Email',
      formSubjectPlaceholder: 'Subject',
      formMessagePlaceholder: 'Your Message',
      formSubmit: 'Send Message',
    },
    footer: {
      tagline: 'AI-powered medical intelligence.\nEvidence-based. Privacy-first.',
      productHeading: 'Product',
      companyHeading: 'Company',
      legalHeading: 'Legal',
      productLinks: [
        { label: 'Features', target: 'features' },
        { label: 'Pricing', target: 'pricing' },
        { label: 'How It Works', target: 'how-it-works' },
      ],
      companyLinks: [
        { label: 'About', target: 'why-us' },
        { label: 'Contact', target: 'contact' },
        { label: 'Careers', target: null },
      ],
      legalLinks: [
        { label: 'Privacy Policy', target: null },
        { label: 'Terms of Service', target: null },
        { label: 'KVKK Compliance', target: null },
      ],
      copyright: '\u00A9 2026 MedicaLLM. All rights reserved.',
    },
  },

  tr: {
    nav: {
      links: [
        { id: 'features', label: 'Özellikler' },
        { id: 'how-it-works', label: 'Nasıl Çalışır' },
        { id: 'pricing', label: 'Fiyatlandırma' },
        { id: 'why-us', label: 'Neden Biz' },
        { id: 'contact', label: 'İletişim' },
      ],
      signIn: 'Giriş Yap',
      getStarted: 'Başla',
      languageLabel: 'Dil',
    },
    hero: {
      badge: 'Yapay Zekâ Destekli Tıbbi Zekâ',
      titleLine1: 'Akıllı',
      titleLine2: 'Tıbbi Yardımcınız',
      subtitle:
        'MedicaLLM kapsamlı bir ilaç veritabanını, gerçek zamanlı PubMed taramasını ve gizliliği ön planda tutan bir yapay zekâ asistanını birleştirir — kanıta dayalı tıbbi bilgilere anında ulaşın.',
      ctaPrimary: 'Ücretsiz Başla',
      ctaSecondary: 'Özellikleri Gör',
      note: 'Kredi kartı gerekmez · Ücretsiz paket mevcuttur',
      labelYou: 'Sen',
      labelAI: 'MedicaLLM',
      conversations: [
        {
          question: 'Warfarin ile Ibuprofen etkileşir mi?',
          thinking: 'Güvenli alternatifler aranıyor…',
          answer: {
            pre: 'Evet — birlikte kullanım kanama riskini belirgin artırır. Daha güvenli bir analjezik için ',
            strong: 'Parasetamol',
            post: ' düşünülebilir; trombosit fonksiyonunu veya antikoagülan aktiviteyi etkilemez.',
          },
        },
        {
          question: 'Erişkinlerde amoksisilin önerilen dozu nedir?',
          thinking: 'Dozaj verisi çekiliyor…',
          answer: {
            pre: 'Komplike olmayan enfeksiyonlarda: ',
            strong: 'Her 8 saatte bir 500 mg',
            post: ' veya 12 saatte bir 875 mg. CrCl < 30 mL/dk ise renal yetersizliğe göre doz ayarlayın.',
          },
        },
        {
          question: 'SGLT2 inhibitörleri ve kalp yetmezliği üzerine güncel kanıt?',
          thinking: 'PubMed sorgulanıyor…',
          answer: {
            pre: 'Yeni meta-analizler (',
            strong: 'EMPEROR-Reduced, DAPA-HF',
            post: ') diyabetik ve diyabetik olmayan hastalarda kardiyovasküler ölüm veya KY hastaneye yatışında ~%25 azalma gösteriyor.',
          },
        },
        {
          question: 'Lisinopril kullanan hastam Ibuprofen alabilir mi?',
          thinking: 'Etkileşim matrisi kontrol ediliyor…',
          answer: {
            pre: 'Dikkat. NSAID\u2019ler ACE inhibitörlerinin etkinliğini azaltır ve özellikle dehidrate veya yaşlı hastalarda ',
            strong: 'renal fonksiyonu kötüleştirebilir',
            post: '. Kısa süreli ağrı için Parasetamol tercih edin.',
          },
        },
      ],
    },
    features: {
      titleLine1: 'Daha Akıllı Tıbbi Kararlar İçin',
      titleLine2: 'İhtiyacınız Olan Her Şey',
      subtitle:
        'Hızlı ilaç sorgularından kapsamlı hasta güvenliği analizlerine — MedicaLLM yanınızda.',
      items: [
        { title: 'İlaç Bilgisi', desc: 'Kapsamlı ilaç verisine erişin — endikasyonlar, etki mekanizmaları, yan etkiler, metabolizma ve daha fazlası.' },
        { title: 'Etkileşim Kontrolü', desc: 'İlaç-ilaç ve ilaç-besin etkileşimlerini şiddet seviyesi ile birlikte kontrol edin, güvenli alternatif önerileri alın.' },
        { title: 'PubMed Araştırması', desc: 'Yayımlanmış tıbbi literatürü atıf, güncellik ve kanıt seviyesine göre güven puanlamasıyla tarayın.' },
        { title: 'RAG Destekli Belgeler', desc: 'Tıbbi kılavuzları ve PDF belgelerini yükleyin, retrieval-augmented generation ile hassas yanıtlar alın.' },
        { title: 'Hasta Analizi', desc: 'Sağlık profesyonelleri tam ilaç güvenliği analizleri yapabilir — ikili etkileşimler ve alerji çakışmaları.' },
        { title: 'Yapay Zekâ Asistanı', desc: 'MedicaLLM ile doğal sohbet edin. Bağlamı anlar, görüşmenizi hatırlar ve kaynaklarını gösterir.' },
      ],
    },
    steps: {
      title: 'Nasıl Çalışır',
      subtitle: 'Sorudan yanıta dört basit adımda.',
      items: [
        { title: 'Hesap Oluşturun', desc: 'Saniyeler içinde genel kullanıcı veya sağlık profesyoneli olarak kaydolun.' },
        { title: 'Sorunuzu Sorun', desc: 'İlaç adı yazın, semptom tarif edin veya etkileşim sorun — bir meslektaşınızla konuşur gibi.' },
        { title: 'Kanıta Dayalı Yanıtlar Alın', desc: 'MedicaLLM kendi ilaç veritabanını, PubMed\u2019i ve yüklediğiniz belgeleri tarayarak atıflı, güvenilir yanıtlar verir.' },
        { title: 'Aksiyon Alın', desc: 'Alternatifleri inceleyin, raporları dışa aktarın, klinik veya kişisel sağlık kararlarınızı bilinçli verin.' },
      ],
    },
    pricing: {
      title: 'Sade ve Şeffaf Fiyatlandırma',
      subtitle: 'Ücretsiz başlayın. Hazır olduğunuzda yükseltin.',
      plans: [
        {
          name: 'Başlangıç',
          price: 'Ücretsiz',
          period: '',
          features: ['İlaç bilgisi sorgusu', 'Temel etkileşim kontrolleri', 'Günde 20 sorgu', 'Topluluk desteği'],
          cta: 'Başla',
          status: 'live',
        },
        {
          name: 'Profesyonel',
          price: '29 $',
          period: '/ay',
          features: ['Başlangıçtaki her şey', 'Sınırsız sorgu', 'PubMed araştırma erişimi', 'Hasta yönetimi', 'PDF belge yükleme', 'Öncelikli destek'],
          cta: 'Beni Bilgilendir',
          status: 'coming-soon',
        },
        {
          name: 'Kurumsal',
          price: 'Özel',
          period: '',
          features: ['Profesyoneldeki her şey', 'Özel sunucu', 'Özel LLM ince ayarı', 'SSO ve KVKK uyumu', 'API erişimi', 'Özel hesap yöneticisi'],
          cta: 'Satışla İletişime Geç',
          status: 'contact',
        },
      ],
      popularBadge: 'En Popüler',
      comingSoonBadge: 'Yakında',
    },
    why: {
      title: 'Neden MedicaLLM?',
      subtitle: 'Tasarım gereği farklı.',
      items: [
        { title: 'Önce Gizlilik', desc: 'Ollama üzerinden yerel LLM çalıştırılabilir — verileriniz altyapınızdan dışarı çıkmaz.' },
        { title: 'Kanıta Dayalı', desc: 'Her yanıt ilaç veritabanı, PubMed literatürü ve kendi belgelerinizle gerekçelendirilir.' },
        { title: 'Gerçek Zamanlı Akış', desc: 'Yanıtları üretildikçe canlı token akışıyla görün — tam yanıtın gelmesini beklemeyin.' },
        { title: 'Bağlam Farkındalığı', desc: 'Rolleri anlayan promptlar dilini klinisyene veya genel kullanıcıya göre uyarlar. Hasta bağlamı sorguya enjekte edilir.' },
      ],
    },
    contact: {
      title: 'İletişime Geçin',
      subtitle:
        'Sorunuz mu var, demo mu istiyorsunuz, yoksa kurumsal planları mı konuşmak istiyorsunuz? Sizi duymak isteriz.',
      emailLabel: 'E-posta',
      emailValue: 'contact@medicallm.com.tr',
      locationLabel: 'Konum',
      locationValue: 'İstanbul, Türkiye',
      formNamePlaceholder: 'Adınız',
      formEmailPlaceholder: 'E-posta Adresiniz',
      formSubjectPlaceholder: 'Konu',
      formMessagePlaceholder: 'Mesajınız',
      formSubmit: 'Mesajı Gönder',
    },
    footer: {
      tagline: 'Yapay zekâ destekli tıbbi zekâ.\nKanıta dayalı. Gizliliği önemser.',
      productHeading: 'Ürün',
      companyHeading: 'Şirket',
      legalHeading: 'Yasal',
      productLinks: [
        { label: 'Özellikler', target: 'features' },
        { label: 'Fiyatlandırma', target: 'pricing' },
        { label: 'Nasıl Çalışır', target: 'how-it-works' },
      ],
      companyLinks: [
        { label: 'Hakkımızda', target: 'why-us' },
        { label: 'İletişim', target: 'contact' },
        { label: 'Kariyer', target: null },
      ],
      legalLinks: [
        { label: 'Gizlilik Politikası', target: null },
        { label: 'Kullanım Koşulları', target: null },
        { label: 'KVKK Uyumu', target: null },
      ],
      copyright: '\u00A9 2026 MedicaLLM. Tüm hakları saklıdır.',
    },
  },
};

export const SUPPORTED_LANGS = ['en', 'tr'];
export const DEFAULT_LANG = 'en';

const STORAGE_KEY = 'medicallm.lang';

/**
 * Pick a starting language: previous user choice → browser default → English.
 * Safe to call during render (returns DEFAULT_LANG when localStorage is
 * unavailable, e.g. in private mode quotas).
 */
export function detectInitialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;
  } catch {
    // ignored
  }
  if (typeof navigator !== 'undefined') {
    const nav = (navigator.language || '').toLowerCase();
    if (nav.startsWith('tr')) return 'tr';
  }
  return DEFAULT_LANG;
}

export function persistLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // ignored
  }
}
