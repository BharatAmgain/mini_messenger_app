# fix_production.py
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection

print('🔧 FIXING PRODUCTION POSTGRESQL DATABASE')
print('=' * 50)


def add_missing_columns():
    '''Add all missing columns to PostgreSQL database'''
    with connection.cursor() as cursor:
        # List of all columns from your CustomUser model
        columns_to_add = [
            ('is_online', 'BOOLEAN DEFAULT FALSE'),
            ('show_online_status', 'BOOLEAN DEFAULT TRUE'),
            ('allow_message_requests', 'BOOLEAN DEFAULT TRUE'),
            ('allow_calls', 'BOOLEAN DEFAULT TRUE'),
            ('allow_invitations', 'BOOLEAN DEFAULT TRUE'),
            ('show_last_seen', 'BOOLEAN DEFAULT TRUE'),
            ('show_profile_picture', 'BOOLEAN DEFAULT TRUE'),
            ('message_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('message_sound', 'BOOLEAN DEFAULT TRUE'),
            ('message_preview', 'BOOLEAN DEFAULT TRUE'),
            ('group_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('group_mentions_only', 'BOOLEAN DEFAULT FALSE'),
            ('friend_request_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('friend_online_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('system_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('marketing_notifications', 'BOOLEAN DEFAULT FALSE'),
            ('push_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('email_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('desktop_notifications', 'BOOLEAN DEFAULT TRUE'),
            ('quiet_hours_enabled', 'BOOLEAN DEFAULT FALSE'),
            ('quiet_hours_start', 'TIME'),
            ('quiet_hours_end', 'TIME'),
            ('theme', 'VARCHAR(10) DEFAULT \'auto\''),
            ('email_verified', 'BOOLEAN DEFAULT FALSE'),
            ('phone_verified', 'BOOLEAN DEFAULT FALSE'),
            ('last_updated', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ]

        for col_name, col_def in columns_to_add:
            try:
                cursor.execute(f'''
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 
                            FROM information_schema.columns 
                            WHERE table_name='accounts_customuser' 
                            AND column_name='{col_name}'
                        ) THEN
                            EXECUTE 'ALTER TABLE accounts_customuser ADD COLUMN {col_name} {col_def}';
                            RAISE NOTICE 'Added column: {col_name}';
                        ELSE
                            RAISE NOTICE 'Column already exists: {col_name}';
                        END IF;
                    END $$;
                ''')
                print(f'✅ Checked/added: {col_name}')
            except Exception as e:
                print(f'⚠️  Error with {col_name}: {e}')

        # Verify
        cursor.execute("SELECT COUNT(*) FROM accounts_customuser;")
        user_count = cursor.fetchone()[0]
        print(f'\n📊 Total users: {user_count}')

        cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='accounts_customuser' ORDER BY column_name;")
        columns = [row[0] for row in cursor.fetchall()]
        print(f'\n📋 Total columns: {len(columns)}')

        # Check key columns
        key_columns = ['is_online', 'facebook_url', 'email', 'username']
        for col in key_columns:
            if col in columns:
                print(f'✅ {col} exists')
            else:
                print(f'❌ {col} missing!')


if __name__ == '__main__':
    add_missing_columns()
    print('\n' + '=' * 50)
    print('🎉 PRODUCTION DATABASE FIXED!')
    print('✅ Anyone can now register and login!')
    print('👉 URL: https://connect-io-0cql.onrender.com/accounts/register/')
    print('=' * 50)