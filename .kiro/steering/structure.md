# Project Structure

## Root Organization
```
iam-app/
├── iam-frontend/          # React frontend application
├── iam-backend/           # Flask backend application
└── README.md              # Project documentation
```

## Frontend Structure (`iam-frontend/`)
```
iam-frontend/
├── src/
│   ├── components/        # React components
│   │   ├── AudioRecorder.jsx
│   │   ├── MeetingsList.jsx
│   │   ├── PaymentModal.jsx
│   │   └── ui/           # shadcn/ui components library
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utility functions
│   ├── assets/           # Static assets
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Application entry point
│   └── index.css         # Global styles
├── public/               # Public static files
├── package.json          # Dependencies and scripts
└── vite.config.js        # Vite configuration
```

## Backend Structure (`iam-backend/`)
```
iam-backend/
├── src/
│   ├── models/           # SQLAlchemy database models
│   │   ├── user.py
│   │   └── meeting.py
│   ├── routes/           # Flask API route blueprints
│   │   ├── user.py
│   │   ├── meeting.py
│   │   └── payment.py
│   ├── database/         # SQLite database files
│   ├── static/           # Built frontend files (production)
│   └── main.py           # Flask application entry point
└── requirements.txt      # Python dependencies
```

## Architecture Patterns

### Backend Patterns
- **Blueprint Organization**: Routes organized by feature (user, meeting, payment)
- **Model Pattern**: SQLAlchemy models with `to_dict()` serialization methods
- **Database**: Single SQLite file in `src/database/app.db`
- **Static Serving**: Flask serves built frontend from `src/static/`

### Frontend Patterns
- **Component Structure**: Feature-based components with shadcn/ui library
- **State Management**: React useState for local state
- **API Communication**: Fetch API with Vite proxy to backend
- **Local Storage**: IndexedDB for audio files, localStorage for user preferences

### File Naming Conventions
- **Frontend**: PascalCase for components (`AudioRecorder.jsx`)
- **Backend**: snake_case for Python files (`meeting.py`)
- **Database Models**: PascalCase classes with snake_case table names