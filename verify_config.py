#!/usr/bin/env python3
"""
Simple configuration verification script
Checks timeout settings without requiring all dependencies
"""

import re


def check_file_content(filename, checks):
    """Check if file contains expected patterns"""
    print(f"\n{'='*70}")
    print(f"Checking: {filename}")
    print('='*70)
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        all_passed = True
        for pattern, description in checks:
            if re.search(pattern, content):
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description} - NOT FOUND!")
                all_passed = False
        
        return all_passed
    except FileNotFoundError:
        print(f"  ✗ File not found: {filename}")
        return False


def main():
    print("\n" + "="*70)
    print("LONG-RUNNING SESSION CONFIGURATION VERIFICATION")
    print("="*70)
    
    all_tests_passed = True
    
    # Check gunicorn_conf.py
    gunicorn_checks = [
        (r'timeout\s*=\s*7200', 'Timeout set to 7200s (120 minutes)'),
        (r'keepalive\s*=\s*300', 'Keepalive set to 300s (5 minutes)'),
    ]
    all_tests_passed &= check_file_content('gunicorn_conf.py', gunicorn_checks)
    
    # Check uvicorn_worker.py
    uvicorn_checks = [
        (r'"ws_ping_interval":\s*30', 'WebSocket ping interval: 30s'),
        (r'"ws_ping_timeout":\s*300', 'WebSocket ping timeout: 300s'),
        (r'"timeout_keep_alive":\s*300', 'Timeout keep-alive: 300s'),
    ]
    all_tests_passed &= check_file_content('uvicorn_worker.py', uvicorn_checks)
    
    # Check main.py
    main_checks = [
        (r'HEARTBEAT_INTERVAL_SECONDS\s*=\s*30', 'Heartbeat interval: 30s'),
        (r'HEARTBEAT_TIMEOUT_SECONDS\s*=\s*300', 'Heartbeat timeout: 300s'),
        (r'SESSION_CLEANUP_INTERVAL_SECONDS\s*=\s*600', 'Session cleanup: 600s'),
        (r'SessionManager\(idle_ttl_seconds=7200\)', 'Session TTL: 7200s'),
        (r'ws_ping_interval=30', 'Uvicorn ping interval: 30s'),
        (r'ws_ping_timeout=300', 'Uvicorn ping timeout: 300s'),
        (r'timeout_keep_alive=300', 'Uvicorn keep-alive: 300s'),
    ]
    all_tests_passed &= check_file_content('main.py', main_checks)
    
    # Check nginx-terminal.conf
    nginx_checks = [
        (r'proxy_read_timeout\s+7200', 'Proxy read timeout: 7200s'),
        (r'proxy_send_timeout\s+7200', 'Proxy send timeout: 7200s'),
        (r'proxy_connect_timeout\s+300', 'Proxy connect timeout: 300s'),
        (r'proxy_buffering\s+off', 'Proxy buffering: off'),
        (r'proxy_http_version\s+1\.1', 'HTTP version: 1.1'),
        (r'proxy_set_header\s+Upgrade', 'Upgrade header set'),
        (r'proxy_set_header\s+Connection\s+"upgrade"', 'Connection upgrade set'),
    ]
    all_tests_passed &= check_file_content('nginx-terminal.conf', nginx_checks)
    
    # Check session_manager.py
    session_checks = [
        (r'idle_ttl_seconds:\s*int\s*=\s*7200', 'Default session TTL: 7200s'),
    ]
    all_tests_passed &= check_file_content('session_manager.py', session_checks)
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if all_tests_passed:
        print("\n✅ ALL CONFIGURATION CHECKS PASSED!")
        print("\n📊 Configuration Summary:")
        print("  • Gunicorn timeout: 7200s (120 minutes)")
        print("  • Gunicorn keepalive: 300s (5 minutes)")
        print("  • WebSocket ping interval: 30s")
        print("  • WebSocket ping timeout: 300s (5 minutes)")
        print("  • Session idle TTL: 7200s (120 minutes)")
        print("  • Nginx proxy timeouts: 7200s (120 minutes)")
        print("  • Session cleanup interval: 600s (10 minutes)")
        
        print("\n✅ Benefits:")
        print("  • Sessions stay alive for 120 minutes")
        print("  • Automatic heartbeat every 30 seconds")
        print("  • No disconnection during long tests")
        print("  • Graceful timeout handling")
        
        print("\n🚀 Ready for production deployment!")
        print("="*70 + "\n")
        return 0
    else:
        print("\n❌ SOME CONFIGURATION CHECKS FAILED!")
        print("Please review the errors above and fix the configuration files.")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    exit(main())
