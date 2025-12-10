"""
AI proxy endpoints: securely call Gemini API from the backend using server-side key.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
import requests

from config.settings import GEMINI_API_KEY, APP_ENV
from api.auth import auth_required, log_api_access


logger = logging.getLogger('financial_data_ml.api.ai')
ai_bp = Blueprint('ai', __name__)


GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent'


@ai_bp.before_request
def before_request():
    log_api_access()


@ai_bp.route('/ai/generate', methods=['POST'])
@auth_required
def ai_generate():
    """
    Returns a static stub response. Real AI processing is disabled due to legal requirements.
    """
    
    # Stub response with legal disclaimer
    stub_text = (
        "Мы больше не предоставляем пользователям информацию о финансах."
        "Это связано с требованиями законодательства и риском неверной интерпретации такой информации. "
        "Все данные в сервисе носят исключительно информационный характер и не являются руководством "
        "к инвестициям или иным финансовым решениям. К сожалению мы были вынужны отключить AI-ассистента."
    )

    # Mimic Gemini API response structure so frontend keeps working
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": stub_text
                        }
                    ],
                    "role": "model"
                },
                "finishReason": "STOP",
                "index": 0
            }
        ]
    }

    return jsonify({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'data': mock_gemini_response
    }), 200



