#!/usr/bin/env python3
"""Test script for new terminal features: grep -c, nano, sudo"""

from execution_engine import CommandExecutionEngine
from session_manager import TerminalSession


def test_grep_count():
    """Test grep -c flag"""
    print("=" * 60)
    print("TEST 1: grep -c (count matches)")
    print("=" * 60)
    
    engine = CommandExecutionEngine()
    session = TerminalSession("test-session")
    
    # Create a test file with multiple ERROR lines
    result = engine.execute(session, 'echo "ERROR Disk" > alerts.log')
    print(f"✓ Created alerts.log: {result['status']}")
    
    result = engine.execute(session, 'echo "ERROR Memory" >> alerts.log')
    print(f"✓ Appended to alerts.log: {result['status']}")
    
    result = engine.execute(session, 'echo "INFO System OK" >> alerts.log')
    print(f"✓ Appended INFO line: {result['status']}")
    
    # Test normal grep
    result = engine.execute(session, 'grep "ERROR" alerts.log')
    print(f"\nNormal grep output:\n{result['output']}")
    print(f"Message: {result['message']}")
    
    # Test grep -c
    result = engine.execute(session, 'grep -c "ERROR" alerts.log')
    print(f"\ngrep -c output: {result['output']}")
    assert result['output'] == "2", f"Expected '2', got '{result['output']}'"
    print("✓ grep -c returned correct count")
    
    # Test grep -c with pipeline
    result = engine.execute(session, 'cat alerts.log | grep -c "ERROR"')
    print(f"\nPipeline grep -c output: {result['output']}")
    assert result['output'] == "2", f"Expected '2', got '{result['output']}'"
    print("✓ Pipeline grep -c works correctly")
    
    print("\n✅ grep -c tests PASSED\n")


def test_nano():
    """Test nano simulated editor"""
    print("=" * 60)
    print("TEST 2: nano (simulated editor)")
    print("=" * 60)
    
    engine = CommandExecutionEngine()
    session = TerminalSession("test-session")
    
    # Test nano on new file
    result = engine.execute(session, 'nano newfile.txt')
    print(f"nano newfile.txt response type: {result.get('type', 'response')}")
    
    if result.get('type') == 'nano':
        data = result.get('data', {})
        print(f"✓ nano returned special response")
        print(f"  - filename: {data.get('filename')}")
        print(f"  - path: {data.get('path')}")
        print(f"  - content: '{data.get('content')}'")
        assert data.get('filename') == 'newfile.txt'
        assert data.get('content') == ''
        print("✓ New file has empty content")
    
    # Create a file and test nano on existing file
    result = engine.execute(session, 'echo "Hello World" > existing.txt')
    print(f"\n✓ Created existing.txt: {result['status']}")
    
    result = engine.execute(session, 'nano existing.txt')
    if result.get('type') == 'nano':
        data = result.get('data', {})
        print(f"✓ nano opened existing file")
        print(f"  - content: '{data.get('content')}'")
        assert data.get('content') == 'Hello World'
        print("✓ Existing file content loaded correctly")
    
    # Test nano on directory (should fail)
    result = engine.execute(session, 'mkdir testdir')
    result = engine.execute(session, 'nano testdir')
    print(f"\nnano on directory error: {result['error']}")
    assert 'Is a directory' in result['error']
    print("✓ nano correctly rejects directories")
    
    print("\n✅ nano tests PASSED\n")


def test_sudo():
    """Test sudo command wrapper"""
    print("=" * 60)
    print("TEST 3: sudo (privilege wrapper)")
    print("=" * 60)
    
    engine = CommandExecutionEngine()
    session = TerminalSession("test-session")
    
    # Test sudo mkdir
    result = engine.execute(session, 'sudo mkdir admin')
    print(f"sudo mkdir result: {result['status']}")
    print(f"Message: {result['message']}")
    assert '[sudo]' in result['message']
    print("✓ sudo message indicator present")
    
    # Verify directory was created
    result = engine.execute(session, 'ls')
    print(f"ls output: {result['output']}")
    assert 'admin' in result['output']
    print("✓ sudo mkdir created directory")
    
    # Test sudo rm
    result = engine.execute(session, 'touch testfile.txt')
    result = engine.execute(session, 'sudo rm testfile.txt')
    print(f"\nsudo rm result: {result['status']}")
    print(f"Message: {result['message']}")
    assert result['status'] == 'success'
    print("✓ sudo rm executed successfully")
    
    # Test sudo with invalid command
    result = engine.execute(session, 'sudo invalidcmd')
    print(f"\nsudo invalid command error: {result['error']}")
    assert 'command not found' in result['error']
    print("✓ sudo handles invalid commands correctly")
    
    # Test sudo chmod
    result = engine.execute(session, 'touch config.txt')
    result = engine.execute(session, 'sudo chmod 755 config.txt')
    print(f"\nsudo chmod result: {result['status']}")
    print(f"Message: {result['message']}")
    assert result['status'] == 'success'
    print("✓ sudo chmod works correctly")
    
    print("\n✅ sudo tests PASSED\n")


def test_combined_features():
    """Test features working together"""
    print("=" * 60)
    print("TEST 4: Combined features")
    print("=" * 60)
    
    engine = CommandExecutionEngine()
    session = TerminalSession("test-session")
    session.mode = "exam"  # Use exam mode to avoid message in output
    
    # Create log file with sudo
    result = engine.execute(session, 'sudo mkdir logs')
    result = engine.execute(session, 'cd logs')
    result = engine.execute(session, 'echo "ERROR: Failed login" > system.log')
    result = engine.execute(session, 'echo "ERROR: Disk full" >> system.log')
    result = engine.execute(session, 'echo "INFO: System started" >> system.log')
    result = engine.execute(session, 'echo "ERROR: Network timeout" >> system.log')
    
    # Count errors with grep -c
    result = engine.execute(session, 'grep -c "ERROR" system.log')
    print(f"Error count in system.log: {result['output']}")
    assert result['output'] == "3"
    print("✓ grep -c counted 3 errors")
    
    # Use sudo with grep
    result = engine.execute(session, 'sudo grep -c "INFO" system.log')
    print(f"sudo grep -c INFO output: '{result['output']}'")
    print(f"Message: '{result['message']}'")
    print(f"Status: {result['status']}")
    # The output should be just "1", message is separate
    assert result['output'].strip() == "1", f"Expected '1', got '{result['output']}'"
    print("✓ sudo + grep -c works together")
    
    print("\n✅ Combined features test PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING NEW TERMINAL FEATURES")
    print("=" * 60 + "\n")
    
    try:
        test_grep_count()
        test_nano()
        test_sudo()
        test_combined_features()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNew features implemented:")
        print("  ✓ grep -c (count matching lines)")
        print("  ✓ nano (simulated editor with special response)")
        print("  ✓ sudo (privilege wrapper for commands)")
        print("\nReady for CEO demo! 🚀")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
