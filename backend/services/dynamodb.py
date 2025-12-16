import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, Dict
from datetime import datetime
import os
import hashlib
import secrets
import importlib

class DynamoDBService:
    """Сервіс для роботи з користувачами та API ключами"""
    
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('rf_checker_users')
        self.user_limits_table = self.dynamodb.Table('rf_checker_user_limits')
        self.checks_table = self.dynamodb.Table('rf_checker_checks')
        self._tables_verified = False

        # --- Додаємо автоматичну синхронізацію полів ---
        self._sync_table_fields()

    def _sync_table_fields(self):
        """Синхронізувати всі таблиці з шаблонами (оновити поля)"""
        try:
            init_dynamodb = importlib.import_module("backend.services.init_dynamodb")
            init_dynamodb.sync_all_tables_from_templates()
        except Exception as e:
            print(f"⚠️  Не вдалося синхронізувати поля таблиць: {e}")

    def _verify_tables_exist(self):
        """Перевірити що таблиці існують"""
        if self._tables_verified:
            return
        
        try:
            self.users_table.load()
            self.user_limits_table.load()
            self.checks_table.load()
            self._tables_verified = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Warning: Tables don't exist. Creating tables...")
                from backend.services.init_dynamodb import init_tables
                init_tables()
                self._tables_verified = True
                # Після створення таблиць — одразу оновити поля
                self._sync_table_fields()
            else:
                raise
    
    def create_user(self, username: str, password: str) -> Dict:
        """Створити нового користувача"""
        try:
            self._verify_tables_exist()
            
            # Перевірити чи користувач вже існує
            response = self.users_table.get_item(Key={'username': username})
            if 'Item' in response:
                raise ValueError("User already exists")
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            api_key = self._generate_api_key()
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            user_id = secrets.token_hex(16)
            
            item = {
                'username': username,
                'user_id': user_id,
                'password_hash': password_hash,
                'api_key_hash': api_key_hash,
                'created_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            self.users_table.put_item(Item=item)
            
            # Ініціалізуємо лімити для користувача
            self.user_limits_table.put_item(
                Item={
                    'user_id': user_id,
                    'max_checks': 10,
                    'checks_count': 0,
                    'created_at': datetime.now().isoformat()
                }
            )
            
            return {
                'username': username,
                'user_id': user_id,
                'api_key': api_key
            }
        except ValueError as e:
            raise Exception(f"Validation error: {str(e)}")
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise Exception(f"Error creating user: {str(e)}")
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Перевірити логін і пароль"""
        try:
            self._verify_tables_exist()
            
            response = self.users_table.get_item(Key={'username': username})
            user = response.get('Item')
            
            if not user or not user.get('is_active'):
                return None
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user['password_hash'] == password_hash:
                return {
                    'username': user['username'],
                    'created_at': user['created_at'],
                    'user_id': user['user_id'],
                    'api_key': user['api_key_hash']  # Повертаємо хеш для безпеки
                }
            
            return None
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            return None
    
    def verify_api_key(self, api_key_hash: str) -> Optional[Dict]:
        """Перевірити API ключ і повернути дані користувача"""
        try:
            self._verify_tables_exist()
            
            # Використати GSI для швидкого пошуку
            response = self.users_table.query(
                IndexName='api_key_index',
                KeyConditionExpression=Key('api_key_hash').eq(api_key_hash)
            )
            
            items = response.get('Items', [])
            if items and items[0].get('is_active'):
                user = items[0]
                return {
                    'username': user['username'],
                    'user_id': user.get('user_id'),
                    'id': user.get('user_id'),  # Для сумісності
                    'created_at': user['created_at']
                }
            
            return None
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            return None
    
    def regenerate_api_key(self, username: str) -> str:
        """Згенерувати новий API ключ для користувача"""
        try:
            self._verify_tables_exist()
            
            api_key = self._generate_api_key()
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            self.users_table.update_item(
                Key={'username': username},
                UpdateExpression='SET api_key_hash = :key, updated_at = :time',
                ExpressionAttributeValues={
                    ':key': api_key_hash,
                    ':time': datetime.now().isoformat()
                }
            )
            
            return api_key
        except ClientError as e:
            raise Exception(f"DynamoDB error: {str(e)}")
    
    def _generate_api_key(self) -> str:
        """Згенерувати випадковий API ключ"""
        return secrets.token_urlsafe(32)
    
    # === Методи для роботи з лімітами ===
    
    def get_user_checks_count(self, user_id: str) -> int:
        """Отримати кількість перевірок користувача"""
        try:
            self._verify_tables_exist()
            
            response = self.user_limits_table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item'].get('checks_count', 0)
            return 0
        except ClientError as e:
            print(f"Error getting user checks count: {e}")
            return 0
    
    def increment_user_checks(self, user_id: str) -> int:
        """Збільшити лічильник перевірок користувача"""
        try:
            self._verify_tables_exist()
            
            response = self.user_limits_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET checks_count = if_not_exists(checks_count, :zero) + :inc, last_check = :timestamp',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':zero': 0,
                    ':timestamp': datetime.utcnow().isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            return response['Attributes']['checks_count']
        except ClientError as e:
            print(f"Error incrementing user checks: {e}")
            raise
    
    def get_user_limit(self, user_id: str) -> int:
        """Отримати ліміт користувача (за замовчуванням 10)"""
        try:
            self._verify_tables_exist()
            
            response = self.user_limits_table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item'].get('max_checks', 10)
            return 10  # Дефолтний ліміт
        except ClientError as e:
            print(f"Error getting user limit: {e}")
            return 10
    
    def set_user_limit(self, user_id: str, max_checks: int):
        """Встановити ліміт для користувача (для адміністраторів)"""
        try:
            self._verify_tables_exist()
            
            self.user_limits_table.put_item(
                Item={
                    'user_id': user_id,
                    'max_checks': max_checks,
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
        except ClientError as e:
            print(f"Error setting user limit: {e}")
            raise
    
    def reset_user_checks(self, user_id: str):
        """Скинути лічильник перевірок користувача"""
        try:
            self._verify_tables_exist()
            
            self.user_limits_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET checks_count = :zero, last_reset = :timestamp',
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        except ClientError as e:
            print(f"Error resetting user checks: {e}")
            raise
    
    def save_check_history(self, user_id: str, check_type: str, data: dict, result: dict):
        """Зберегти історію перевірок"""
        try:
            self._verify_tables_exist()
            
            self.checks_table.put_item(
                Item={
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'check_type': check_type,
                    'data': data,
                    'result': result
                }
            )
        except ClientError as e:
            print(f"Error saving check history: {e}")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Отримати статистику користувача"""
        try:
            self._verify_tables_exist()
            
            checks_count = self.get_user_checks_count(user_id)
            limit = self.get_user_limit(user_id)
            return {
                'user_id': user_id,
                'checks_used': checks_count,
                'max_checks': limit,
                'checks_remaining': limit - checks_count
            }
        except ClientError as e:
            print(f"Error getting user stats: {e}")
            raise