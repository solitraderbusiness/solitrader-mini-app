"""
TG-Trade Suite FastAPI Application
"""
import os
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to Python path
sys.path.append('/app')

app = FastAPI(
    title="TG-Trade Suite API", 
    version="1.0.0",
    description="AI-powered chart analysis for Telegram"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "TG-Trade Suite API is running",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "api",
        "environment": os.getenv("DEBUG", "False")
    }

@app.get("/test-db-real")
async def test_database_connection():
    """Test real database connection"""
    try:
        # Import asyncpg inside the function to avoid startup crashes
        import asyncpg
        
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            return {"status": "error", "message": "No DATABASE_URL found"}
        
        # Test connection
        conn = await asyncpg.connect(database_url)
        
        # Test query
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM users")
        await conn.close()
        
        return {
            "status": "success", 
            "message": "Database connected successfully",
            "users_count": result['count'] if result else 0
        }
    except ImportError:
        return {
            "status": "error", 
            "message": "asyncpg not installed"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database connection failed: {str(e)}"
        }

@app.get("/test-env")
async def test_environment():
    """Test environment variables"""
    return {
        "database_url_exists": bool(os.getenv('DATABASE_URL')),
        "database_url_preview": os.getenv('DATABASE_URL', '')[:30] + "..." if os.getenv('DATABASE_URL') else "None",
        "debug": os.getenv('DEBUG', 'False'),
        "redis_url": os.getenv('REDIS_URL', 'Not set')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
