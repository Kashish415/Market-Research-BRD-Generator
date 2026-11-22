import httpx

def _base_url(value: str) -> str:
    return value.strip().rstrip("/")

def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
    }

def _response_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        message = body.get("detail") or body.get("message") or body.get("error")
        if message:
            return f"AMP request failed ({response.status_code}): {message}"

    return f"AMP request failed ({response.status_code})."

# Start an AMP execution
async def start_execution(
    client: httpx.AsyncClient,
    api_url: str,
    bearer_token: str,
    inputs: dict[str, str],
) -> str:
    response = await client.post(
        f"{_base_url(api_url)}/kickoff",
        headers=_headers(bearer_token),
        json={"inputs": inputs},
    )

    if response.is_error:
        raise RuntimeError(_response_error(response))

    body = response.json()
    kickoff_id = body.get("kickoff_id")
    if not isinstance(kickoff_id, str) or not kickoff_id:
        raise RuntimeError("AMP kickoff response did not include a kickoff_id.")

    return kickoff_id

# Extract the final BRD Content
# checks 4 different response format
def extract_brd_text(status: dict) -> str:
    result_json = status.get("result_json")
    if isinstance(result_json, str) and result_json.strip():
        return result_json.strip()

    if isinstance(result_json, dict):
        output = result_json.get("output")
        if isinstance(output, str) and output.strip():
            return output.strip()

    result = status.get("result")
    if isinstance(result, str) and result.strip():
        return result.strip()

    if isinstance(result, dict):
        output = result.get("output")
        if isinstance(output, str) and output.strip():
            return output.strip()

    raise RuntimeError("AMP completed the execution without returning BRD text.")

async def get_status(
    client: httpx.AsyncClient,
    api_url: str,
    bearer_token: str,
    kickoff_id: str,
) -> dict:
    response = await client.get(
        f"{_base_url(api_url)}/status/{kickoff_id}",
        headers=_headers(bearer_token),
    )

    if response.is_error:
        raise RuntimeError(_response_error(response))

    return response.json()

def normalize_execution_status(status: dict) -> str:
    value = status.get("state") or status.get("status")
    if not isinstance(value, str):
        return ""

    value = value.strip().lower()

    if value in {"pending", "started", "running"}:
        return "running"
    if value in {"success", "completed"}:
        return "completed"
    if value in {"failed", "error", "revoked"}:
        return "failed"
    if value == "paused":
        return "paused"

    return ""

def progress_summary(status: dict) -> str:
    progress = status.get("progress")
    if not isinstance(progress, dict):
        current_task = status.get("current_task")
        return current_task if isinstance(current_task, str) and current_task else ""

    completed = progress.get("completed_tasks")
    if completed is None:
        completed = progress.get("completed")

    total = progress.get("total_tasks")
    if total is None:
        total = progress.get("total")

    current = progress.get("current_task") or progress.get("current")

    if isinstance(completed, int) and isinstance(total, int):
        summary = f"{completed}/{total} tasks"
        if isinstance(current, str) and current:
            return f"{summary} | {current}"
        return summary

    if isinstance(current, str) and current:
        return current

    return ""
