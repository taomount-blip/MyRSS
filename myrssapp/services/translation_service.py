"""AI translation service using Tencent Hunyuan API (OpenAI-compatible)."""

import hashlib
import logging
from typing import Optional

from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class TranslationService:
    """Chinese-English bidirectional translation with cache support.

    Uses the OpenAI-compatible API protocol, defaulting to Tencent Hunyuan.
    """

    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._client = None
        self._api_key: str = ""
        self._base_url: str = ""
        self._model: str = ""

    def _lazy_init_client(self) -> Optional[str]:
        """Initialize the OpenAI client from settings.
        
        Returns None on success, or an error message string on failure.
        """
        from ..services.settings_service import SettingsService
        settings = SettingsService(self._db)

        api_key = settings.translation_api_key
        base_url = settings.translation_api_url
        model = settings.translation_model

        if not api_key:
            return "未设置 API Key"

        if not base_url:
            return "未设置 API 地址"

        # 用户可能误填了完整路径，自动修正
        if base_url.endswith("/chat/completions"):
            base_url = base_url[:-len("/chat/completions")]

        if (api_key != self._api_key or base_url != self._base_url
                or model != self._model):
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )
                self._api_key = api_key
                self._base_url = base_url
                self._model = model
            except Exception as e:
                return f"API 客户端初始化失败: {e}"
        return None

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
    ) -> Optional[str]:
        """Translate text. Returns the translated text or None on failure.

        Args:
            text: The text to translate.
            source_lang: Source language code ('zh', 'en', 'auto').
            target_lang: Target language code ('zh', 'en').

        Returns:
            Translated text string, or None on error.
        """
        if not text or not text.strip():
            return ""

        text_to_translate = text.strip()

        # Check cache
        cache_key = self._hash(text_to_translate, source_lang, target_lang)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        err = self._lazy_init_client()
        if err:
            return f"[配置错误] {err}"

        # Build system prompt based on language direction
        if target_lang == "zh":
            system_msg = "你是一个专业的翻译助手。请将用户输入的英文翻译成流畅自然的中文。只返回翻译结果，不要添加任何解释。"
        elif target_lang == "en":
            system_msg = "You are a professional translator. Translate the user's Chinese text into fluent, natural English. Only return the translation, no explanations."
        else:
            system_msg = "You are a professional translator. Translate the user's text accurately. Only return the translation."

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": text_to_translate},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            result = response.choices[0].message.content.strip()

            # Save to cache
            self._cache_set(cache_key, text_to_translate, source_lang, target_lang, result)
            return result

        except Exception as e:
            err_msg = str(e)
            logger.error("Translation API error: %s", e)
            return f"[API 错误] {err_msg}"

    def translate_en_to_zh(self, text: str) -> Optional[str]:
        """Convenience: English → Chinese."""
        return self.translate(text, source_lang="en", target_lang="zh")

    def translate_zh_to_en(self, text: str) -> Optional[str]:
        """Convenience: Chinese → English."""
        return self.translate(text, source_lang="zh", target_lang="en")

    def auto_translate_to_zh(self, text: str) -> Optional[str]:
        """Auto-detect source language and translate to Chinese."""
        return self.translate(text, source_lang="auto", target_lang="zh")

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------
    def _cache_get(self, source_hash: str) -> Optional[str]:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT translated_text FROM translation_cache WHERE source_hash = ?",
            (source_hash,),
        ).fetchone()
        return row["translated_text"] if row else None

    def _cache_set(
        self,
        source_hash: str,
        source_text: str,
        source_lang: str,
        target_lang: str,
        translated_text: str,
    ) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO translation_cache "
            "(source_hash, source_text, source_lang, target_lang, translated_text) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_hash, source_text, source_lang, target_lang, translated_text),
        )
        conn.commit()

    @staticmethod
    def _hash(text: str, source_lang: str, target_lang: str) -> str:
        raw = f"{text}|{source_lang}|{target_lang}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
