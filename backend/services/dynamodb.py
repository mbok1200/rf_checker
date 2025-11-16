import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, Dict
from datetime import datetime
import os
import hashlib
import secrets

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
        self._verify_table_exists()
    
    def _verify_table_exists(self):
        """Перевірити що таблиця існує"""
        try:
            self.users_table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise Exception(
                    "Таблиця 'rf_checker_users' не існує! "
                    "Запустіть: python -m backend.services.init_dynamodb"
                )
            raise
    
    def create_user(self, username: str, password: str) -> Dict:
        """Створити нового користувача"""
        try:
            # Перевірити чи користувач вже існує
            response = self.users_table.get_item(Key={'username': username})
            if 'Item' in response:
                raise ValueError("User already exists")
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            api_key = self._generate_api_key()
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            item = {
                'username': username,
                'password_hash': password_hash,
                'api_key_hash': api_key_hash,
                'created_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            self.users_table.put_item(Item=item)
            
            return {
                'username': username,
                'api_key': api_key
            }
        except ClientError as e:
            raise Exception(f"DynamoDB error: {str(e)}")
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Перевірити логін і пароль"""
        try:
            response = self.users_table.get_item(Key={'username': username})
            user = response.get('Item')
            
            if not user or not user.get('is_active'):
                return None
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user['password_hash'] == password_hash:
                return {
                    'username': user['username'],
                    'created_at': user['created_at'],
                    'api_key': user['api_key_hash']  # Повертаємо хеш для безпеки
                }
            
            return None
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            return None
    
    def verify_api_key(self, api_key_hash: str) -> Optional[str]:
        """Перевірити API ключ і повернути username"""
        try:
            # api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Використати GSI для швидкого пошуку
            response = self.users_table.query(
                IndexName='api_key_index',
                KeyConditionExpression=Key('api_key_hash').eq(api_key_hash)
            )
            
            items = response.get('Items', [])
            if items and items[0].get('is_active'):
                return items[0]['username']
            
            return None
        except ClientError as e:
            print(f"DynamoDB error: {str(e)}")
            return None
    
    def regenerate_api_key(self, username: str) -> str:
        """Згенерувати новий API ключ для користувача"""
        try:
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