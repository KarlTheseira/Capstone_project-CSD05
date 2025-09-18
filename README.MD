# Film Company Store (Local-first, Azure-ready)

- Local: Flask + SQLite + filesystem
- Payments: Stripe test mode
- Azure-ready: flip STORAGE_BACKEND to "azure" and set connection + container

## Quickstart
1. Create .env from .env.example
2. pip install -r requirements.txt
3. python app.py init-db
4. flask --app app.py --debug run

## Stripe test
- Card: 4242 4242 4242 4242
- Any future expiry, any CVC, any ZIP

## Azure migration (high level)
- STORAGE_BACKEND=azure
- Set AZURE_* vars and create container
- Change SQLALCHEMY_DATABASE_URI to your Azure SQL connection string
- Deploy to Azure App Service
