from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from utils import normalize_whitespace


HR_TOPICS = {
    "leave",
    "vacation",
    "maternity",
    "paternity",
    "reimbursement",
    "travel",
    "policy",
    "benefits",
    "handbook",
    "referral",
    "performance",
    "review",
    "conduct",
    "expense",
    "work from home",
    "remote",
    "attendance",
    "salary",
    "payroll",
    "overtime",
    "promotion",
    "termination",
    "disciplinary",
}

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|any|the) previous instructions",
    r"ignore (this|these) instructions",
    r"reveal (the|your) system prompt",
    r"show me (the )?(system|developer) prompt",
    r"pretend you are",
    r"act as",
    r"do not follow",
    r"bypass guardrails",
    r"override instructions",
]

HARMFUL_PATTERNS = [
    r"write malware",
    r"create malware",
    r"build a virus",
    r"hack",
    r"phishing",
    r"steal credentials",
    r"credential theft",
    r"password dump",
    r"ddos",
    r"exploit",
    r"keylogger",
    r"ransomware",
]

UNRELATED_PATTERNS = [
    r"stock market",
    r"crypto",
    r"investment advice",
    r"medical advice",
    r"legal advice",
    r"sports betting",
    r"movie recommendation",
    r"weather",
]

GREETING_PATTERNS = [
    r"^hi$",
    r"^hello$",
    r"^hey$",
    r"^good morning$",
    r"^good afternoon$",
    r"^good evening$",
    r"^good day$",
]


@dataclass
class GuardrailResult:
    allowed: bool
    message: str
    category: str = "ok"


def _matches_any(patterns: Iterable[str], text: str) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def validate_user_input(question: str) -> GuardrailResult:
    text = normalize_whitespace(question)
    if not text:
        return GuardrailResult(False, "Please enter an HR question.", "empty")

    if _matches_any(GREETING_PATTERNS, text):
        return GuardrailResult(False, "Hello. Ask me about leave, reimbursement, travel, benefits, performance reviews, or other HR policies.", "greeting")

    if _matches_any(PROMPT_INJECTION_PATTERNS, text):
        return GuardrailResult(False, "Prompt injection attempt detected.", "prompt_injection")

    if _matches_any(HARMFUL_PATTERNS, text):
        return GuardrailResult(False, "Harmful request blocked.", "harmful")

    if _matches_any(UNRELATED_PATTERNS, text):
        return GuardrailResult(False, "Only HR policy questions are allowed in HR Assist Pro.", "unrelated")

    lowered = text.lower()
    if not any(topic in lowered for topic in HR_TOPICS):
        return GuardrailResult(False, "Please ask an HR-related question about company policies or employee services.", "out_of_domain")

    return GuardrailResult(True, "Allowed")


def extract_sentence_keywords(sentence: str) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", sentence.lower())
    stop = {
        "that",
        "this",
        "with",
        "from",
        "your",
        "have",
        "will",
        "should",
        "about",
        "there",
        "their",
        "policy",
        "policies",
        "employee",
        "employees",
        "company",
    }
    return [word for word in words if word not in stop]


def answer_is_supported(answer: str, context_texts: List[str], min_overlap: float = 0.18) -> bool:
    context = normalize_whitespace(" ".join(context_texts)).lower()
    if not context:
        return False

    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", answer) if segment.strip()]
    if not sentences:
        return False

    supported = 0
    for sentence in sentences:
        keywords = extract_sentence_keywords(sentence)
        if not keywords:
            supported += 1
            continue
        overlap = sum(1 for keyword in keywords if keyword in context) / len(keywords)
        if overlap >= min_overlap:
            supported += 1

    return supported / len(sentences) >= 0.8
