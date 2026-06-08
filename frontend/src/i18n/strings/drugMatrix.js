/**
 * Drug interaction matrix UI strings.
 *
 * Severity labels are also part of the i18n table so the legend, the
 * cell content, and the detail panel all stay aligned across languages.
 * The keys mirror the scoring buckets in src/pages/DrugMatrix.jsx ::
 * severityLabel().
 */
export const DRUG_MATRIX_STRINGS = {
  en: {
    title: 'Drug Interaction Matrix',
    subtitle: 'Add drugs to see all pairwise interactions at a glance.',
    searchPlaceholder: 'Search drugs to add…',
    loadFromPatient: 'Load from patient…',
    patientMedsHint: (n) => `${n} meds`,
    clearAll: 'Clear all',
    checking: 'Checking interactions…',
    summaryDrugs: 'Drugs',
    summaryFound: 'Interactions Found',
    summaryCritical: 'Critical/Major',
    emptyTitle: 'Add at least 2 drugs',
    emptyDescGeneric: 'Search for drugs above to see the interaction matrix.',
    emptyDescDoctor: "Search for drugs above or load a patient's medication list to see the interaction matrix.",
    detailSafe: 'No known interaction',
    legendHeading: 'Severity Legend',
    severities: {
      Unknown: 'Unknown',
      Minimal: 'Minimal',
      Mild: 'Mild',
      Moderate: 'Moderate',
      'Moderate-High': 'Moderate-High',
      Major: 'Major',
      Critical: 'Critical',
      Contraindicated: 'Contraindicated',
    },
  },
  tr: {
    title: 'İlaç Etkileşim Matrisi',
    subtitle: 'İlaçları ekleyerek tüm ikili etkileşimleri tek bakışta görün.',
    searchPlaceholder: 'Eklenecek ilacı ara…',
    loadFromPatient: 'Hastadan yükle…',
    patientMedsHint: (n) => `${n} ilaç`,
    clearAll: 'Tümünü temizle',
    checking: 'Etkileşimler kontrol ediliyor…',
    summaryDrugs: 'İlaç',
    summaryFound: 'Bulunan Etkileşim',
    summaryCritical: 'Kritik/Major',
    emptyTitle: 'En az 2 ilaç ekleyin',
    emptyDescGeneric: 'Etkileşim matrisini görmek için yukarıdan ilaç arayın.',
    emptyDescDoctor: 'Etkileşim matrisini görmek için yukarıdan ilaç arayın veya bir hastanın ilaç listesini yükleyin.',
    detailSafe: 'Bilinen bir etkileşim yok',
    legendHeading: 'Şiddet Skalası',
    severities: {
      Unknown: 'Bilinmiyor',
      Minimal: 'Minimal',
      Mild: 'Hafif',
      Moderate: 'Orta',
      'Moderate-High': 'Orta-Yüksek',
      Major: 'Yüksek',
      Critical: 'Kritik',
      Contraindicated: 'Kontrendike',
    },
  },
};
