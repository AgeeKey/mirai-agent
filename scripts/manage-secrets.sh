#!/bin/bash

# GitHub Actions Secrets & Variables Management Script
# Требует токен GH_TOKEN с правами repo + admin:org

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка наличия токена
check_token() {
    if [ -z "$GH_TOKEN" ]; then
        echo -e "${RED}❌ Ошибка: GH_TOKEN не найден в переменных окружения${NC}"
        echo -e "${YELLOW}💡 Убедитесь что токен GH_TOKEN добавлен в Codespaces secrets${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Токен GH_TOKEN найден${NC}"
}

# Получение public key для шифрования
get_public_key() {
    local repo=$1
    echo -e "${BLUE}🔑 Получаем public key для репозитория $repo...${NC}"
    
    curl -s -H "Authorization: Bearer $GH_TOKEN" \
         -H "Accept: application/vnd.github+json" \
         "https://api.github.com/repos/$repo/actions/secrets/public-key"
}

# Шифрование значения с помощью PyNaCl
encrypt_secret() {
    local value=$1
    local public_key=$2
    
    python3 << EOF
import base64
from nacl import encoding, public
from nacl.public import SealedBox

# Декодируем public key
public_key_bytes = base64.b64decode("$public_key")
public_key_obj = public.PublicKey(public_key_bytes)

# Шифруем значение
sealed_box = SealedBox(public_key_obj)
encrypted = sealed_box.encrypt(b"$value")

# Возвращаем base64 encoded результат
print(base64.b64encode(encrypted).decode())
EOF
}

# Создание repository secret
create_repository_secret() {
    local repo=$1
    local secret_name=$2
    local secret_value=$3
    
    echo -e "${BLUE}🔐 Создаем repository secret $secret_name...${NC}"
    
    # Получаем public key
    local key_data=$(get_public_key "$repo")
    local key_id=$(echo "$key_data" | jq -r '.key_id')
    local public_key=$(echo "$key_data" | jq -r '.key')
    
    if [ "$key_id" = "null" ] || [ "$public_key" = "null" ]; then
        echo -e "${RED}❌ Ошибка получения public key${NC}"
        echo "$key_data"
        return 1
    fi
    
    # Шифруем значение
    local encrypted_value=$(encrypt_secret "$secret_value" "$public_key")
    
    # Создаем secret
    local response=$(curl -s -X PUT \
        -H "Authorization: Bearer $GH_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$repo/actions/secrets/$secret_name" \
        -d "{\"encrypted_value\":\"$encrypted_value\",\"key_id\":\"$key_id\"}")
    
    if echo "$response" | grep -q '"message"'; then
        echo -e "${RED}❌ Ошибка создания secret:${NC}"
        echo "$response" | jq .
        return 1
    else
        echo -e "${GREEN}✅ Secret $secret_name создан успешно${NC}"
    fi
}

# Создание repository variable
create_repository_variable() {
    local repo=$1
    local var_name=$2
    local var_value=$3
    
    echo -e "${BLUE}📝 Создаем repository variable $var_name...${NC}"
    
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $GH_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$repo/actions/variables" \
        -d "{\"name\":\"$var_name\",\"value\":\"$var_value\"}")
    
    if echo "$response" | grep -q '"message"'; then
        echo -e "${RED}❌ Ошибка создания variable:${NC}"
        echo "$response" | jq .
        return 1
    else
        echo -e "${GREEN}✅ Variable $var_name создана успешно${NC}"
    fi
}

# Список repository secrets
list_repository_secrets() {
    local repo=$1
    echo -e "${BLUE}📋 Список repository secrets для $repo:${NC}"
    
    curl -s -H "Authorization: Bearer $GH_TOKEN" \
         -H "Accept: application/vnd.github+json" \
         "https://api.github.com/repos/$repo/actions/secrets" | \
         jq '.secrets[]? | {name: .name, created_at: .created_at, updated_at: .updated_at}'
}

# Список repository variables
list_repository_variables() {
    local repo=$1
    echo -e "${BLUE}📋 Список repository variables для $repo:${NC}"
    
    curl -s -H "Authorization: Bearer $GH_TOKEN" \
         -H "Accept: application/vnd.github+json" \
         "https://api.github.com/repos/$repo/actions/variables" | \
         jq '.variables[]? | {name: .name, value: .value, created_at: .created_at, updated_at: .updated_at}'
}

# Основная функция
main() {
    echo -e "${BLUE}🚀 GitHub Actions Secrets & Variables Manager${NC}"
    echo "=========================================="
    
    check_token
    
    local repo="AgeeKey/mirai-agent"
    
    case "${1:-help}" in
        "create-secret")
            if [ $# -ne 3 ]; then
                echo "Использование: $0 create-secret SECRET_NAME SECRET_VALUE"
                exit 1
            fi
            create_repository_secret "$repo" "$2" "$3"
            ;;
        "create-variable")
            if [ $# -ne 3 ]; then
                echo "Использование: $0 create-variable VAR_NAME VAR_VALUE"
                exit 1
            fi
            create_repository_variable "$repo" "$2" "$3"
            ;;
        "list-secrets")
            list_repository_secrets "$repo"
            ;;
        "list-variables")
            list_repository_variables "$repo"
            ;;
        "test")
            echo -e "${YELLOW}🧪 Тестовый режим - создаем тестовые secret и variable${NC}"
            create_repository_secret "$repo" "TEST_SECRET" "test-secret-value-$(date +%s)"
            create_repository_variable "$repo" "TEST_VARIABLE" "test-variable-value-$(date +%s)"
            echo -e "${GREEN}✅ Тест завершен${NC}"
            ;;
        *)
            echo "Доступные команды:"
            echo "  create-secret SECRET_NAME SECRET_VALUE  - Создать repository secret"
            echo "  create-variable VAR_NAME VAR_VALUE      - Создать repository variable"
            echo "  list-secrets                            - Список repository secrets"
            echo "  list-variables                          - Список repository variables"
            echo "  test                                    - Создать тестовые secret и variable"
            ;;
    esac
}

# Запуск скрипта
main "$@"