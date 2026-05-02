# TODO: Backend Endpoints to Implement

These endpoints are referenced in the frontend but not yet implemented in the backend routers.

## High Priority

### 1. Update Patient Profile
**Endpoint:** `PUT /api/users/profile/patient/{patient_id}`
**Router:** `backend/src/users/router.py`
**Purpose:** Allow doctors to update existing patient information
**Request Body:**
```python
{
    "date_of_birth": str (optional),
    "gender": str (optional),
    "chronic_conditions": str (optional),
    "allergies": str (optional),
    "current_medications": str (optional),
    "notes": str (optional)
}
```

### 2. Drug Alternatives
**Endpoint:** `GET /api/drug-search/alternatives/{drug_name}`
**Router:** `backend/src/drugs/router.py`
**Purpose:** Suggest alternative drugs when interactions are found
**Query Parameters:**
- `patient_medications`: comma-separated list of other medications
**Response:**
```python
{
    "count": int,
    "alternatives": [
        {
            "name": str,
            "drug_id": str,
            "categories": List[str],
            "indication": str,
            "groups": List[str]
        }
    ],
    "message": str (optional)
}
```

### 3. Patient AI Analysis
**Endpoint:** `POST /api/drugs/analyze-patient`
**Router:** `backend/src/drugs/router.py` or `backend/src/session/router.py`
**Purpose:** AI-powered analysis of patient medication profile
**Request Body:**
```python
{
    "chronic_conditions": List[str],
    "allergies": List[str],
    "current_medications": List[str]
}
```
**Response:**
```python
{
    "analysis": str (markdown formatted)
}
```

## Medium Priority

### 4. Streaming Query Endpoint
**Endpoint:** `POST /api/drugs/query-stream`
**Router:** `backend/src/session/router.py`
**Purpose:** Server-sent events streaming for real-time responses
**Status:** Marked as "not implemented yet" in backend
**Note:** Frontend already has SSE parsing logic, but backend returns 501

### 5. RAG Endpoints
**Router:** `backend/src/rag/router.py`
**Status:** Empty file
**Purpose:** PDF upload and vector search functionality
**Suggested Endpoints:**
- `POST /api/rag/upload` - Upload PDF documents
- `GET /api/rag/search` - Search uploaded documents
- `DELETE /api/rag/document/{doc_id}` - Delete document

## Low Priority

### 6. Get Patient Details by ID (for non-doctors)
**Current:** `GET /api/users/profile/patient/{patient_id}` requires authorization
**Enhancement:** Allow patients to view their own profile
**Note:** Currently only accessible by patient themselves or their assigned doctors

### 7. Assign/Remove Doctor-Patient Relationships
**Endpoints:**
- `POST /api/users/relationships/assign`
- `DELETE /api/users/relationships/remove`
**Status:** Marked as "Admin only" but no admin check implemented
**Enhancement:** Add admin authorization check

## Data Model Considerations

### Patient Profile Creation
The current backend expects:
```python
class CreatePatientProfileRequest(BaseModel):
    date_of_birth: str
    gender: str
    chronic_conditions: str = ""
    allergies: str = ""
    current_medications: str = ""
    notes: str = ""
```

But the frontend collects more data:
- name, surname (from user record)
- identityNumber
- bloodType
- phone, email, address
- height, weight, BMI
- labFile (PDF)

**Recommendation:** Extend the patient profile model to include these fields or create a separate medical record model.

## API Consistency Issues

### 1. Drug ID vs Drug Name
- Interaction endpoint uses drug IDs: `/interaction/{drug1_id}/{drug2_id}`
- Get drug endpoint uses drug name: `/{drug_id}` (but actually expects name)
- **Recommendation:** Standardize on drug IDs for all endpoints

### 2. Response Format Consistency
Some endpoints return:
```python
{"success": True, "data": {...}}
```
Others return the data directly:
```python
{...}
```
**Recommendation:** Standardize response format across all endpoints

### 3. Error Handling
- Some endpoints raise HTTPException with detail
- Others return error in response body
- **Recommendation:** Consistent error response format

## Testing Checklist

Once endpoints are implemented, test:

- [ ] Create patient profile
- [ ] Update patient profile
- [ ] Get patient details (as doctor)
- [ ] Get patient details (as patient themselves)
- [ ] Get drug alternatives
- [ ] AI patient analysis
- [ ] Streaming query responses
- [ ] RAG document upload
- [ ] RAG document search
- [ ] Admin authorization for relationship management

## Notes

- The frontend is now fully compatible with the current backend API
- Disabled features show user-friendly messages
- All changes are documented in FRONTEND_API_UPDATES.md
- Frontend uses proper URL encoding for all parameters
- Authentication is consistent across all requests
