"""
Groq + OpenRouter + Kotlin compiler MCP server (FastMCP).

Tools:
  ask_groq, ask_openrouter, ask_auto (Groq -> OpenRouter fallback),
  list_models, kotlin_check (kotlinc se compile/run)

Auth: Claude ke custom connector me header/token dalne ki jagah nahi hai,
isliye secret token URL me rehta hai:  https://HOST/s/<MCP_SECRET>/mcp
"""

import asyncio
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows console par Hindi/emoji print crash na kare
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def _load_env(path: Path) -> None:
    """Simple .env loader (extra package ki zaroorat nahi)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v:
            os.environ.setdefault(k.strip(), v)


_load_env(Path(__file__).with_name(".env"))

import httpx  # noqa: E402
import uvicorn  # noqa: E402
from fastmcp import FastMCP  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

MCP_SECRET = os.getenv("MCP_SECRET", "").strip()
if len(MCP_SECRET) < 16:
    MCP_SECRET = secrets.token_urlsafe(24)
    print(f"[WARN] MCP_SECRET set nahi hai. Temporary token: {MCP_SECRET}")
MCP_PATH = f"/s/{MCP_SECRET}/mcp"

PROVIDERS = {
    "groq": {
        "base": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile"),
    },
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": os.getenv(
            "OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
        ),
    },
}

MAX_KOTLIN_CHARS = 50_000
KOTLINC_TIMEOUT = int(os.getenv("KOTLINC_TIMEOUT", "180"))
RUN_TIMEOUT = int(os.getenv("KOTLIN_RUN_TIMEOUT", "20"))
_kotlin_lock = asyncio.Semaphore(1)

mcp = FastMCP("groq-openrouter-kotlin")


# ----------------------------------------------------------------------------
# LLM helpers
# ----------------------------------------------------------------------------
async def _chat(
    provider: str,
    prompt: str,
    model: str | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> str:
    cfg = PROVIDERS[provider]
    key = os.getenv(cfg["key_env"], "").strip()
    if not key:
        raise ValueError(f"{cfg['key_env']} set nahi hai ({provider} available nahi).")

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERER", "https://localhost")
        headers["X-Title"] = "groq-openrouter-kotlin-mcp"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model or cfg["default_model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(f"{cfg['base']}/chat/completions", headers=headers, json=body)

    if r.status_code != 200:
        raise RuntimeError(f"{provider} error {r.status_code}: {r.text[:500]}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        raise RuntimeError(f"{provider} se ajeeb jawab mila: {str(data)[:500]}")


@mcp.tool()
async def ask_groq(
    prompt: str,
    model: str = "",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """Groq ke model (jaise llama-3.3-70b-versatile) se jawab lo. model khali ho to default."""
    return await _chat("groq", prompt, model or None, system or None, temperature, max_tokens)


@mcp.tool()
async def ask_openrouter(
    prompt: str,
    model: str = "",
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """OpenRouter ke kisi bhi model (jaise 'deepseek/deepseek-chat') se jawab lo."""
    return await _chat(
        "openrouter", prompt, model or None, system or None, temperature, max_tokens
    )


@mcp.tool()
async def ask_auto(
    prompt: str,
    system: str = "",
    temperature: float = 0.3,
    max_tokens: int = 2048,
    prefer: str = "groq",
) -> dict:
    """Pehle prefer wala provider ('groq' ya 'openrouter'); fail/limit par doosre par fallback."""
    order = ["groq", "openrouter"] if prefer != "openrouter" else ["openrouter", "groq"]
    errors = {}
    for provider in order:
        try:
            text = await _chat(provider, prompt, None, system or None, temperature, max_tokens)
            return {"provider": provider, "answer": text, "errors": errors}
        except Exception as e:  # noqa: BLE001
            errors[provider] = str(e)
    return {"provider": None, "answer": "", "errors": errors}


@mcp.tool()
async def list_models(provider: str = "groq", limit: int = 50) -> list[str]:
    """Provider ('groq' ya 'openrouter') ke model IDs ki list."""
    if provider not in PROVIDERS:
        raise ValueError("provider 'groq' ya 'openrouter' hona chahiye")
    cfg = PROVIDERS[provider]
    key = os.getenv(cfg["key_env"], "").strip()
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{cfg['base']}/models", headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"{provider} error {r.status_code}: {r.text[:300]}")
    ids = sorted(m["id"] for m in r.json().get("data", []))
    return ids[:limit]


# ----------------------------------------------------------------------------
# Kotlin compiler tool (Windows/Linux dono par chalta hai)
# ----------------------------------------------------------------------------
def _run_sync(cmd: list[str], cwd: str, timeout: int) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout: {timeout} second me poora nahi hua"


async def _run(cmd: list[str], cwd: str, timeout: int) -> tuple[int, str, str]:
    return await asyncio.to_thread(_run_sync, cmd, cwd, timeout)


@mcp.tool()
async def kotlin_check(code: str, run: bool = False) -> dict:
    """Kotlin code ko kotlinc se compile karke syntax/type errors dikhata hai.
    run=True ho to main() bhi chala kar output deta hai (20 second limit)."""
    kotlinc = shutil.which("kotlinc")
    if not kotlinc:
        return {
            "ok": False,
            "error": "kotlinc is machine par install nahi hai. JDK 17 + kotlinc install karke PATH me jodo.",
        }
    if len(code) > MAX_KOTLIN_CHARS:
        return {"ok": False, "error": f"Code bahut bada hai (limit {MAX_KOTLIN_CHARS} characters)."}

    async with _kotlin_lock:
        work = tempfile.mkdtemp(prefix="kt_")
        try:
            src = Path(work) / "Main.kt"
            src.write_text(code, encoding="utf-8")
            jar = str(Path(work) / "out.jar")

            rc, out, err = await _run(
                [kotlinc, str(src), "-include-runtime", "-d", jar], work, KOTLINC_TIMEOUT
            )
            result = {"ok": rc == 0, "compiler_output": (out + err).strip()}

            if rc == 0 and run:
                java = shutil.which("java") or "java"
                rrc, rout, rerr = await _run([java, "-jar", jar], work, RUN_TIMEOUT)
                result["run"] = {"exit_code": rrc, "stdout": rout[-4000:], "stderr": rerr[-4000:]}
            return result
        finally:
            shutil.rmtree(work, ignore_errors=True)


# ----------------------------------------------------------------------------
# Health + app
# ----------------------------------------------------------------------------
@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "kotlinc": bool(shutil.which("kotlinc")),
        }
    )


# json_response=True: tunnel/proxy ke peeche SSE ki dikkat nahi aati
app = mcp.http_app(path=MCP_PATH, stateless_http=True, json_response=True)

if __name__ == "__main__":
    print("=" * 60)
    print("Server chal raha hai:  http://localhost:%d" % PORT)
    print("Health check        :  http://localhost:%d/health" % PORT)
    print("Connector path      :  %s" % MCP_PATH)
    print("Final Claude URL    :  <tunnel-ya-render-URL>%s" % MCP_PATH)
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT)
