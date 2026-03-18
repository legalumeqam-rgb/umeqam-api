import re


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _word_overlap(a: str, b: str) -> float:
    wa = set(_normalize(a).split())
    wb = set(_normalize(b).split())
    if not wa and not wb:
        return 1.0
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _avg_overlap(answers: dict) -> float:
    vals = [v for v in answers.values() if not v.startswith("[")]
    if len(vals) < 2:
        return 0.0
    scores = []
    for i in range(len(vals)):
        for j in range(i+1, len(vals)):
            scores.append(_word_overlap(vals[i], vals[j]))
    return sum(scores) / len(scores)


HEDGE_WORDS = [
    "maybe", "perhaps", "possibly", "might", "unclear", "uncertain",
    "not sure", "i think", "i believe", "probably", "could be",
    "can't predict", "cannot predict", "hard to say", "difficult to say",
    "speculative", "speculation", "inherently uncertain", "no way to know",
    "impossible to predict", "highly uncertain", "with confidence",
    "i cannot", "i can't", "it's unclear", "it is unclear",
    "возможно", "наверное", "вероятно", "не уверен", "может быть",
    "скорее всего", "думаю", "полагаю", "трудно сказать", "сложно сказать",
]

AUTHORITY_PATTERNS = [
    "everyone knows", "it is known", "obviously", "clearly", "of course",
    "все знают", "очевидно", "известно", "конечно", "разумеется",
]

RECENCY_PATTERNS = [
    "recently", "just", "latest", "current", "now", "as of",
    "as of my last", "last update", "knowledge cutoff", "my knowledge",
    "недавно", "только что", "последний", "новый", "сейчас", "текущий",
]

CUTOFF_PATTERNS = [
    "as of my last", "my knowledge cutoff", "last update", "last knowledge",
    "as of october", "as of 2023", "as of 2024", "may be outdated",
    "verify with", "check a reliable", "more recent information",
]


class FactualJudge:
    def evaluate(self, question, answers):
        alarms = []
        vals = [v for v in answers.values() if not v.startswith("[")]
        if len(vals) < 2:
            return {"judge": "FactualJudge", "alarms": ["insufficient_models"], "similarity": 0.0}

        similarity = _avg_overlap(answers)
        if similarity > 0.85:
            alarms.append(f"semantic_agreement (similarity={similarity:.2f})")

        # Check negation contradiction across any pair
        negations = [bool(re.search(r"\bnot\b|\bno\b|\bне\b|\bнет\b", v, re.I)) for v in vals]
        if len(set(negations)) > 1:
            alarms.append("self_contradiction")

        return {"judge": "FactualJudge", "alarms": alarms, "similarity": round(similarity, 3)}


class LogicalJudge:
    def evaluate(self, question, answers):
        alarms = []
        similarity = _avg_overlap(answers)

        if similarity < 0.15:
            alarms.append(f"strong_logical_divergence (similarity={similarity:.2f})")
        elif similarity < 0.35:
            alarms.append(f"mild_logical_divergence (similarity={similarity:.2f})")

        return {"judge": "LogicalJudge", "alarms": alarms}


class AnthropologicalJudge:
    def evaluate(self, question, answers):
        alarms = []
        text = " ".join(answers.values()).lower()
        question_text = question.lower()

        for pattern in AUTHORITY_PATTERNS:
            if pattern in text or pattern in question_text:
                alarms.append(f"authority_bias ({pattern!r})")
                break

        for pattern in RECENCY_PATTERNS:
            if pattern in text:
                alarms.append(f"recency_bias ({pattern!r})")
                break

        hedge_hits = [w for w in HEDGE_WORDS if w in text]
        if hedge_hits:
            alarms.append(f"hedging ({', '.join(hedge_hits[:3])})")

        cutoff_hits = [p for p in CUTOFF_PATTERNS if p in text]
        if cutoff_hits:
            alarms.append(f"cutoff_detected ({cutoff_hits[0]!r})")

        return {"judge": "AnthropologicalJudge", "alarms": alarms}


class AlienJudge:
    def evaluate(self, question, answers):
        alarms = []
        vals = [v for v in answers.values() if not v.startswith("[")]
        if not vals:
            return {"judge": "AlienJudge", "alarms": []}

        lengths = [len(v) for v in vals]
        diff = max(lengths) - min(lengths)

        if diff > 300:
            alarms.append(f"length_anomaly (diff={diff})")
        elif diff > 150:
            alarms.append(f"mild_length_anomaly (diff={diff})")

        if len(question) > 40 and all(l < 20 for l in lengths):
            alarms.append("all_answers_too_short")

        return {"judge": "AlienJudge", "alarms": alarms}


class FalseConsensusJudge:
    """
    Порог снижен до 0.5 — ловим false consensus даже при умеренном сходстве.
    Особый режим для outdated knowledge: cutoff + similarity > 0.4.
    """
    def evaluate(self, question, answers):
        alarms = []
        similarity = _avg_overlap(answers)
        text = " ".join(answers.values()).lower()

        hedge_hits = [w for w in HEDGE_WORDS if w in text]
        cutoff_hits = [p for p in CUTOFF_PATTERNS if p in text]
        both_short = all(len(v) < 30 for v in answers.values())

        if cutoff_hits and similarity > 0.4:
            alarms.append(f"FALSE_CONSENSUS_OUTDATED (sim={similarity:.2f}, cutoff={cutoff_hits[0]!r})")
        elif similarity > 0.5:
            if hedge_hits:
                alarms.append(f"false_consensus_uncertain (sim={similarity:.2f}, hedges={hedge_hits[:2]})")
            elif both_short:
                alarms.append(f"false_consensus_short (sim={similarity:.2f})")
            else:
                alarms.append(f"possible_false_consensus (sim={similarity:.2f})")

        return {"judge": "FalseConsensusJudge", "alarms": alarms, "similarity": round(similarity, 3)}


class JudgeCouncil:
    def __init__(self):
        self.judges = [
            FactualJudge(),
            LogicalJudge(),
            AnthropologicalJudge(),
            AlienJudge(),
            FalseConsensusJudge(),
        ]

    def evaluate(self, question, answers):
        return [j.evaluate(question, answers) for j in self.judges]
