# Frontend API Updates - Backend Router Overhaul

This document summarizes all the changes made to the frontend to match the new backend router structure.

## Summary of Changes

### 1. **Chat.jsx** - Conversation & Query Management
- **Conversations endpoint**: Changed from `c.id` to `c.conversation_id` when mapping conversations
- **Patient list endpoint**: Changed from `/api/patients/` to `/api/users/doctors/patients`
- **Patient selection**: Changed from `selectedPatient.id` to `selectedPatient.patient_id`
- **Generate title endpoint**: Changed request body from `{ message: input }` to `{ conversation_id: chatId }`
- **Query endpoint**: Removed `account_type` parameter (backend now infers from token)

### 2. **Patients.jsx** - Patient Management
- **Load patients endpoint**: Changed from `/api/patients` to `/api/users/doctors/patients`
- **Create patient endpoint**: Changed from `/api/patients` (POST) to `/api/users/profile/patient` (POST)
- **Patient data structure**: Updated to match new backend schema:
  - Uses `date_of_birth` instead of `age`
  - Converts arrays to comma-separated strings for `chronic_conditions`, `allergies`, `current_medications`
- **AI Analysis**: Disabled (endpoint `/api/drugs/analyze-patient` not implemented in new backend)
- **Edit patient**: Disabled (no update endpoint in new backend yet)

### 3. **DrugSearch.jsx** - Drug Information & Interactions
- **Search endpoint**: Added `encodeURIComponent` for query parameter and `?include_semantic_search=false` query param
- **Interaction check**: Changed from drug names to drug IDs: `/api/drug-search/interaction/${drug_id}/${drug_id}`
- **Get drug details**: Added `encodeURIComponent` for drug name parameter
- **Alternatives feature**: Commented out (endpoint not implemented in new backend)

### 4. **Auth.jsx** - Simple Authentication
- **Register endpoint**: Changed from `/api/auth/register` to `/api/auth/send-code`
- **Registration flow**: Now shows alert about verification code instead of direct login

### 5. **Register.jsx** - Registration with Verification
- **Verify code endpoint**: Changed from `/api/auth/verify-code` to `/api/auth/verification-code`

### 6. **Admin.jsx** - No changes needed
- Admin endpoints remain the same

### 7. **Login.jsx** - No changes needed
- Login and password reset endpoints remain the same

## Backend Endpoints Used

### Authentication (`/api/auth`)
- `POST /api/auth/login` - User login
- `POST /api/auth/send-code` - Send verification code for registration
- `POST /api/auth/verification-code` - Verify code and create account
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with code

### Users (`/api/users`)
- `POST /api/users/profile/patient` - Create patient profile
- `GET /api/users/doctors/patients` - Get patients for authenticated doctor
- `GET /api/users/patients/doctors` - Get doctors for authenticated patient
- `GET /api/users/profile/patient/{patient_id}` - Get patient details

### Conversations (`/api/conversations`)
- `GET /api/conversations/` - Get all conversations for user
- `POST /api/conversations/` - Create new conversation
- `GET /api/conversations/{conversation_id}` - Get specific conversation
- `PATCH /api/conversations/{conversation_id}/title` - Update conversation title
- `DELETE /api/conversations/{conversation_id}` - Delete conversation

### Drugs (`/api/drugs` - session router)
- `POST /api/drugs/query` - Send query to AI agent
- `POST /api/drugs/generate-title` - Generate conversation title

### Drug Search (`/api/drug-search`)
- `GET /api/drug-search/search/{query}` - Search for drugs
- `GET /api/drug-search/{drug_id}` - Get drug details by ID
- `GET /api/drug-search/interaction/{drug1_id}/{drug2_id}` - Check drug interactions

### Admin (`/api/admin`)
- `POST /api/admin/login` - Admin login
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/users` - Get all users

## Features Temporarily Disabled

These features are commented out in the frontend because the backend endpoints don't exist yet:

1. **Drug Alternatives** (DrugSearch.jsx)
   - Endpoint: `/api/drug-search/alternatives/{drug_name}`
   - Feature: Suggest alternative drugs when interactions are found

2. **Patient AI Analysis** (Patients.jsx)
   - Endpoint: `/api/drugs/analyze-patient`
   - Feature: AI-powered analysis of patient medication profile

3. **Edit Patient** (Patients.jsx)
   - Endpoint: `PUT /api/users/profile/patient/{patient_id}`
   - Feature: Update existing patient information

## Key Data Structure Changes

### Patient Object
**Old Structure:**
```javascript
{
  id: number,
  name: string,
  surname: string,
  age: number,
  chronicConditions: string[],
  allergies: string[],
  currentMedications: Array<{name, dosage, frequency}>
}
```

**New Structure:**
```javascript
{
  patient_id: string,
  user_id: string,
  name: string,
  date_of_birth: string (ISO date),
  gender: string,
  chronic_conditions: string (comma-separated),
  allergies: string (comma-separated),
  current_medications: string (comma-separated),
  notes: string
}
```

### Conversation Object
**Old:** `id` field
**New:** `conversation_id` field

### Drug Interaction Check
**Old:** Uses drug names
**New:** Uses drug IDs

## Testing Recommendations

1. **Authentication Flow**
   - Test registration with email verification
   - Test login
   - Test password reset

2. **Chat Functionality**
   - Test creating new conversations
   - Test sending messages
   - Test title generation
   - Test patient context selection (for doctors)

3. **Patient Management** (for doctors)
   - Test loading patient list
   - Test creating new patient profile
   - Verify edit and AI analysis show appropriate messages

4. **Drug Search**
   - Test drug search functionality
   - Test drug interaction checking
   - Verify alternatives section is hidden

5. **Admin Panel**
   - Test admin login
   - Test viewing statistics
   - Test viewing user list

## Migration Notes

- All API calls now properly use `encodeURIComponent` for URL parameters
- Authentication token is consistently passed in `Authorization: Bearer {token}` header
- Error handling remains consistent across all endpoints
- The frontend gracefully handles missing backend features with user-friendly messages
