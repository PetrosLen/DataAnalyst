"""Create or update an admin panel user.

Usage:
    python -m app.scripts.create_admin_user founder@example.com --role owner
"""

import argparse
import getpass

from app.core.security import hash_password
from app.db.models import AdminUser
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an admin panel user")
    parser.add_argument("email")
    parser.add_argument("--role", default="owner", choices=["owner", "editor", "viewer"])
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords don't match.")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter_by(email=args.email).first()
        if user:
            user.password_hash = hash_password(password)
            user.role = args.role
            print(f"Updated existing admin user: {args.email} ({args.role})")
        else:
            user = AdminUser(email=args.email, role=args.role, password_hash=hash_password(password))
            db.add(user)
            print(f"Created admin user: {args.email} ({args.role})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
