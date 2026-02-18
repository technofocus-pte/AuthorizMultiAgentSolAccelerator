"""Shared JSON response parser for agent outputs."""

import json
import logging
import re

logger = logging.getLogger(__name__)


def parse_json_response(response) -> dict:
    """Extract JSON from an agent response, with fallback.

    The agent response may contain interleaved tool-call results and
    explanatory text before / after the final JSON object.  This parser
    tries multiple strategies in order of reliability:

    1. JSON inside a markdown code fence (```json ... ``` or ``` ... ```)
    2. Brace-matched extraction working **backwards** from the last ``}``
       — this finds the outermost JSON object that ends at the very end
       of the response, which is almost always the final answer.
    3. Legacy first-``{`` to last-``}`` substring (original approach).

    Each strategy also tries a JSON cleanup pass (trailing commas,
    single-line comments) if the initial parse fails.

    Returns parsed dict on success, or an error dict on failure.
    """
    # --- Diagnostic logging ---
    logger.info(
        "[parse] response type=%s, has .text=%s",
        type(response).__name__,
        hasattr(response, "text"),
    )

    try:
        text = response.text if hasattr(response, "text") else str(response)
    except Exception:
        text = str(response)

    text_len = len(text) if text else 0
    logger.info("[parse] text length=%d", text_len)
    if text and text_len > 0:
        logger.info("[parse] first 300 chars: %s", text[:300])
        if text_len > 300:
            logger.info("[parse] last 300 chars: %s", text[-300:])

    if not text or not text.strip():
        logger.error("[parse] Agent returned empty response")
        return {"error": "Agent returned empty response", "raw": ""}

    # --- Strategy 1: markdown code fence ---
    # Match the LAST fenced JSON block (most likely the final answer)
    # Two patterns: strict (with newlines) and relaxed (without)
    fence_patterns = [
        re.compile(r"```(?:json)?\s*\n(\{.*?\})\s*\n```", re.DOTALL),
        re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL),
    ]
    for pat_idx, fence_pattern in enumerate(fence_patterns):
        fences = fence_pattern.findall(text)
        if fences:
            logger.info("[parse] Strategy 1 (fence pattern %d): found %d fences", pat_idx, len(fences))

            # If multiple fences found, try to merge all valid JSON dicts.
            # Agents often split output across multiple ```json blocks
            # (e.g., code_validation, clinical_extraction, procedure_assessment).
            # Merging gives a complete result instead of just the last block.
            if len(fences) > 1:
                merged = {}
                merge_count = 0
                for candidate in fences:
                    parsed = _try_parse(candidate)
                    if parsed is None:
                        parsed = _try_parse(_cleanup_json(candidate))
                    if parsed is not None:
                        merged.update(parsed)
                        merge_count += 1
                if merged and merge_count > 1:
                    logger.info("[parse] Strategy 1: merged %d/%d fence blocks into %d keys",
                                merge_count, len(fences), len(merged))
                    return merged

            # Single fence or merge didn't work — fall back to last-fence
            for idx, candidate in enumerate(reversed(fences)):
                parsed = _try_parse(candidate)
                if parsed is not None:
                    logger.info("[parse] Strategy 1 succeeded (pattern %d, fence #%d from end)", pat_idx, idx)
                    return parsed
                # Try with cleanup
                parsed = _try_parse(_cleanup_json(candidate))
                if parsed is not None:
                    logger.info("[parse] Strategy 1 succeeded after cleanup (pattern %d, fence #%d from end)", pat_idx, idx)
                    return parsed
                logger.info("[parse] Strategy 1 fence #%d from end failed to parse (%d chars)", idx, len(candidate))

    logger.info("[parse] Strategy 1: no fences found or none parsed")

    # --- Strategy 2: brace-matched, working backward from last ``}`` ---
    parsed = _extract_last_json_object(text)
    if parsed is not None:
        logger.info("[parse] Strategy 2 (brace-match backward) succeeded")
        return parsed
    logger.info("[parse] Strategy 2 (brace-match backward) failed")

    # --- Strategy 3: legacy first-{ to last-} (fallback) ---
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        candidate = text[json_start:json_end]
        logger.info("[parse] Strategy 3: trying text[%d:%d] (%d chars)", json_start, json_end, len(candidate))
        parsed = _try_parse(candidate)
        if parsed is not None:
            logger.info("[parse] Strategy 3 (legacy first-to-last brace) succeeded")
            return parsed
        # Try with cleanup
        parsed = _try_parse(_cleanup_json(candidate))
        if parsed is not None:
            logger.info("[parse] Strategy 3 succeeded after cleanup")
            return parsed
        logger.info("[parse] Strategy 3 failed to parse")
    else:
        logger.info("[parse] Strategy 3: no braces found (start=%d, end=%d)", json_start, json_end - 1)

    # --- All strategies failed ---
    snippet = text[:500] + ("..." if len(text) > 500 else "")
    logger.error("Could not parse agent response as JSON. Full length=%d. Snippet: %s", text_len, snippet)
    return {
        "error": "Could not parse agent response as JSON",
        "raw": snippet,
        "text_length": text_len,
    }


def _cleanup_json(text: str) -> str:
    """Attempt to fix common JSON issues produced by LLM agents.

    Handles:
    - Trailing commas before } or ]
    - Single-line comments (// ...)
    - Unquoted NaN/Infinity values
    """
    # Remove single-line comments (but not inside strings — best effort)
    cleaned = re.sub(r'(?<!["\w])//[^\n]*', '', text)
    # Remove trailing commas before } or ]
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return cleaned


def _try_parse(text: str) -> dict | None:
    """Attempt to parse *text* as JSON.  Returns dict or None."""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
        logger.info("[parse] _try_parse: parsed OK but not a dict (type=%s)", type(obj).__name__)
    except json.JSONDecodeError as e:
        logger.debug("[parse] _try_parse: JSONDecodeError at pos %d: %s", e.pos, e.msg)
    except (ValueError, TypeError) as e:
        logger.debug("[parse] _try_parse: %s: %s", type(e).__name__, e)
    return None


def _extract_last_json_object(text: str) -> dict | None:
    """Find the last complete top-level JSON object in *text*.

    Walks backward from the final ``}`` and counts braces to locate
    the matching ``{``.  Handles nested objects, strings (including
    escaped quotes), and ignores braces inside string literals.
    """
    end = text.rfind("}")
    if end == -1:
        return None

    # Walk backward counting braces, respecting string boundaries
    depth = 0
    in_string = False
    i = end
    while i >= 0:
        ch = text[i]

        if in_string:
            if ch == '"':
                # Check if this quote is escaped
                num_backslashes = 0
                j = i - 1
                while j >= 0 and text[j] == "\\":
                    num_backslashes += 1
                    j -= 1
                if num_backslashes % 2 == 0:
                    in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "}":
                depth += 1
            elif ch == "{":
                depth -= 1
                if depth == 0:
                    # Found matching opening brace
                    candidate = text[i : end + 1]
                    parsed = _try_parse(candidate)
                    if parsed is not None:
                        return parsed
                    # Try with cleanup
                    parsed = _try_parse(_cleanup_json(candidate))
                    if parsed is not None:
                        logger.info("[parse] Strategy 2: succeeded after cleanup")
                        return parsed
                    # If parse failed, keep searching backward
                    # for an earlier { that might be the real start
                    depth = 1  # reset — we still haven't closed the }

        i -= 1

    return None
