#!/bin/bash
set -e

# Скрипт для создания релиза Mirai Agent

VERSION=${1:-$(date +%Y.%m.%d)}
TAG="v${VERSION}"

echo "🚀 Creating release ${TAG}"

# Проверяем, что мы на main ветке
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "❌ Error: Must be on main branch (currently on: $CURRENT_BRANCH)"
    exit 1
fi

# Проверяем, что рабочая директория чистая
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Error: Working directory is not clean"
    git status --short
    exit 1
fi

# Создаем тег
echo "📝 Creating tag ${TAG}"
git tag -a "$TAG" -m "Release ${TAG}

🚀 Mirai Agent ${TAG}

### Docker Images:
- ghcr.io/ageekey/mirai-api:${TAG}
- ghcr.io/ageekey/mirai-trader:${TAG}  
- ghcr.io/ageekey/mirai-services:${TAG}

### Latest Images:
- ghcr.io/ageekey/mirai-api:latest
- ghcr.io/ageekey/mirai-trader:latest
- ghcr.io/ageekey/mirai-services:latest"

# Пушим тег
echo "📦 Pushing tag ${TAG} to origin"
git push origin "$TAG"

echo "✅ Release ${TAG} created successfully!"
echo "🔗 Check status at: https://github.com/AgeeKey/mirai-agent/actions"
echo "📋 Release will be available at: https://github.com/AgeeKey/mirai-agent/releases/tag/${TAG}"
