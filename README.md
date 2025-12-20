# BUSTED - AI-Powered CV Evaluation Platform

**BUSTED** is an intelligent CV evaluation platform that uses AI and LLM technology to analyze candidate resumes, verify skills, detect authenticity issues, and generate personalized interview questions.

## 🚀 Features

### Core Capabilities

- **📄 CV Upload & Processing**: Upload candidate CVs in PDF format for automated analysis
- **🔍 Skill Evidence Mapping**: Map every skill in the CV to evidence found on GitHub or LinkedIn
- **✅ Project Authenticity Score**: Detect copy-paste projects, tutorial clones, or AI-generated code
- **📊 Skill Inflation Detection**: LLM classifies claims as Beginner/Intermediate/Expert and compares claim wording vs actual usage
- **💡 Personalized Interview Questions**: Generated based on CV claims and weak points, including theoretical, practical, and debugging questions
- **📈 Candidate Comparison Dashboard**: View final evaluation scores with skill confidence, evidence count, red flags, and interview readiness scores

### Scoring System

The platform evaluates candidates based on:
- **Skill Authenticity (40%)**: Verification of claimed skills through GitHub/LinkedIn evidence
- **Timeline Consistency (20%)**: Validation of work history and education timelines
- **Code Quality (20%)**: Analysis of project code quality and complexity
- **Online Presence Match (20%)**: Correlation between CV claims and online profiles

## 🛠️ Tech Stack

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Typed superset of JavaScript
- **Vite** - Next generation frontend tooling
- **Ant Design Vue** - Enterprise-class UI component library
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API requests

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3** - Programming language
- **MongoDB** - NoSQL database (via PyMongo)
- **SuperTokens** - Authentication solution
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

### AI/LLM Stack
- **LLM Integration** - For CV analysis and skill verification
- **GitHub API** - For repository analysis
- **LinkedIn Integration** - For profile verification

## 📋 Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- **MongoDB** (local installation or MongoDB Atlas account)
- **SuperTokens** account (for authentication)
- **Git** (for version control)

## 🚀 Getting Started

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** in the `backend` directory:
   ```env
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=busted_db
   API_DOMAIN=http://127.0.0.1:8000
   API_BASE_PATH=/auth
   WEBSITE_DOMAIN=http://localhost:5173
   WEBSITE_BASE_PATH=/auth
   ```

5. **Run the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be available at `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create `.env` file** in the `frontend` directory:
   ```env
   VITE_BACKEND_URL=http://127.0.0.1:8000
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
hackathon/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── analysis.py      # Analysis endpoints
│   │   ├── auth/
│   │   │   └── supertokens.py       # Authentication setup
│   │   ├── core/
│   │   │   └── config.py            # Configuration settings
│   │   ├── db/
│   │   │   └── mongo.py             # MongoDB connection
│   │   ├── services/
│   │   │   └── analysis/            # Analysis pipeline
│   │   └── main.py                  # FastAPI application
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.ts             # API client configuration
│   │   ├── components/
│   │   │   ├── LandingPage.vue      # Landing page
│   │   │   ├── Dashboard.vue        # CV dashboard
│   │   │   ├── CreateCV.vue         # CV upload page
│   │   │   ├── CVResults.vue        # CV results page
│   │   │   └── ScoreCircle.vue      # Score display component
│   │   ├── router/
│   │   │   └── index.ts              # Route configuration
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── .env
│
└── README.md
```

## 🔌 API Endpoints

### Analysis Endpoints

- **POST `/analysis/upload-cv`**
  - Upload a CV file for analysis
  - **Request**: `multipart/form-data` with `file` field (PDF)
  - **Response**: `{ "cv_json_ready": boolean }`

- **GET `/cv-results`**
  - Get all CV analysis results
  - **Response**: Array of CV analysis objects with:
    - `_id`: CV ID
    - `cv`: Parsed CV data (candidate info, skills, experience, etc.)
    - `skill_evidence`: Skill verification results
    - `projects_authenticity`: Project authenticity scores
    - `skill_inflation`: Skill inflation detection
    - `interview_questions`: Generated interview questions

## 🎯 Usage

### Uploading a CV

1. Navigate to the Dashboard
2. Click "Add CV" button
3. Select a PDF file (max 50MB)
4. Click "Submit CV"
5. Wait for processing to complete

### Viewing Results

1. From the Dashboard, click "View" on any CV
2. Review the detailed analysis including:
   - Skill evidence with confidence scores
   - Project authenticity scores
   - Skill inflation detection
   - Overall authenticity score

## 🎨 UI Features

- **Dark Theme**: Modern dark theme with purple glassmorphism design
- **Animated Backgrounds**: Smooth animated gradient backgrounds
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Live updates during CV processing
- **Interactive Score Circles**: Visual representation of authenticity scores

## 🔒 Environment Variables

### Backend (.env)
- `MONGODB_URI`: MongoDB connection string
- `MONGODB_DB`: Database name
- `API_DOMAIN`: Backend API domain
- `API_BASE_PATH`: API base path for authentication
- `WEBSITE_DOMAIN`: Frontend domain
- `WEBSITE_BASE_PATH`: Frontend base path

### Frontend (.env)
- `VITE_BACKEND_URL`: Backend API URL (default: `http://127.0.0.1:8000`)

## 🧪 Development

### Running Tests

```bash
# Backend tests (if available)
cd backend
pytest

# Frontend tests (if available)
cd frontend
npm run test
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build

# Backend (no build step needed, just deploy)
```

## 📝 License

This project is part of the NS4W Hackathon.

## 🤝 Contributing

This is a hackathon project. Contributions and improvements are welcome!

## 📧 Contact

For questions or support, please refer to the project repository.

---

**Built with ❤️ for the NS4W Hackathon**
