# MedicaLLM

[![CI](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/ci.yml/badge.svg)](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/ci.yml)
[![Deploy](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/deploy.yml/badge.svg)](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/deploy.yml)
[![Health Monitor](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/health-monitor.yml/badge.svg)](https://github.com/IsmailEsadKilic/MedicaLLM/actions/workflows/health-monitor.yml)

Evidence-based medical AI assistant. Drug interactions, PubMed-grounded
research, patient-aware consultations.

Live: <https://medicallm.com.tr>

## Quick links

- **What's deployed?** <https://medicallm.com.tr/api/version>
- **Health probe:** <https://medicallm.com.tr/health>
- [Deployment & operations guide](DEPLOYMENT.md)
- [GitHub Actions](https://github.com/IsmailEsadKilic/MedicaLLM/actions)

## Local development

```bash
# Backend
cd backend
uv sync
uv run python run.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

Push to `main` → automatic deploy via GitHub Actions. Full process and
rollback details in [DEPLOYMENT.md](DEPLOYMENT.md).
