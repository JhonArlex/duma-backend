#!/usr/bin/env python3
"""Seed script to populate stores table with initial store data."""

import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.store import Store
from sqlalchemy.exc import IntegrityError


def seed_stores():
    """Seed the database with initial store data."""
    app = create_app()
    
    with app.app_context():
        stores_data = [
            {
                'name': 'Amazon',
                'slug': 'amazon',
                'base_url': 'https://www.amazon.com',
                'logo_url': 'https://logo.clearbit.com/amazon.com',
                'is_active': True,
                'display_order': 1,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'eBay',
                'slug': 'ebay',
                'base_url': 'https://www.ebay.com',
                'logo_url': 'https://logo.clearbit.com/ebay.com',
                'is_active': True,
                'display_order': 2,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'Walmart',
                'slug': 'walmart',
                'base_url': 'https://www.walmart.com',
                'logo_url': 'https://logo.clearbit.com/walmart.com',
                'is_active': True,
                'display_order': 3,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'Target',
                'slug': 'target',
                'base_url': 'https://www.target.com',
                'logo_url': 'https://logo.clearbit.com/target.com',
                'is_active': True,
                'display_order': 4,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'Best Buy',
                'slug': 'bestbuy',
                'base_url': 'https://www.bestbuy.com',
                'logo_url': 'https://logo.clearbit.com/bestbuy.com',
                'is_active': True,
                'display_order': 5,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'Shein',
                'slug': 'shein',
                'base_url': 'https://www.shein.com',
                'logo_url': 'https://logo.clearbit.com/shein.com',
                'is_active': True,
                'display_order': 6,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US']
                }
            },
            {
                'name': 'AliExpress',
                'slug': 'aliexpress',
                'base_url': 'https://www.aliexpress.com',
                'logo_url': 'https://logo.clearbit.com/aliexpress.com',
                'is_active': True,
                'display_order': 7,
                'config': {
                    'scraping_enabled': True,
                    'supported_countries': ['US', 'CN']
                }
            },
            {
                'name': 'Otra Tienda',
                'slug': 'other',
                'base_url': 'https://www.google.com',
                'logo_url': None,
                'is_active': True,
                'display_order': 99,
                'config': {
                    'scraping_enabled': False,
                    'supported_countries': ['US']
                }
            }
        ]

        created_count = 0
        skipped_count = 0

        for store_data in stores_data:
            # Check if store already exists
            existing_store = Store.query.filter_by(slug=store_data['slug']).first()
            
            if existing_store:
                print(f"⏭️  Skipping '{store_data['name']}' - already exists")
                skipped_count += 1
                continue

            try:
                store = Store(**store_data)
                db.session.add(store)
                db.session.commit()
                print(f"✅ Created store: {store_data['name']} (slug: {store_data['slug']})")
                created_count += 1
            except IntegrityError as e:
                db.session.rollback()
                print(f"❌ Error creating store '{store_data['name']}': {str(e)}")
                continue

        print(f"\n📊 Summary:")
        print(f"   Created: {created_count} stores")
        print(f"   Skipped: {skipped_count} stores")
        print(f"   Total: {created_count + skipped_count} stores processed")


if __name__ == '__main__':
    print("🌱 Seeding stores...\n")
    seed_stores()
    print("\n✨ Done!")
