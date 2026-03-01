# **CSE 401 Senior Design Project Progress Report** **Deliverable 2**

## 

## **Team Members:**

Arda Ünal  
Doğukan Gökdüman  
İsmail Esad Kılıç  
Özge Şahin

## 

## 

## **Project Customer:**

Prof. Dr. Uğur Sezerman

#### **Senior Design Project Title:**

#### Agentic AI Drug Consultant For Doctors And Patients  **Senior Design Project Abstract (200 words):**

Our project aims to develop an AI-powered medical assistant that provides accurate and personalized information about drug interactions and usage. The system will utilize data from trusted sources such as DrugBank, Medscape, or medical data provided by our university’s faculty of medicine — or we may generate our own dataset.

The chatbot will be designed for both healthcare professionals and the general public. It can help doctors understand whether a drug from another specialty can be used safely, providing detailed medical explanations for experts or simplified explanations for regular users.

In addition to the chatbot, there will be a separate section where users can simply enter the names of two or more drugs to check for potential harmful interactions. Moreover, by integrating patient health records, the system will generate personalized recommendations based on the user’s medical history, current medications, and diagnosed conditions.

This project aims to make medical information more accessible, reduce prescription errors, and assist both patients and doctors in making safer, data-driven healthcare decisions. 

#### **Senior Design Project Keywords (at least 3 keywords; comma-separated):** 

LLM Agent (Large Language Model Agent), RAG (retrieval augmented generation), AI Assistant, Prescriptions, Drug-Drug Interactions

**Senior Design Project Technical Report**

**1\. Problem statement and goals**						        \[20%\]  
Problems:

* Medication errors and harmful drug interactions are a major global health concern.  
* Doctors may not always know drugs outside their specialty.  
* Patients often cannot understand complex medical explanations.  
* Existing tools provide fragmented or overly technical information.

Goals:

* Build an AI-powered assistant to detect potential drug interactions.  
* Provide two explanation levels: detailed (for doctors) and simplified (for patients).  
* Allow users to either chat or directly enter drug names to check compatibility.  
* Integrate patient data (past drugs, diseases) for personalized recommendations.  
* Improve medication safety and accessibility through intelligent automation.

**2\. Literature review** 						                      \[10%\]

Drug–Drug Interaction Prediction:

* Models like SSF-DDI use chemical sequences and molecular substructures to predict pairwise drug interactions.  
* Effective for binary drug interaction checks but limited to two-drug combinations and lacks detailed clinical explanations.

Graph-Based Approaches:

* Decagon models drugs, proteins, and side effects as a heterogeneous graph to predict multi-drug interactions and specific side effect types.  
* Captures network-level interactions but does not provide full mechanistic explanations for clinicians.

Knowledge-Based Systems:

* Databases such as DrugBank, Medscape, and SIDER provide curated information about drug targets, metabolic pathways, and known side effects.  
* Useful for cross-referencing predictions and explaining underlying mechanisms.

AI-Powered Clinical Assistants:

* Large Language Models (LLMs) can interpret predictions and generate human-readable explanations.  
    
  

**3\. Methodology** 								        \[40%\]

1. Constraints \[10%\]  
* Data availability: Only publicly accessible datasets (DrugBank, Medscape, SIDER) or institutional medical data can be used.  
* Privacy and security: Patient data must comply with confidentiality and data protection regulations.  
* Multi-user compatibility: System must serve both doctors and general users with different explanation levels.  
* Scalability: Must handle multiple drug combinations efficiently.  
* Accuracy: Predictions should be medically reliable and interpretable.  
* Usability: Interface must allow both chat-based queries and direct drug name input  
    
2.  Main Design 								        \[20%\]

   Data Integration:

* Collect drug information, protein targets, and known side effects from DrugBank, Medscape, and institutional medical records.  
* Generate a dataset linking drugs, interactions, and patient history.

  Prediction and Explanation Module:

* AI model evaluates potential interactions between two or more drugs and outputs risk levels.  
* LLM Integration: Use Claude Sonnet 4 API combined with libraries like LangChain to create a custom agent that interprets model predictions and generates human-readable explanations.  
  * Doctors: Detailed clinical mechanisms.  
  * General Users: Simplified language.

  System Architecture & Deployment:

* Backend: Python \+ TypeScript/JavaScript, deployed via AWS Lambda (serverless) with AWS CDK for stable deployment and smooth integration with databases and functions.  
* Database: AWS DynamoDB (NoSQL) for storing drug data, patient info, and prediction logs.  
* Frontend: Built with React, which can be deployed on AWS Amplify, S3 \+ CloudFront, or Vercel for scalability and global access.  
* Integration: Backend endpoints connect to the LLM agent, DynamoDB, and frontend to provide real-time predictions and explanations.

  User Interfaces:

* Chat interface: Interactive queries for detailed information.  
* Quick check interface: Enter multiple drug names for immediate interaction alerts.  
* Personalization**:** Uses patient history to generate tailored recommendations.

3. Discussion \[10%\]

* Data Availability & Accuracy: By integrating DrugBank, Medscape, and institutional medical data, the system uses reliable, curated sources to ensure accurate drug interaction predictions.  
* Privacy & Security: Patient data is stored securely in AWS DynamoDB with controlled access, and backend endpoints are serverless (AWS Lambda), minimizing exposure to security risks.  
* Multi-User Compatibility: The system provides two explanation levels — detailed for doctors and simplified for general users — satisfying the requirement for different audiences.  
* Scalability: Serverless deployment with AWS Lambda and CDK automation ensures that the system can handle multiple users and requests simultaneously without downtime.  
* Usability: Interactive chat interface and quick check module meet the constraint of user-friendly design, allowing both in-depth queries and fast drug combination checks.  
* Integration & Personalization: The architecture supports patient history integration to generate personalized recommendations, meeting the goal of tailored clinical support.  
* Technical Feasibility: Using Claude Sonnet 4 API with LangChain, React frontend, and Python/TypeScript backend ensures the system is implementable, maintainable, and scalable while satisfying all design constraints.

**4\. Reflection**									        \[30%\]

4A. Code of Conduct & Ethics (5%)

* All patient data used in the project is anonymized and handled securely, in compliance with privacy regulations.  
* The project follows ethical guidelines in AI usage: transparency, fairness, and avoiding harm to users.  
* Predictions and recommendations are presented as informational support only, not as direct medical prescriptions.

4B. Industrial Standards (10%)

* Followed best practices for software engineering and AI development, including modular code, version control, and code reviews.  
* Used AWS CDK for reproducible, stable deployments and serverless architecture for scalable, maintainable infrastructure.  
* Adhered to data handling standards and ensured reliability through curated data sources like DrugBank and Medscape.  
* Implemented testing and validation protocols for both AI predictions and system functionality.

4C. Impact on Society (10%)

* Helps reduce medication errors and improves patient safety by providing quick, accurate drug interaction insights.  
* Bridges the gap between expert medical knowledge and public accessibility, benefiting both doctors and patients.  
* Supports informed decision-making in clinical settings and empowers patients to understand potential drug risks.  
* Contributes to digital health innovation by combining AI, knowledge bases, and natural language explanations.

4D. Lifelong Learning (5%)

* Continuously monitor advances in AI, healthcare, and pharmacology to improve system performance and accuracy.  
* Regularly update knowledge through research papers, medical databases, and online courses.  
* Actively experiment with new AI models, tools, and deployment methods to stay current with industry standards.

# **Progress report (D2)**

# **1\. Specific Features of Our MVP (Updated According to Current Progress)**

### The current MVP focuses on demonstrating the core functionality and technical foundation of the system. While the final medical features and real drug datasets are not yet integrated, the main components of the architecture already work in a prototype environment.

### **1.1. User Interface & Design**

* ### Complete UI/UX design for the chatbot interface, drug interaction query page, and login/register pages.

* ### Fully responsive layout intended for both doctors and regular users.

* ### Visual design of the chat window, input components, and interaction sections completed.

### **1.2. Authentication System (Frontend \+ Logic)**

* ### Login and registration screens implemented on the frontend.

* ### JWT-based authentication logic prepared (token storage).

### **1.3. Working LLM Chatbot Prototype**

* ### A functional chatbot capable of generating responses using a local or hosted LLM.

* ### The chatbot currently provides general and structured answers.

* ### Conversation flow, message formatting, and UI rendering are fully operational.   The chatbot can be extended to incorporate medical knowledge once real data is integrated.

### **1.4. RAG Pipeline Prototype**

* ### End-to-end RAG architecture fully implemented in prototype form using:

  * ### PDF loader

  * ### Text chunking     Embedding generation

  * ### Vector storage via ChromaDB

  * ### Top-k retrieval 

* ### For testing purposes, non-medical sample documents are used instead of real drug reports.

* ### The pipeline currently works as a proof of concept to validate:

  * ### Embedding quality

  * ### Retrieval accuracy

  * ### End-to-end LLM \+ RAG integration

* ### Medical datasets will be integrated in the next milestone.

### **1.5. Prepared Agent/Tool Architecture (Not Yet Connected)**

* ### Initial design of agent-based workflow completed.

* ### Tool-calling formats defined but not integrated with backend services yet.

* ### Existing RAG and chatbot modules are structured to be extended into agentic architecture.

# **2\. Detailed Technical Design**

# The system is designed as a modular AI-powered platform consisting of a frontend interface, a backend service layer, and an LLM-based RAG architecture. Although some components are still under integration, the technical foundation and prototype pipeline are fully functional.

## **2.1. System Architecture Overview**

## **The architecture includes:**

### **Frontend (Completed UI Design)**

* ## Built using a modern framework (React/Next.js).

* ## Functional chatbot interface, login/register pages, and drug-interaction input screen.

* ## Currently connected to mock APIs until backend integration is completed.

### **Backend (Partially Implemented)**

* ## **Planned modules include:**

  * ## Authentication (JWT)

  * ## Chat/LLM endpoint

  * ## Future agent/tool endpoints 

* ## **Full integration will be added in the next development stage.**

## 

## 

## 

## **2.2. RAG Pipeline Design (Fully Working With Test Data)**

## The RAG prototype is fully operational and validated using sample PDFs (not medical datasets yet).

1. ## **Document Processing:** Test PDFs are loaded and cleaned.

2. ## **Chunking:** Text is split into 500–1000 token chunks with overlap.

3. ## **Embeddings:** Generated using transformer-based embedding models.

4. ## **Vector Store:** Stored in ChromaDB for persistent retrieval.

5. ## **Retrieval:** Top-k similarity search returns relevant chunks.

6. ## **LLM Integration:** Retrieved context is injected into the LLM prompt to produce informed answers.

## This pipeline confirms architectural correctness and will later be supplied with real medical data.

## **2.3. LLM Integration Layer**

* ## Local LLM models are used to generate responses.

* ## Prompting includes a system prompt \+ user input \+ RAG context.

* ## The model support multi-turn conversations

* ## Prepared for future function calling and agent workflows.

## **2.4. Authentication & Role Logic**

* ## Frontend logic for JWT handling is implemented (login/register UI, token storage).

* ## Backend-side enforcement will be completed after integration.

## **2.5. Agent & Tool Framework (Designed, Not Implemented)**

## **Planned tools:**

* ## Drug lookup

* ## Interaction severity analysis

* ## Patient history evaluation

## The agent will coordinate these tools to produce multi-step reasoning once real data and backend integration are added.

## **2.6. Data Usage**

* ## Current: Only sample test documents used for RAG validation.

* ## Future: DrugBank, Medscape, SIDER, institutional medical datasets.

## The system is technically ready to integrate real drug information in the next phase.

## 

**Client Approval**

