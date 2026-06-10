CHECK_STATUS_UNDERSTOOD = "UNDERSTOOD"
CHECK_STATUS_REVIEW = "REVIEW"


def normalize_check_payload(payload):
    confidence = int(payload.get("confidence") or 0)
    confidence = min(5, max(1, confidence))
    doubt = (payload.get("doubt") or "").strip()
    summary = (payload.get("summary") or "").strip()
    return {
        "topic_key": (payload.get("topic_key") or "").strip(),
        "topic_title": (payload.get("topic_title") or "").strip(),
        "page_number": int(payload.get("page_number") or 1),
        "confidence": confidence,
        "summary": summary,
        "doubt": doubt,
        "status": check_status(confidence, summary, doubt),
    }


def check_status(confidence, summary, doubt):
    if confidence <= 2 or doubt or len(summary) < 30:
        return CHECK_STATUS_REVIEW
    return CHECK_STATUS_UNDERSTOOD
