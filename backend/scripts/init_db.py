"""
Database initialization script - creates all tables and seeds initial admin user
Run: python scripts/init_db.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, Base
from app.core.security import get_password_hash, generate_verification_token
from app.db.models import User, UserRole  # imports register all models
import sqlalchemy


async def init_db():
    print("🔧 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")

    # Seed admin user
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "admin@llmops.dev")
        )
        if result.scalar_one_or_none():
            print("ℹ️  Admin user already exists")
            return

        admin = User(
            email="admin@llmops.dev",
            username="admin",
            full_name="Platform Admin",
            hashed_password=get_password_hash("Admin@1234"),
            role=UserRole.SUPERADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        print("✅ Admin user created: admin@llmops.dev / Admin@1234")

    await engine.dispose()
    print("🚀 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
