#!/usr/bin/env python3
# ruff: noqa
# mypy: ignore-errors
"""Script to generate service JWT tokens for service-to-service authentication.

Usage:
    python scripts/generate_service_token.py <service_name> [--days DAYS]

Example:
    python scripts/generate_service_token.py classification-service --days 365
"""

import argparse
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).parent.parent))

from jose import jwt

from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.models import UserRole


ALGORITHM = "RS256"


def generate_service_token(service_name: str, days: int = 365) -> str:
    """Generate a JWT service token."""
    exp: datetime = datetime.now(UTC) + timedelta(days=days)
    payload: dict[str, Any] = {
        "sub": service_name,
        "roles": UserRole.SERVICE.value,
        "exp": exp,
        "iat": datetime.now(UTC),
    }

    token: str = jwt.encode(
        payload,
        settings.auth.PRIVATE_KEY.get_secret_value(),
        algorithm=ALGORITHM,
    )

    return token


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate service JWT token for service-to-service authentication"
    )
    parser.add_argument(
        "service_name",
        help="Name of the service (e.g., classification-service)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Token validity in days (default: 365)",
    )

    args = parser.parse_args()

    token = generate_service_token(args.service_name, args.days)

    print(f"\n{'=' * 80}")
    print("Service Token Generated Successfully")
    print(f"{'=' * 80}")
    print(f"\nService Name: {args.service_name}")
    print(f"Role: {UserRole.SERVICE.value}")
    print(f"Valid for: {args.days} days")
    print(f"\nToken:\n{token}")
    print(f"\n{'=' * 80}")
    print("\nUsage in HTTP requests:")
    print(f"  Authorization: Bearer {token}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
