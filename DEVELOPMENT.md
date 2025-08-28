# IAM App Development Guide

## Quick Start

### Option 1: Start Both Servers (Recommended)
```bash
./start-dev.sh
```
This will start both the backend (Flask) and frontend (React) servers simultaneously.

### Option 2: Start Servers Individually
```bash
# Terminal 1 - Backend
./start-backend.sh

# Terminal 2 - Frontend  
./start-frontend.sh
```

## Development URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5001

## Environment Setup

### 1. Copy Environment Files
```bash
# Root level
cp .env.example .env

# Backend
cp iam-backend/.env.example iam-backend/.env

# Frontend
cp iam-frontend/.env.example iam-frontend/.env
```

### 2. Configure API Keys
Edit the `.env` files and add your actual API keys:
- OpenAI API key for transcription
- Stripe keys for payment processing

## Project Structure

```
iam-app/
├── iam-backend/           # Flask Python backend
│   ├── src/
│   │   ├── main.py       # Flask app entry point
│   │   ├── models/       # Database models
│   │   └── routes/       # API endpoints
│   ├── venv/             # Python virtual environment
│   └── requirements.txt  # Python dependencies
├── iam-frontend/         # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   └── App.jsx       # Main app component
│   └── package.json      # Node.js dependencies
├── start-dev.sh          # Start both servers
├── start-backend.sh      # Start backend only
└── start-frontend.sh     # Start frontend only
```

## Development Workflow

### Backend Development
1. Activate virtual environment: `source iam-backend/venv/bin/activate`
2. Install new dependencies: `pip install package_name`
3. Update requirements: `pip freeze > requirements.txt`
4. Run backend: `python iam-backend/src/main.py`

### Frontend Development
1. Navigate to frontend: `cd iam-frontend`
2. Install new dependencies: `pnpm add package_name`
3. Run development server: `pnpm dev`
4. Build for production: `pnpm build`

## Testing

### Backend Testing
```bash
cd iam-backend
source venv/bin/activate
python -m pytest tests/
```

### Frontend Testing
```bash
cd iam-frontend
pnpm test
```

## Building for Production

### 1. Build Frontend
```bash
cd iam-frontend
pnpm build
```

### 2. Copy to Backend Static Directory
```bash
cp -r iam-frontend/dist/* iam-backend/src/static/
```

### 3. Deploy Backend
The Flask backend serves both API and static files.

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Backend (5001): `lsof -ti:5001 | xargs kill -9`
   - Frontend (5173): `lsof -ti:5173 | xargs kill -9`

2. **Python virtual environment issues**
   ```bash
   cd iam-backend
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Node modules issues**
   ```bash
   cd iam-frontend
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

4. **CORS issues**
   - Check that FRONTEND_URL in backend .env matches frontend URL
   - Ensure Flask-CORS is properly configured

## API Endpoints

### Meeting Management
- `POST /api/transcribe` - Upload and transcribe audio
- `GET /api/meetings` - Get all meetings
- `GET /api/meetings/<id>` - Get specific meeting
- `DELETE /api/meetings/<id>` - Delete meeting

### Payment Processing
- `POST /api/create-payment-intent` - Create Stripe payment
- `POST /api/confirm-payment` - Confirm payment
- `GET /api/subscription-plans` - Get available plans

## Database

The app uses SQLite by default. Database file: `iam-backend/iam_app.db`

To reset the database:
```bash
rm iam-backend/iam_app.db
# Restart the backend to recreate tables
```
