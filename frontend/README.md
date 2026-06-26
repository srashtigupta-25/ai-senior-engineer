# AI Senior Engineer Frontend

This is the Next.js frontend for AI Senior Engineer. It lets users index a GitHub repository, ask codebase questions, generate an architecture report, and generate an onboarding guide.

## Run Locally

Start the backend first:

```bash
cd ../backend
uvicorn app.main:app --reload --port 8000
```

Then start the frontend:

```bash
npm install
npm run dev -- --port 3001
```

Open:

```text
http://localhost:3001
```

## API Configuration

The frontend calls `http://127.0.0.1:8000` by default. Override it with:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --port 3001
```

## Scripts

```bash
npm run dev
npm run lint
npm run build
npm run start
```

## Main Files

- `app/page.tsx`: Main product UI and tab logic.
- `app/layout.tsx`: App metadata and font setup.
- `app/globals.css`: Global Tailwind and body styles.
- `lib/api.ts`: Axios client for the FastAPI backend.
