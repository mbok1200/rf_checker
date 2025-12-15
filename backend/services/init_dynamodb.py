import boto3
import os
from dotenv import load_dotenv
import pathlib
import sys
from botocore.exceptions import ClientError

# Завантажити .env
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT / ".env")

def get_dynamodb_client():
    """Отримати DynamoDB клієнт"""
    return boto3.client(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

def init_tables():
    """Ініціалізація всіх таблиць DynamoDB (безпечно, без перетирання)"""
    dynamodb = get_dynamodb_client()

    tables = [
        {
            'TableName': 'rf_checker_users',
            'KeySchema': [
                {'AttributeName': 'username', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'username', 'AttributeType': 'S'},
                {'AttributeName': 'api_key_hash', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'isAdmin', 'AttributeType': 'N'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'api_key_index',
                    'KeySchema': [
                        {'AttributeName': 'api_key_hash', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'user_id_index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        },
        {
            'TableName': 'rf_checker_user_limits',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        },
        {
            'TableName': 'rf_checker_checks',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ]

    for table_config in tables:
        table_name = table_config['TableName']
        try:
            # Спробувати створити таблицю
            dynamodb.create_table(**table_config)
            print(f"✅ Created table: {table_name}")
            
            # Почекати поки таблиця створюється
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists - skipping")
            else:
                print(f"❌ Error creating {table_name}: {e}")
                raise

def create_users_table():
    """Створити таблицю користувачів в DynamoDB"""
    
    dynamodb = get_dynamodb_client()
    
    try:
        # Перевірити чи таблиця вже існує
        try:
            dynamodb.describe_table(TableName='rf_checker_users')
            print("⚠️  Таблиця 'rf_checker_users' вже існує!")
            return False
        except dynamodb.exceptions.ResourceNotFoundException:
            pass
        
        # Створити таблицю
        table = dynamodb.create_table(
            TableName='rf_checker_users',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'api_key_hash',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'api_key_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'api_key_hash',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print("⏳ Створюємо таблицю 'rf_checker_users'...")
        
        # Почекати поки таблиця створюється
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='rf_checker_users')
        
        print("✅ Таблиця 'rf_checker_users' успішно створена!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка створення таблиці: {str(e)}")
        raise

def delete_users_table():
    """Видалити таблицю користувачів"""
    
    dynamodb = get_dynamodb_client()
    
    try:
        # Перевірити чи таблиця існує
        try:
            dynamodb.describe_table(TableName='rf_checker_users')
        except dynamodb.exceptions.ResourceNotFoundException:
            print("⚠️  Таблиця 'rf_checker_users' не існує!")
            return False
        
        # Підтвердження видалення
        confirm = input("⚠️  Ви впевнені що хочете видалити таблицю 'rf_checker_users'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Видалення скасовано")
            return False
        
        print("⏳ Видаляємо таблицю 'rf_checker_users'...")
        dynamodb.delete_table(TableName='rf_checker_users')
        
        # Почекати поки таблиця видаляється
        waiter = dynamodb.get_waiter('table_not_exists')
        waiter.wait(TableName='rf_checker_users')
        
        print("✅ Таблиця 'rf_checker_users' успішно видалена!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка видалення таблиці: {str(e)}")
        raise

def recreate_users_table():
    """Видалити та створити таблицю заново"""
    print("🔄 Пересоздання таблиці...")
    
    # Видалити якщо існує
    try:
        delete_users_table()
    except:
        pass
    
    # Створити нову
    create_users_table()

def delete_all_tables():
    """Видалити всі таблиці"""
    dynamodb = get_dynamodb_client()
    tables = ['rf_checker_users', 'rf_checker_user_limits', 'rf_checker_checks']
    
    for table_name in tables:
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"⏳ Deleting {table_name}...")
            waiter = dynamodb.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
            print(f"✅ Deleted {table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"⚠️  Table {table_name} doesn't exist")
            else:
                print(f"❌ Error deleting {table_name}: {e}")

def list_tables():
    """Показати всі таблиці"""
    dynamodb = get_dynamodb_client()
    
    try:
        response = dynamodb.list_tables()
        tables = response.get('TableNames', [])
        
        if tables:
            print("\n📋 Наявні таблиці DynamoDB:")
            for table in tables:
                print(f"  - {table}")
        else:
            print("ℹ️  Немає таблиць в DynamoDB")
            
        return tables
        
    except Exception as e:
        print(f"❌ Помилка отримання списку таблиць: {str(e)}")
        raise

def show_table_info():
    """Показати інформацію про таблицю"""
    dynamodb = get_dynamodb_client()
    
    try:
        response = dynamodb.describe_table(TableName='rf_checker_users')
        table = response['Table']
        
        print("\n📊 Інформація про таблицю 'rf_checker_users':")
        print(f"  Status: {table['TableStatus']}")
        print(f"  Item Count: {table['ItemCount']}")
        print(f"  Size (bytes): {table['TableSizeBytes']}")
        print(f"  Created: {table['CreationDateTime']}")
        
        if 'GlobalSecondaryIndexes' in table:
            print(f"  Indexes: {len(table['GlobalSecondaryIndexes'])}")
            for idx in table['GlobalSecondaryIndexes']:
                print(f"    - {idx['IndexName']}: {idx['IndexStatus']}")
        
    except dynamodb.exceptions.ResourceNotFoundException:
        print("⚠️  Таблиця 'rf_checker_users' не існує!")
    except Exception as e:
        print(f"❌ Помилка: {str(e)}")

def show_menu():
    """Показати меню"""
    print("\n" + "="*50)
    print("🔧 DynamoDB Management Tool")
    print("="*50)
    print("1. Створити таблицю користувачів")
    print("2. Видалити таблицю користувачів")
    print("3. Пересоздати таблицю (видалити + створити)")
    print("4. Показати список всіх таблиць")
    print("5. Показати інформацію про таблицю")
    print("6. Ініціалізувати всі таблиці")
    print("7. Вихід")
    print("="*50)

if __name__ == "__main__":
    # Перевірка змінних середовища
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("❌ Помилка: AWS credentials не налаштовані в .env файлі!")
        sys.exit(1)
    
    # Якщо передано аргументи командного рядка
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'create':
            create_users_table()
        elif command == 'delete':
            delete_users_table()
        elif command == 'recreate':
            recreate_users_table()
        elif command == 'list':
            list_tables()
        elif command == 'info':
            show_table_info()
        elif command == 'init':
            print("🚀 Initializing DynamoDB tables...")
            init_tables()
            print("✅ Done!")
        elif command == 'delete_all':
            print("🔥 Deleting all tables...")
            delete_all_tables()
            print("✅ Done!")
        elif command == 'recreate_all':
            print("🔄 Recreating tables...")
            delete_all_tables()
            init_tables()
            print("✅ Done!")
        else:
            print(f"❌ Невідома команда: {command}")
            print("\nДоступні команди:")
            print("  create     - створити таблицю користувачів")
            print("  delete     - видалити таблицю користувачів")
            print("  recreate   - пересоздати таблицю користувачів")
            print("  list       - список таблиць")
            print("  info       - інформація про таблицю")
            print("  init       - ініціалізувати всі таблиці")
            print("  delete_all - видалити всі таблиці")
            print("  recreate_all- пересоздати всі таблиці")
    else:
        # Якщо без аргументів - ініціалізувати всі таблиці
        print("🚀 Initializing DynamoDB tables...")
        init_tables()
        print("✅ Done!")