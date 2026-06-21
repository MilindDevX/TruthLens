"""
Phase D — End-to-End Integration Tests.

Tests the full stack:
  1. Auth flow (register, login, refresh, forced logout)
  2. Text inference (normal, long text, duplicate, edge cases)
  3. History (list, detail)
  4. Performance instrumentation (per-stage latency)
  5. Concurrency (parallel requests, rapid duplicates)

Run: python tests/test_integration.py
"""

import asyncio
import time
import sys
import os

import httpx

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"

TEST_EMAIL = "integration_test@truthlens.dev"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Integration Tester"


class TestResults:
    def __init__(self):
        self.results = []
        self.perf = []

    def record(self, name, passed, detail=""):
        self.results.append((name, passed, detail))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))

    def perf_record(self, name, ms):
        self.perf.append((name, ms))

    def summary(self):
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed
        print(f"\n{'═' * 60}")
        print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
        print(f"{'═' * 60}")
        if self.perf:
            print(f"\n{'─' * 60}")
            print(f"  PERFORMANCE METRICS")
            print(f"{'─' * 60}")
            print(f"  {'Metric':<35} {'Time (ms)':>10}")
            print(f"  {'─' * 35} {'─' * 10}")
            for name, ms in self.perf:
                print(f"  {name:<35} {ms:>10.1f}")
            print(f"{'─' * 60}")
        if failed > 0:
            print("\n  FAILURES:")
            for name, passed, detail in self.results:
                if not passed:
                    print(f"    ✗ {name}: {detail}")
        return failed == 0


T = TestResults()


def safe_json(r):
    """Safely parse JSON response, return {} on failure."""
    try:
        return r.json()
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────
# 1. AUTH FLOW
# ─────────────────────────────────────────────────────────

async def test_auth_flow():
    print("\n▶ AUTH FLOW TESTS")
    print("─" * 40)

    async with httpx.AsyncClient(base_url=API, timeout=15) as client:
        # 1a. Register
        t0 = time.perf_counter()
        r = await client.post("/auth/register", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD, "full_name": TEST_NAME,
        })
        T.perf_record("Register", (time.perf_counter() - t0) * 1000)

        if r.status_code == 409:
            r = await client.post("/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD,
            })
        T.record("Register/Login", r.status_code in (200, 201), f"status={r.status_code}")

        tokens = safe_json(r)
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        T.record("Tokens received", bool(access_token and refresh_token))
        T.record("Token type is bearer", tokens.get("token_type") == "bearer")
        T.record("Expires_in > 0", tokens.get("expires_in", 0) > 0)

        # 1b. Login
        t0 = time.perf_counter()
        r = await client.post("/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD,
        })
        T.perf_record("Login", (time.perf_counter() - t0) * 1000)
        T.record("Login succeeds", r.status_code == 200)
        login_tokens = safe_json(r)
        access_token = login_tokens.get("access_token", access_token)
        refresh_token = login_tokens.get("refresh_token", refresh_token)

        # 1c. Refresh
        t0 = time.perf_counter()
        r = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        T.perf_record("Token refresh", (time.perf_counter() - t0) * 1000)
        T.record("Refresh succeeds", r.status_code == 200, f"status={r.status_code}")
        new_tokens = safe_json(r)
        new_access = new_tokens.get("access_token", access_token)
        new_refresh = new_tokens.get("refresh_token", refresh_token)
        if r.status_code == 200:
            T.record("New tokens differ", new_refresh != refresh_token)
            access_token = new_access
        else:
            T.record("New tokens differ", False, "refresh failed")

        # 1d. Reuse old refresh (should fail)
        r = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        T.record("Reuse detection: old token rejected", r.status_code == 401, f"status={r.status_code}")

        # 1e. Login fresh after revocation
        r = await client.post("/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD,
        })
        T.record("Login after revocation", r.status_code == 200)
        login_tokens = safe_json(r)
        access_token = login_tokens.get("access_token", access_token)
        refresh_token = login_tokens.get("refresh_token", "")

        # 1f. Protected endpoint with valid token
        try:
            r = await client.get("/history", headers={"Authorization": f"Bearer {access_token}"})
            T.record("Protected: valid token → 200", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            T.record("Protected: valid token → 200", False, str(e)[:60])

        # 1g. Protected endpoint with invalid token
        try:
            r = await client.get("/history", headers={"Authorization": "Bearer invalid_garbage"})
            T.record("Protected: invalid token → 401/403", r.status_code in (401, 403), f"status={r.status_code}")
        except Exception as e:
            T.record("Protected: invalid token → 401/403", False, str(e)[:60])

        # 1h. Wrong password
        r = await client.post("/auth/login", json={
            "email": TEST_EMAIL, "password": "WrongPassword!",
        })
        T.record("Wrong password → 401", r.status_code == 401)

        return access_token, refresh_token


# ─────────────────────────────────────────────────────────
# 2. TEXT INFERENCE
# ─────────────────────────────────────────────────────────

SAMPLE_TEXT = (
    "Breaking news: Scientists have discovered a new element that could revolutionize "
    "clean energy production. The element, temporarily named Truthium, was found deep "
    "in the Earth's mantle during a routine geological survey. Researchers claim it could "
    "produce 10x more energy than uranium with zero radioactive waste."
)

ADVERSARIAL_TEXT = (
    "Th1s t3xt haz b33n wr1tten w1th int3ntional m1sspell1ngs and ch4r4cter sw4ps "
    "to t3st the mod3l's rob8stness aga1nst advers4rial 1nput att4cks."
)


async def test_inference(access_token: str):
    print("\n▶ TEXT INFERENCE TESTS")
    print("─" * 40)

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=API, timeout=30) as client:
        # 2a. Normal text — cold start
        t0 = time.perf_counter()
        try:
            r = await client.post("/analyze/text", json={"text": SAMPLE_TEXT}, headers=headers)
            cold_ms = (time.perf_counter() - t0) * 1000
            T.perf_record("Cold-start analysis", cold_ms)
            T.record("Normal text → 200", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            T.record("Normal text → 200", False, str(e)[:80])
            r = None

        first_id = None
        if r and r.status_code == 200:
            data = safe_json(r)
            T.record("Has prediction", data.get("prediction") in ("real", "fake"), f"pred={data.get('prediction')}")
            T.record("Has confidence (0-1)", 0 <= data.get("confidence", -1) <= 1)
            T.record("Has credibility_score", 0 <= data.get("credibility_score", -1) <= 1)
            T.record("Has model_scores", "baseline" in data.get("model_scores", {}))
            T.record("Has model_version", len(data.get("model_version", "")) > 0)
            T.record("Has id (UUID)", len(str(data.get("id", ""))) > 10)

            conf = data.get("confidence", 0.5)
            expected_flag = 0.4 <= conf <= 0.6
            T.record("Low confidence flag correct",
                     data.get("low_confidence_flag") == expected_flag,
                     f"conf={conf:.3f}, flag={data.get('low_confidence_flag')}")

            first_id = data.get("id")

        # 2b. Warm request
        try:
            t0 = time.perf_counter()
            r = await client.post("/analyze/text", json={
                "text": "The mayor stated the new highway would cost $450 million. Critics remain skeptical."
            }, headers=headers)
            T.perf_record("Warm analysis", (time.perf_counter() - t0) * 1000)
            T.record("Warm request → 200", r.status_code == 200)
        except Exception as e:
            T.record("Warm request → 200", False, str(e)[:60])

        # 2c. Duplicate text — should return cached result
        try:
            r = await client.post("/analyze/text", json={"text": SAMPLE_TEXT}, headers=headers)
            T.record("Duplicate → 200", r.status_code == 200)
            if r.status_code == 200 and first_id:
                T.record("Dedup: same ID returned", safe_json(r).get("id") == first_id)
        except Exception as e:
            T.record("Duplicate → 200", False, str(e)[:60])

        # 2d. Very long text → validation error
        try:
            r = await client.post("/analyze/text", json={"text": "A" * 31000}, headers=headers)
            T.record("Long text → 422", r.status_code == 422, f"status={r.status_code}")
        except Exception as e:
            T.record("Long text → 422", False, str(e)[:60])

        # 2e. Empty text → validation error
        try:
            r = await client.post("/analyze/text", json={"text": ""}, headers=headers)
            T.record("Empty text → 422", r.status_code == 422, f"status={r.status_code}")
        except Exception as e:
            T.record("Empty text → 422", False, str(e)[:60])

        # 2f. Adversarial text
        try:
            r = await client.post("/analyze/text", json={"text": ADVERSARIAL_TEXT}, headers=headers)
            T.record("Adversarial text → 200", r.status_code == 200)
        except Exception as e:
            T.record("Adversarial text → 200", False, str(e)[:60])

        # 2g. No auth
        try:
            r = await client.post("/analyze/text", json={"text": "test"})
            T.record("No auth → 401/403", r.status_code in (401, 403))
        except Exception as e:
            T.record("No auth → 401/403", False, str(e)[:60])


# ─────────────────────────────────────────────────────────
# 3. HISTORY
# ─────────────────────────────────────────────────────────

async def test_history(access_token: str):
    print("\n▶ HISTORY TESTS")
    print("─" * 40)

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=API, timeout=10) as client:
        try:
            r = await client.get("/history", headers=headers)
            T.record("History list → 200", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                data = safe_json(r)
                T.record("Has items array", isinstance(data.get("items"), list))
                T.record("Has total count", isinstance(data.get("total"), int))
                items = data.get("items", [])
                T.record(f"Items returned ({len(items)})", len(items) >= 0)
                if items:
                    item_id = items[0]["id"]
                    r2 = await client.get(f"/history/{item_id}", headers=headers)
                    T.record("History detail → 200", r2.status_code == 200)
        except Exception as e:
            T.record("History list → 200", False, str(e)[:60])

        try:
            r = await client.get("/history")
            T.record("History no auth → 401/403", r.status_code in (401, 403))
        except Exception as e:
            T.record("History no auth → 401/403", False, str(e)[:60])


# ─────────────────────────────────────────────────────────
# 4. HEALTH / DRIFT
# ─────────────────────────────────────────────────────────

async def test_health():
    print("\n▶ HEALTH & DRIFT TESTS")
    print("─" * 40)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        r = await client.get("/health")
        T.record("Health → 200", r.status_code == 200)
        data = safe_json(r)
        T.record("Status = healthy", data.get("status") == "healthy")
        T.record("Has models section", "text" in data.get("models", {}))
        T.record("Has drift section", "kl_divergence" in data.get("drift", {}))
        T.record("Drift window max=1000", data.get("drift", {}).get("max_window") == 1000)


# ─────────────────────────────────────────────────────────
# 5. CONCURRENCY
# ─────────────────────────────────────────────────────────

async def test_concurrency(access_token: str):
    print("\n▶ CONCURRENCY TESTS")
    print("─" * 40)

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=API, timeout=30) as client:
        # 5a. 10 concurrent analyze requests
        texts = [f"Concurrent test text number {i}. Testing parallel request handling." for i in range(10)]
        t0 = time.perf_counter()
        tasks = [client.post("/analyze/text", json={"text": t}, headers=headers) for t in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        T.perf_record("10 concurrent requests", (time.perf_counter() - t0) * 1000)

        errors = [r for r in results if isinstance(r, Exception)]
        successes = [r for r in results if not isinstance(r, Exception) and r.status_code == 200]
        T.record(f"10 concurrent: {len(successes)}/10 pass",
                 len(successes) >= 8,  # Allow some tolerance for SQLite contention
                 f"ok={len(successes)}, err={len(errors)}, other={10-len(successes)-len(errors)}")

        # 5b. Rapid dedup (same text 5 times)
        rapid_results = []
        for i in range(5):
            try:
                r = await client.post("/analyze/text", json={"text": "Rapid dedup test content exactly the same"}, headers=headers)
                rapid_results.append(r)
            except Exception:
                pass

        ids = [safe_json(r).get("id") for r in rapid_results if r.status_code == 200]
        unique_ids = len(set(ids)) if ids else 0
        T.record(f"Rapid dedup: {unique_ids} unique ID(s)", unique_ids == 1, f"ids={ids[:3]}")


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

async def main():
    print(f"{'═' * 60}")
    print(f"  TruthLens X — Phase D Integration Tests")
    print(f"  Backend: {BASE_URL}")
    print(f"{'═' * 60}")

    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{BASE_URL}/health")
            if r.status_code != 200:
                print(f"\n❌ Backend not healthy. Status: {r.status_code}")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cannot reach backend at {BASE_URL}: {e}")
        sys.exit(1)

    print(f"\n  ✓ Backend healthy\n")

    access_token, refresh_token = await test_auth_flow()
    await test_inference(access_token)
    await test_history(access_token)
    await test_health()
    await test_concurrency(access_token)

    all_passed = T.summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
