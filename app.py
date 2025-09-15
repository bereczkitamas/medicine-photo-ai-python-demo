import os
import uvicorn
from app import create_app

# Expose `app` for ASGI servers
app = create_app()

if __name__ == '__main__':
    uvicorn.run("app:app", host='0.0.0.0', port=int(os.environ.get('PORT', '8000')), reload=True)
