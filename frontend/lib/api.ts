import type {
  PriorAuthRequest,
  ReviewResponse,
  DecisionRequest,
  DecisionResponse,
  ProgressEvent,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export async function submitReview(
  request: PriorAuthRequest
): Promise<ReviewResponse> {
  const response = await fetch(`${API_BASE}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Review failed (${response.status})`);
  }

  return response.json();
}

/**
 * Submit a prior auth review with real-time SSE progress streaming.
 * Returns an AbortController so the caller can cancel the request.
 */
export function submitReviewStream(
  request: PriorAuthRequest,
  onProgress: (event: ProgressEvent) => void,
  onResult: (result: ReviewResponse) => void,
  onError: (error: string) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/review/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        onError(err.detail || `Review failed (${response.status})`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError("No response stream available");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "progress";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              if (eventType === "result") {
                onResult(parsed as ReviewResponse);
              } else if (eventType === "error") {
                onError(parsed.detail || "Unknown error");
              } else {
                onProgress(parsed as ProgressEvent);
              }
            } catch {
              // Skip malformed JSON lines
            }
            eventType = "progress"; // Reset for next event
          }
          // Skip comment lines (": keepalive") and empty lines
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(err instanceof Error ? err.message : "An error occurred");
      }
    }
  })();

  return controller;
}

export async function submitDecision(
  request: DecisionRequest
): Promise<DecisionResponse> {
  const response = await fetch(`${API_BASE}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Decision failed (${response.status})`);
  }

  return response.json();
}
