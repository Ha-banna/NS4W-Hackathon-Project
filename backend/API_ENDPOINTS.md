# API Endpoints Documentation

Base URL: `http://localhost:8000/api`

All endpoints require authentication via SuperTokens (except where noted).

## CV Management

### Get All CVs
- **GET** `/api/cvs`
- **Query Parameters:**
  - `search` (optional): Search by name, email, position, or skills
  - `position` (optional): Filter by position
  - `skip` (optional, default: 0): Pagination offset
  - `limit` (optional, default: 100): Number of results
- **Response:** List of CV objects
```json
[
  {
    "id": "string",
    "key": "string",
    "name": "string",
    "email": "string",
    "position": "string",
    "score": 85,
    "uploadedDate": "2024-01-15",
    "skills": ["React", "TypeScript"],
    "file_url": "/uploads/file.pdf"
  }
]
```

### Get CV Details
- **GET** `/api/cvs/{cv_id}`
- **Response:** Detailed CV with evaluation results
```json
{
  "id": "string",
  "name": "string",
  "email": "string",
  "position": "string",
  "uploadedDate": "2024-01-15",
  "overallScore": 85,
  "categories": [
    {
      "name": "Technical Skills",
      "items": [
        {
          "id": "string",
          "name": "React",
          "value": "Expert level",
          "authenticityScore": 92
        }
      ]
    }
  ],
  "file_url": "/uploads/file.pdf"
}
```

### Upload CV
- **POST** `/api/cvs`
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `position` (required): Position name
  - `file` (required): PDF file (max 50MB)
- **Response:** Created CV object

### Delete CV
- **DELETE** `/api/cvs/{cv_id}`
- **Response:** 204 No Content

## Company Management (Admin)

### Get All Companies
- **GET** `/api/companies`
- **Response:** List of companies with employee counts
```json
[
  {
    "id": "string",
    "name": "TechCorp Inc.",
    "email": "contact@techcorp.com",
    "employeeCount": 5
  }
]
```

### Get Company Employees
- **GET** `/api/companies/{company_id}/employees`
- **Query Parameters:**
  - `search` (optional): Search by name or email
- **Response:** List of employees
```json
[
  {
    "id": "string",
    "name": "John Doe",
    "email": "john@example.com",
    "companyId": "string"
  }
]
```

### Create Employee
- **POST** `/api/companies/{company_id}/employees`
- **Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```
- **Response:** Created employee object

### Delete Employee
- **DELETE** `/api/companies/employees/{employee_id}`
- **Response:** 204 No Content

## Request to Join

### Submit Request
- **POST** `/api/requests`
- **No authentication required**
- **Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "TechCorp Inc.",
  "message": "We would like to join the platform..."
}
```
- **Response:** Created request object

### Get All Requests (Admin)
- **GET** `/api/requests`
- **Query Parameters:**
  - `skip` (optional, default: 0)
  - `limit` (optional, default: 100)
- **Response:** List of requests

## Health Check

### Health Check
- **GET** `/health`
- **No authentication required**
- **Response:**
```json
{
  "status": "healthy"
}
```

## Error Responses

All endpoints may return the following error responses:

- **400 Bad Request:** Invalid input data
- **401 Unauthorized:** Not authenticated
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server error

Example error response:
```json
{
  "detail": "Error message"
}
```
