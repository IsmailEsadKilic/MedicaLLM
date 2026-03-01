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

Client Information:  
Name: Prof. Dr. Uğur Sezerman  
Position: Professor at Faculty of Medicine at Acıbadem University  
Date:   
Signature:

[image1]: <data:image/png;base64,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>