# Створити таблицю
python -m backend.services.init_dynamodb create

# Видалити таблицю
python -m backend.services.init_dynamodb delete

# Пересоздати таблицю
python -m backend.services.init_dynamodb recreate

# Список таблиць
python -m backend.services.init_dynamodb list

# Інформація про таблицю
python -m backend.services.init_dynamodb info

python -m backend.services.init_dynamodb