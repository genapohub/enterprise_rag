"""OpenAI-compatible LLM client with stub fallback."""
from typing import List
import httpx
from app.config import Settings


NO_HIT = "知识库中未找到相关内容"


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.stub = settings.use_llm_stub()

    def answer(self, question: str, contexts: List[str]) -> str:
        if not contexts:
            return NO_HIT
        if self.stub:
            joined = "\n---\n".join(contexts[:3])
            return f"根据知识库资料：{joined[:500]}"
        return self._api_chat(question, contexts)

    def _api_chat(self, question: str, contexts: List[str]) -> str:
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        system = (
            "你是企业知识库助手。仅依据给定检索片段作答；"
            "若片段不足以回答，回复「知识库中未找到相关内容」，不要编造。"
        )
        ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
        user = f"检索片段：\n{ctx}\n\n用户问题：{question}"
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
