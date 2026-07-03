"""Cria a organizacao e o usuario administrador iniciais (bootstrap).

Uso: python scripts/seed_admin.py "Consominas" admin@consominas.com "senha-forte"
"""

import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import Role, User


def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__)
        raise SystemExit(1)

    org_name, email, password = sys.argv[1], sys.argv[2], sys.argv[3]

    with SessionLocal() as db:
        org = Organization(name=org_name)
        db.add(org)
        db.flush()

        admin = User(
            organization_id=org.id,
            name="Administrador",
            email=email,
            hashed_password=hash_password(password),
            role=Role.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Organizacao '{org.name}' e admin '{admin.email}' criados.")


if __name__ == "__main__":
    main()
