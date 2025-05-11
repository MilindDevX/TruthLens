#!/usr/bin/env python3
"""
TruthLens Load Simulation — Phase 3

Simulates production-like traffic and measures:
- Average response time
- 95th percentile latency
- Error rate
- Throughput

Tests:
1. 50 concurrent text analysis requests
2. 20 concurrent login requests
3. Rapid sequential refresh token flow (20 iterations)

Usage:
    python tests/test_load.py [BASE_URL]
    Default BASE_URL: http://localhost:8000/api/v1
"""

import asyncio
import time
import statistics
import sys
import os

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1"

# ─── Helpers ───

def p95(values: list[float]) -> float:
    """95th percentile."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(len(sorted_v) * 0.95)
    return sorted_v[min(idx, len(sorted_v) - 1)]


def report(name: str, timings: list[float], errors: int, total: int):
    """Print a formatted report section."""
    if not timings:
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"  ALL {total} REQUESTS FAILED")
        print(f"{'='*60}")
        return

    avg = statistics.mean(timings) * 1000
    p95_val = p95(timings) * 1000
    max_val = max(timings) * 1000
    min_val = min(timings) * 1000
    success = total - errors
    throughput = success / sum(timings) if sum(timings) > 0 else 0

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Total requests    : {total}")
    print(f"  Successful        : {success}")
    print(f"  Failed            : {errors}")
    print(f"  Error rate        : {errors/total*100:.1f}%")
    print(f"  Avg response time : {avg:.1f} ms")
    print(f"  P95 latency       : {p95_val:.1f} ms")
    print(f"  Min / Max         : {min_val:.1f} ms / {max_val:.1f} ms")
    print(f"  Throughput        : {throughput:.1f} req/s")


# ─── Test 1: 50 Concurrent Analysis Requests ───

async def run_analysis_load(client: httpx.AsyncClient, token: str, idx: int):
    """Single analysis request."""
    text = (
        f"Test article {idx}: Scientists claim a breakthrough in renewable energy. "
        f"The study, published in Nature, shows a {idx*3}% improvement in solar cell efficiency. "
        f"However, critics argue the sample size of {idx*10} participants is too small. "
        f"Funding came from an anonymous donor with ties to the fossil fuel industry."
    )
    headers = {"Authorization": f"Bearer {token}"}
    start = time.perf_counter()
    try:
        resp = await client.post(
            f"{BASE_URL}/analyze/text",
            json={"text": text},
            headers=headers,
            timeout=60.0,
        )
        elapsed = time.perf_counter() - start
        return elapsed, resp.status_code < 400
    except Exception as e:
        elapsed = time.perf_counter() - start
        return elapsed, False


async def test_concurrent_analysis(client: httpx.AsyncClient, token: str):
    """50 concurrent text analysis requests."""
    N = 50
    tasks = [run_analysis_load(client, token, i) for i in range(N)]
    results = await asyncio.gather(*tasks)

    timings = [r[0] for r in results if r[1]]
    errors = sum(1 for r in results if not r[1])
    report("50 Concurrent Analysis Requests", timings, errors, N)
    return timings, errors


# ─── Test 2: 20 Concurrent Login Requests ───

async def run_login(client: httpx.AsyncClient, email: str, password: str):
    """Single login request."""
    start = time.perf_counter()
    try:
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=30.0,
        )
        elapsed = time.perf_counter() - start
        return elapsed, resp.status_code < 400
    except Exception:
        elapsed = time.perf_counter() - start
        return elapsed, False


async def test_concurrent_login(client: httpx.AsyncClient, email: str, password: str):
    """20 concurrent login requests with the same user."""
    N = 20
    tasks = [run_login(client, email, password) for _ in range(N)]
    results = await asyncio.gather(*tasks)

    timings = [r[0] for r in results if r[1]]
    errors = sum(1 for r in results if not r[1])
    report("20 Concurrent Login Requests", timings, errors, N)
    return timings, errors


# ─── Test 3: Rapid Refresh Token Flow ───

async def test_rapid_refresh(client: httpx.AsyncClient, refresh_token: str):
    """20 sequential rapid refresh token rotations."""
    N = 20
    timings = []
    errors = 0
    current_refresh = refresh_token

    for i in range(N):
        start = time.perf_counter()
        try:
            resp = await client.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": current_refresh},
                timeout=10.0,
            )
            elapsed = time.perf_counter() - start
            if resp.status_code < 400:
                data = resp.json()
                current_refresh = data.get("refresh_token", current_refresh)
                timings.append(elapsed)
            else:
                errors += 1
                # After first error, remaining will also fail (revoked chain)
                break
        except Exception:
            elapsed = time.perf_counter() - start
            errors += 1
            break

    report("20 Rapid Sequential Refresh Rotations", timings, errors, N)
    return timings, errors


# ─── Main ───

async def main():
    print(f"\n{'#'*60}")
    print(f"  TruthLens Load Simulation")
    print(f"  Target: {BASE_URL}")
    print(f"{'#'*60}")

    async with httpx.AsyncClient() as client:
        # 1. Verify backend is healthy
        try:
            health = await client.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5.0)
            print(f"\n  Backend health: {health.json().get('status', 'unknown')}")
        except Exception as e:
            print(f"\n  ❌ Backend unreachable: {e}")
            print("  Make sure the backend is running on the target URL.")
            sys.exit(1)

        # 2. Register a test user
        import uuid
        test_id = uuid.uuid4().hex[:8]
        email = f"loadtest_{test_id}@truthlens.dev"
        password = "LoadTest123!"

        print(f"\n  Registering test user: {email}")
        reg = await client.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": "Load Tester"},
            timeout=10.0,
        )
        if reg.status_code >= 400:
            print(f"  ❌ Registration failed: {reg.status_code} {reg.text}")
            sys.exit(1)

        reg_data = reg.json()
        access_token = reg_data.get("access_token")
        refresh_token_val = reg_data.get("refresh_token")

        if not access_token:
            print(f"  ❌ No access token in response: {reg_data}")
            sys.exit(1)

        print(f"  ✓ Registered + got tokens")

        # 3. Run load tests
        total_start = time.perf_counter()

        a_timings, a_errors = await test_concurrent_analysis(client, access_token)
        l_timings, l_errors = await test_concurrent_login(client, email, password)
        r_timings, r_errors = await test_rapid_refresh(client, refresh_token_val)

        total_elapsed = time.perf_counter() - total_start

        # 4. Summary
        all_timings = a_timings + l_timings + r_timings
        all_errors = a_errors + l_errors + r_errors
        total_requests = 50 + 20 + 20

        print(f"\n{'='*60}")
        print(f"  OVERALL SUMMARY")
        print(f"{'='*60}")
        print(f"  Total requests     : {total_requests}")
        print(f"  Total errors       : {all_errors}")
        print(f"  Total wall time    : {total_elapsed*1000:.0f} ms")
        print(f"  Overall error rate : {all_errors/total_requests*100:.1f}%")
        if all_timings:
            print(f"  Overall avg latency: {statistics.mean(all_timings)*1000:.1f} ms")
            print(f"  Overall P95 latency: {p95(all_timings)*1000:.1f} ms")
        print(f"{'='*60}")

        # 5. Bottleneck analysis
        print(f"\n  Bottleneck Analysis:")
        if a_timings and statistics.mean(a_timings) > 1.0:
            print(f"  ⚠ Analysis avg > 1s — ML inference is the bottleneck")
        elif a_timings and p95(a_timings) > 2.0:
            print(f"  ⚠ Analysis P95 > 2s — high variance in inference time")
        else:
            print(f"  ✓ Analysis latency acceptable")

        if l_timings and statistics.mean(l_timings) > 0.5:
            print(f"  ⚠ Login avg > 500ms — bcrypt is expensive (expected)")
        else:
            print(f"  ✓ Login latency acceptable")

        if r_errors > 2:
            print(f"  ⚠ Refresh chain broken — possible reuse detection interference")
        else:
            print(f"  ✓ Refresh token chain stable")

        if all_errors / total_requests > 0.05:
            print(f"  ⚠ Error rate > 5% — investigate failures")
        else:
            print(f"  ✓ Error rate acceptable (<5%)")

        print()


if __name__ == "__main__":
    asyncio.run(main())
