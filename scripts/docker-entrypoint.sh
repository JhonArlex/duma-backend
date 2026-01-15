#!/bin/bash
set -e

echo "=== Duma Express Backend Startup ==="

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "
import os
import psycopg2
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
conn.close()
" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

# Only run migrations and seed for the main API service (gunicorn)
if [[ "$1" == "gunicorn" ]]; then
    # Run migrations
    echo "Running database migrations..."
    flask db upgrade

    # Create superadmin if not exists
    echo "Checking/creating superadmin user..."
    python -c "
from app import create_app, db
from app.models.user import User
from app.models.role import Role

app = create_app()
with app.app_context():
    # Check if superadmin exists
    superadmin_role = Role.get_superadmin_role()
    if superadmin_role:
        existing = User.query.filter_by(email_hash=User.hash_email('admin@duma.com')).first()
        if not existing:
            user = User(
                display_name='Admin Duma',
                role_id=superadmin_role.id
            )
            user.set_email('admin@duma.com')
            user.set_password('Bp8ld0zS2Q2yrDQq')
            db.session.add(user)
            db.session.commit()
            print('Superadmin created: admin@duma.com')
        else:
            print('Superadmin already exists: admin@duma.com')
    else:
        print('Warning: Superadmin role not found. Run migrations first.')
"
fi

echo "=== Starting application ==="

# Execute the main command
exec "$@"
