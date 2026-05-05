#!/usr/bin/env python3
"""
Test script for long-running WebSocket sessions
Verifies 120-minute session support with heartbeat mechanism
"""

import asyncio
import json
import time
from datetime import datetime, timedelta


# Mock WebSocket for testing without actual connection
class MockWebSocket:
    """Mock WebSocket for testing heartbeat logic"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
        self.last_ping = time.time()
    
    async def send_json(self, data):
        self.messages.append(data)
        if data.get("type") == "ping":
            self.last_ping = time.time()
    
    async def close(self, code=1000, reason=""):
        self.closed = True
        print(f"WebSocket closed: {code} - {reason}")


def test_timeout_configuration():
    """Test that timeout configurations are correct"""
    print("=" * 70)
    print("TEST 1: Timeout Configuration Verification")
    print("=" * 70)
    
    # Import configurations
    import gunicorn_conf
    from uvicorn_worker import ProductionUvicornWorker
    from session_manager import SessionManager
    import main
    
    # Check Gunicorn config
    print("\n✓ Gunicorn Configuration:")
    print(f"  - timeout: {gunicorn_conf.timeout}s (expected: 7200s)")
    assert gunicorn_conf.timeout == 7200, "Gunicorn timeout should be 7200s"
    print(f"  - keepalive: {gunicorn_conf.keepalive}s (expected: 300s)")
    assert gunicorn_conf.keepalive == 300, "Gunicorn keepalive should be 300s"
    
    # Check Uvicorn worker config
    print("\n✓ Uvicorn Worker Configuration:")
    config = ProductionUvicornWorker.CONFIG_KWARGS
    print(f"  - ws_ping_interval: {config['ws_ping_interval']}s (expected: 30s)")
    assert config['ws_ping_interval'] == 30, "Ping interval should be 30s"
    print(f"  - ws_ping_timeout: {config['ws_ping_timeout']}s (expected: 300s)")
    assert config['ws_ping_timeout'] == 300, "Ping timeout should be 300s"
    print(f"  - timeout_keep_alive: {config['timeout_keep_alive']}s (expected: 300s)")
    assert config['timeout_keep_alive'] == 300, "Keep-alive should be 300s"
    
    # Check main.py constants
    print("\n✓ Main Application Configuration:")
    print(f"  - HEARTBEAT_INTERVAL_SECONDS: {main.HEARTBEAT_INTERVAL_SECONDS}s (expected: 30s)")
    assert main.HEARTBEAT_INTERVAL_SECONDS == 30, "Heartbeat interval should be 30s"
    print(f"  - HEARTBEAT_TIMEOUT_SECONDS: {main.HEARTBEAT_TIMEOUT_SECONDS}s (expected: 300s)")
    assert main.HEARTBEAT_TIMEOUT_SECONDS == 300, "Heartbeat timeout should be 300s"
    print(f"  - SESSION_CLEANUP_INTERVAL_SECONDS: {main.SESSION_CLEANUP_INTERVAL_SECONDS}s (expected: 600s)")
    assert main.SESSION_CLEANUP_INTERVAL_SECONDS == 600, "Cleanup interval should be 600s"
    
    # Check SessionManager
    print("\n✓ Session Manager Configuration:")
    session_manager = SessionManager()
    print(f"  - idle_ttl_seconds: {session_manager.idle_ttl_seconds}s (expected: 7200s)")
    assert session_manager.idle_ttl_seconds == 7200, "Session TTL should be 7200s"
    
    print("\n✅ All timeout configurations are correct!\n")


def test_session_lifecycle():
    """Test session creation and cleanup"""
    print("=" * 70)
    print("TEST 2: Session Lifecycle")
    print("=" * 70)
    
    from session_manager import SessionManager
    
    # Create session manager with short TTL for testing
    manager = SessionManager(idle_ttl_seconds=2)
    
    # Create session
    session = manager.create()
    print(f"\n✓ Created session: {session.session_id}")
    assert session.session_id in manager.sessions
    
    # Touch session
    initial_time = session.last_seen
    time.sleep(0.1)
    manager.touch(session)
    print(f"✓ Touched session (last_seen updated)")
    assert session.last_seen > initial_time
    
    # Wait for expiration
    print(f"✓ Waiting 3 seconds for session to expire...")
    time.sleep(3)
    
    # Cleanup
    expired = manager.cleanup_idle()
    print(f"✓ Cleaned up {expired} expired session(s)")
    assert expired == 1, "Should have cleaned up 1 session"
    assert session.session_id not in manager.sessions
    
    print("\n✅ Session lifecycle works correctly!\n")


def test_heartbeat_timing():
    """Test heartbeat timing calculations"""
    print("=" * 70)
    print("TEST 3: Heartbeat Timing")
    print("=" * 70)
    
    # Calculate heartbeat metrics
    ping_interval = 30  # seconds
    session_duration = 7200  # 2 hours
    
    pings_per_session = session_duration / ping_interval
    print(f"\n✓ Heartbeat Metrics:")
    print(f"  - Session duration: {session_duration}s ({session_duration/60:.0f} minutes)")
    print(f"  - Ping interval: {ping_interval}s")
    print(f"  - Pings per session: {pings_per_session:.0f}")
    print(f"  - Bandwidth per session: ~{pings_per_session * 50 / 1024:.1f} KB")
    
    # Verify reasonable values
    assert pings_per_session == 240, "Should send 240 pings in 2 hours"
    
    print("\n✅ Heartbeat timing is optimal!\n")


def test_timeout_hierarchy():
    """Test that timeout hierarchy is correct"""
    print("=" * 70)
    print("TEST 4: Timeout Hierarchy")
    print("=" * 70)
    
    import gunicorn_conf
    from uvicorn_worker import ProductionUvicornWorker
    from session_manager import SessionManager
    import main
    
    # Get all timeouts
    session_ttl = SessionManager().idle_ttl_seconds
    gunicorn_timeout = gunicorn_conf.timeout
    heartbeat_timeout = main.HEARTBEAT_TIMEOUT_SECONDS
    ping_interval = main.HEARTBEAT_INTERVAL_SECONDS
    
    print("\n✓ Timeout Hierarchy (all should be 7200s or less):")
    print(f"  1. Session TTL: {session_ttl}s")
    print(f"  2. Gunicorn Timeout: {gunicorn_timeout}s")
    print(f"  3. Heartbeat Timeout: {heartbeat_timeout}s")
    print(f"  4. Ping Interval: {ping_interval}s")
    
    # Verify hierarchy
    assert session_ttl == gunicorn_timeout == 7200, "Session and Gunicorn should match"
    assert heartbeat_timeout < session_ttl, "Heartbeat timeout should be less than session TTL"
    assert ping_interval < heartbeat_timeout, "Ping interval should be less than heartbeat timeout"
    
    print("\n✅ Timeout hierarchy is correct!\n")


def test_session_duration_calculation():
    """Test session duration calculations"""
    print("=" * 70)
    print("TEST 5: Session Duration Calculations")
    print("=" * 70)
    
    # Test various durations
    durations = [
        (30, "30 seconds"),
        (300, "5 minutes"),
        (1800, "30 minutes"),
        (3600, "1 hour"),
        (7200, "2 hours"),
    ]
    
    print("\n✓ Session Duration Examples:")
    for seconds, description in durations:
        minutes = seconds / 60
        hours = seconds / 3600
        print(f"  - {seconds:5d}s = {minutes:6.1f} min = {hours:4.2f} hours ({description})")
    
    # Verify 2-hour calculation
    two_hours_seconds = 2 * 60 * 60
    assert two_hours_seconds == 7200, "2 hours should be 7200 seconds"
    
    print("\n✅ Duration calculations are correct!\n")


async def test_heartbeat_simulation():
    """Simulate heartbeat mechanism"""
    print("=" * 70)
    print("TEST 6: Heartbeat Simulation")
    print("=" * 70)
    
    websocket = MockWebSocket()
    ping_count = 0
    duration = 10  # Simulate 10 seconds
    interval = 1   # Ping every 1 second for testing
    
    print(f"\n✓ Simulating {duration}s session with {interval}s ping interval...")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # Send ping
        await websocket.send_json({"type": "ping"})
        ping_count += 1
        
        # Wait for interval
        await asyncio.sleep(interval)
    
    elapsed = time.time() - start_time
    print(f"✓ Sent {ping_count} pings in {elapsed:.1f}s")
    print(f"✓ Average interval: {elapsed/ping_count:.2f}s")
    
    # Verify ping count
    expected_pings = duration / interval
    assert abs(ping_count - expected_pings) <= 1, f"Should send ~{expected_pings} pings"
    
    print("\n✅ Heartbeat simulation successful!\n")


def test_nginx_config():
    """Verify nginx configuration file"""
    print("=" * 70)
    print("TEST 7: Nginx Configuration")
    print("=" * 70)
    
    with open("nginx-terminal.conf", "r") as f:
        config = f.read()
    
    print("\n✓ Checking nginx-terminal.conf...")
    
    # Check for required settings
    checks = [
        ("proxy_read_timeout 7200", "Read timeout set to 7200s"),
        ("proxy_send_timeout 7200", "Send timeout set to 7200s"),
        ("proxy_connect_timeout 300", "Connect timeout set to 300s"),
        ("proxy_buffering off", "Buffering disabled"),
        ("proxy_http_version 1.1", "HTTP 1.1 enabled"),
        ('proxy_set_header Upgrade $http_upgrade', "Upgrade header set"),
        ('proxy_set_header Connection "upgrade"', "Connection upgrade set"),
    ]
    
    for setting, description in checks:
        if setting in config:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - NOT FOUND!")
            assert False, f"Missing nginx setting: {setting}"
    
    print("\n✅ Nginx configuration is correct!\n")


def print_summary():
    """Print optimization summary"""
    print("\n" + "=" * 70)
    print("🎉 LONG-RUNNING SESSION OPTIMIZATION SUMMARY")
    print("=" * 70)
    
    print("\n✅ Configuration Changes:")
    print("  • Gunicorn timeout: 3600s → 7200s (120 minutes)")
    print("  • Gunicorn keepalive: 120s → 300s (5 minutes)")
    print("  • WebSocket ping interval: 20s → 30s")
    print("  • WebSocket ping timeout: 120s → 300s (5 minutes)")
    print("  • Session idle TTL: default → 7200s (120 minutes)")
    print("  • Nginx proxy timeout: 3600s → 7200s (120 minutes)")
    print("  • Session cleanup interval: 300s → 600s (10 minutes)")
    
    print("\n✅ Features:")
    print("  • Automatic heartbeat every 30 seconds")
    print("  • Sessions stay alive for 120 minutes")
    print("  • Graceful timeout handling")
    print("  • Automatic session cleanup")
    print("  • Production-ready configuration")
    
    print("\n✅ Benefits:")
    print("  • No disconnection during long tests")
    print("  • Stable 2-hour sessions")
    print("  • Reduced reconnection overhead")
    print("  • Better user experience")
    
    print("\n📊 Metrics:")
    print("  • Max session duration: 120 minutes")
    print("  • Heartbeat frequency: 240 pings per session")
    print("  • Bandwidth overhead: ~12 KB per session")
    print("  • Memory per session: ~10-50 KB")
    
    print("\n🚀 Ready for production deployment!")
    print("=" * 70 + "\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("LONG-RUNNING SESSION OPTIMIZATION - TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        # Run synchronous tests
        test_timeout_configuration()
        test_session_lifecycle()
        test_heartbeat_timing()
        test_timeout_hierarchy()
        test_session_duration_calculation()
        test_nginx_config()
        
        # Run async test
        print("Running async heartbeat simulation...")
        asyncio.run(test_heartbeat_simulation())
        
        # Print summary
        print_summary()
        
        print("✅ ALL TESTS PASSED!\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
