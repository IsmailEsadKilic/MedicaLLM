C:.
│   .gitignore
│   docker-compose.yml
│   README.md
│
├───.vscode
│       settings.json
│
├───agent-api
│   │   .dockerignore
│   │   .gitignore
│   │   api_server.py
│   │   Dockerfile
│   │   dynamodb_manager.py
│   │   entrypoint.sh
│   │   medical_agent.py
│   │   models.py
│   │   pdf_processor.py
│   │   printmeup.py
│   │   pyproject.toml
│   │   README.md
│   │   session.py
│   │   uv.lock
│   │   vector_store.py
│   │
│   ├───data
│   │   ├───pdf
│   │   │       Drug Interactions—Principles, Examples.pdf
│   │   │       drug_interactions_with_antihypertensives.pdf
│   │   │       Management and Treatment of Hypertensive Emergencies[#676412]-990208.pdf
│   │   │       The Hospital Management of Hypoglycaemia.pdf
│   │   │
│   │   └───xml
│   │       └───drugbank
│   │               drugbank.xsd
│   │
│   ├───drugbank_schema
│   │       drugbank.py
│   │       __init__.py
│   │
│   ├───scripts
│   │       docker-compose.yml
│   │       printmeup.py
│   │       setup_database.py
│   │
│   └───static
│           favicon.ico
│
├───backend
│   │   .dockerignore
│   │   Dockerfile
│   │   package-lock.json
│   │   package.json
│   │   README.md
│   │   test-db.js
│   │   tsconfig.json
│   │
│   └───src
│       │   index.ts
│       │
│       ├───db
│       │       dynamodb.ts
│       │       init.ts
│       │       setup.ts
│       │       setupUsers.ts
│       │
│       ├───middleware
│       │       auth.ts
│       │
│       ├───routes
│       │       auth.ts
│       │       conversations.ts
│       │       drugs.ts
│       │       drugSearch.ts
│       │       items.ts
│       │       patients.ts
│       │
│       └───services
│               agentApiService.ts
│
└───frontend
    │   .dockerignore
    │   Dockerfile
    │   index.html
    │   package-lock.json
    │   package.json
    │   test.html
    │   vite.config.js
    │
    └───src
        │   App.css
        │   App.jsx
        │   Auth.css
        │   Auth.jsx
        │   main.jsx
        │
        ├───api
        │       config.js
        │
        └───pages
                Chat.jsx
                DrugSearch.jsx
                DrugSearchTest.jsx
                Login.jsx
                PatientAnalysis.css
                PatientAnalysis.jsx
                Patients.jsx
                Register.jsx