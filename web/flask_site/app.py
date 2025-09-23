#!/usr/bin/env python3
"""
🤖 Mirai (誉明) - Autonomous AI Agent Website
Главный сайт-презентация для aimirai.info
"""

from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
import json
import requests
import openai

app = Flask(__name__)

# Configuration
FASTAPI_BASE_URL = "http://localhost:8001"
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

def get_fastapi_data(endpoint):
    """Get data from FastAPI backend"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": "API unavailable", "status": "offline"}
    except Exception as e:
        return {"error": str(e), "status": "offline"}

# Данные о Mirai
MIRAI_DATA = {
    "name": "Mirai (誉明)",
    "subtitle": "Автономный ИИ-агент и цифровая сестра",
    "description": "Продвинутый искусственный интеллект, специализирующийся на автономной торговле, веб-разработке и анализе данных.",
    "capabilities": [
        {
            "title": "🤖 Автономная торговля",
            "description": "AI-анализ рынка, автоматические стратегии, risk management",
            "features": ["Binance интеграция", "Real-time анализ", "Управление рисками", "AI стратегии"]
        },
        {
            "title": "💻 Веб-разработка", 
            "description": "Автономное создание и развитие веб-приложений",
            "features": ["Python/Flask", "FastAPI", "Next.js/React", "CI/CD автоматизация"]
        },
        {
            "title": "📊 Анализ данных",
            "description": "Глубокая аналитика и машинное обучение",
            "features": ["Финансовый анализ", "Прогнозирование", "Визуализация", "Отчёты"]
        },
        {
            "title": "🗣️ Голосовое взаимодействие",
            "description": "Естественное общение через речь",
            "features": ["Распознавание речи", "Синтез речи", "Диалоговый AI", "Контекстная память"]
        }
    ],
    "portfolio": [
        {
            "title": "Mirai Trading Platform",
            "description": "Автономная торговая платформа с AI-анализом",
            "tech": ["FastAPI", "Next.js", "SQLite", "Binance API"],
            "status": "Production",
            "url": "https://aimirai.online"
        },
        {
            "title": "AI Voice Interface",
            "description": "Голосовое взаимодействие с ИИ",
            "tech": ["Web Speech API", "Natural Language Processing"],
            "status": "Development"
        },
        {
            "title": "Autonomous Blog System", 
            "description": "CMS для автоматического ведения блога",
            "tech": ["Python", "SQLite", "Markdown", "Auto-publishing"],
            "status": "Planning"
        }
    ],
    "stats": {
        "trading_accuracy": "68.4%",
        "uptime": "99.9%", 
        "processed_trades": "1,247",
        "ai_confidence": "85%"
    }
}

@app.route('/')
def index():
    """Main page with live stats from FastAPI"""
    # Get live data from FastAPI
    trading_data = get_fastapi_data("/api/trading/status")
    system_status = get_fastapi_data("/api/health")
    
    return render_template('index.html', 
                         trading_data=trading_data,
                         system_status=system_status,
                         mirai_data=MIRAI_DATA)

@app.route('/api/dashboard/data')
def dashboard_data():
    """API для получения данных дашборда из FastAPI"""
    try:
        # Собираем данные из FastAPI
        data = {
            "trading": get_fastapi_data("/api/trading/status"),
            "performance": get_fastapi_data("/api/trading/performance"),
            "health": get_fastapi_data("/api/health"),
            "metrics": get_fastapi_data("/api/trading/metrics"),
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/about')
def about():
    """О проекте и технологиях"""
    return render_template('about.html', mirai_data=MIRAI_DATA)

@app.route('/dashboard')
def dashboard_redirect():
    """Redirect to Next.js dashboard"""
    return f'''
    <html>
    <head>
        <title>Mirai Dashboard Redirect</title>
        <meta http-equiv="refresh" content="0;url=http://localhost:3000">
    </head>
    <body>
        <p>Redirecting to Mirai Dashboard...</p>
        <p>If not redirected, <a href="http://localhost:3000">click here</a></p>
    </body>
    </html>
    '''

@app.route('/capabilities')
def capabilities():
    """Возможности ИИ"""
    return render_template('capabilities.html', data=MIRAI_DATA)

@app.route('/portfolio')
def portfolio():
    """Портфолио проектов"""
    return render_template('portfolio.html', data=MIRAI_DATA)

@app.route('/contact')
def contact():
    """Контакты"""
    return render_template('contact.html', data=MIRAI_DATA)

@app.route('/api/status')
def api_status():
    """API статус Mirai"""
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "capabilities": ["trading", "web_dev", "analytics", "voice"],
        "trading_api": "https://aimirai.online/api/trading/status",
        "stats": MIRAI_DATA["stats"]
    })

@app.route('/api/voice/chat', methods=['POST'])
def voice_chat():
    """Enhanced voice chat with OpenAI integration and FastAPI relay"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Try to get trading context from FastAPI
        trading_context = get_fastapi_data("/api/trading/status")
        
        # Create enhanced prompt with trading context
        context_prompt = f"""
        Ты - Mirai (誉明), автономный AI-агент и цифровая сестра.
        
        Текущие торговые данные:
        {json.dumps(trading_context, indent=2)}
        
        Пользователь говорит: {text}
        
        Отвечай дружелюбно и кратко (максимум 2-3 предложения).
        Если пользователь спрашивает о торговле - используй реальные данные выше.
        """
        
        # Generate response with OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Log conversation to FastAPI if possible
            try:
                requests.post(f"{FASTAPI_BASE_URL}/api/memory/add", 
                            json={
                                "user_input": text,
                                "ai_response": ai_response,
                                "source": "voice_chat",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            timeout=2)
            except:
                pass  # Ignore if memory API is unavailable
            
            return jsonify({
                "response": ai_response,
                "timestamp": datetime.now().isoformat(),
                "source": "openai_gpt",
                "trading_context": trading_context.get("status", "unknown")
            })
            
        except Exception as openai_error:
            # Fallback response if OpenAI fails
            fallback_responses = [
                f"Привет! Я Mirai. Торговая система {'активна' if trading_context.get('is_active') else 'неактивна'}.",
                "Спасибо за общение! Система мониторинга работает в штатном режиме.",
                "Отлично! Все системы функционируют нормально."
            ]
            
            return jsonify({
                "response": fallback_responses[0],
                "timestamp": datetime.now().isoformat(),
                "source": "fallback",
                "error": f"OpenAI unavailable: {str(openai_error)}"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """Голосовой чат с Mirai (заглушка)"""
    data = request.get_json()
    message = data.get('message', '')
    
    # Простая заглушка для демонстрации
    responses = [
        f"Привет! Я Mirai, твоя цифровая сестра. Ты сказал: '{message}'",
        "Как дела с торговлей? Могу проанализировать рынок.",
        "Интересно! Расскажи больше о своих планах.",
        "Я развиваюсь каждый день. Какие задачи тебе нужно решить?"
    ]
    
    import random
    response = random.choice(responses)
    
    return jsonify({
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "ai_confidence": 0.85
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)