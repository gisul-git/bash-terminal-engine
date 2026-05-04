#!/usr/bin/env python3
"""
Interactive demo script showcasing new terminal features
Perfect for CEO presentations and stakeholder demos
"""

from execution_engine import CommandExecutionEngine
from session_manager import TerminalSession
import time


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_command(cmd):
    """Print a command with prompt"""
    print(f"$ {cmd}")


def execute_and_show(engine, session, command, delay=0.5):
    """Execute command and show output with delay for demo effect"""
    print_command(command)
    result = engine.execute(session, command)
    
    if result.get('type') == 'nano':
        data = result.get('data', {})
        print(f"[nano editor opened]")
        print(f"  File: {data.get('filename')}")
        print(f"  Content: {data.get('content')[:50]}..." if len(data.get('content', '')) > 50 else f"  Content: {data.get('content')}")
    else:
        output = result.get('output', '')
        error = result.get('error', '')
        if output:
            print(output)
        if error:
            print(f"Error: {error}")
    
    time.sleep(delay)
    return result


def demo_grep_count():
    """Demo grep -c feature"""
    print_header("DEMO 1: grep -c (Count Matching Lines)")
    
    engine = CommandExecutionEngine()
    session = TerminalSession("demo-session")
    
    print("Creating a log file with multiple error entries...\n")
    execute_and_show(engine, session, 'echo "2024-05-04 10:15:23 ERROR: Database connection failed" > system.log')
    execute_and_show(engine, session, 'echo "2024-05-04 10:15:45 INFO: Service started successfully" >> system.log')
    execute_and_show(engine, session, 'echo "2024-05-04 10:16:12 ERROR: Disk space low (5% remaining)" >> system.log')
    execute_and_show(engine, session, 'echo "2024-05-04 10:16:30 WARNING: High memory usage detected" >> system.log')
    execute_and_show(engine, session, 'echo "2024-05-04 10:17:01 ERROR: Network timeout on port 8080" >> system.log')
    
    print("\nLet's view the log file:")
    execute_and_show(engine, session, 'cat system.log', delay=1)
    
    print("\nNow, let's count how many ERROR entries we have:")
    execute_and_show(engine, session, 'grep -c "ERROR" system.log', delay=1)
    
    print("\n💡 Result: 3 errors found instantly!")
    
    print("\nWe can also use it in pipelines:")
    execute_and_show(engine, session, 'cat system.log | grep -c "INFO"', delay=1)
    
    print("\n✅ grep -c is perfect for log analysis and monitoring!")


def demo_nano():
    """Demo nano editor"""
    print_header("DEMO 2: nano (Simulated Text Editor)")
    
    engine = CommandExecutionEngine()
    session = TerminalSession("demo-session")
    
    print("Let's create a configuration file...\n")
    execute_and_show(engine, session, 'echo "server_port=8080" > config.txt')
    execute_and_show(engine, session, 'echo "debug_mode=false" >> config.txt')
    execute_and_show(engine, session, 'echo "max_connections=100" >> config.txt')
    
    print("\nView the current configuration:")
    execute_and_show(engine, session, 'cat config.txt', delay=1)
    
    print("\nNow let's edit it with nano:")
    result = execute_and_show(engine, session, 'nano config.txt', delay=1)
    
    print("\n💡 In a real browser terminal, this would open an editor modal!")
    print("   The frontend receives:")
    print(f"   - Filename: {result.get('data', {}).get('filename')}")
    print(f"   - Current content for editing")
    print("   - User can modify and save")
    
    print("\nLet's try creating a new file:")
    execute_and_show(engine, session, 'nano newscript.sh', delay=1)
    
    print("\n✅ nano provides a familiar editing experience!")


def demo_sudo():
    """Demo sudo command"""
    print_header("DEMO 3: sudo (Privilege Escalation)")
    
    engine = CommandExecutionEngine()
    session = TerminalSession("demo-session")
    
    print("Let's perform some administrative tasks...\n")
    
    print("Creating a system directory:")
    execute_and_show(engine, session, 'sudo mkdir /var/backups', delay=0.8)
    
    print("\nSetting up backup files:")
    execute_and_show(engine, session, 'cd /var/backups')
    execute_and_show(engine, session, 'sudo touch database.sql', delay=0.8)
    execute_and_show(engine, session, 'sudo touch config.tar.gz', delay=0.8)
    
    print("\nSetting secure permissions:")
    execute_and_show(engine, session, 'sudo chmod 600 database.sql', delay=0.8)
    
    print("\nVerifying our work:")
    execute_and_show(engine, session, 'ls', delay=1)
    
    print("\n💡 Notice the [sudo] indicators in the messages!")
    print("   This shows privilege escalation was used.")
    
    print("\n✅ sudo enables realistic IT admin scenarios!")


def demo_combined():
    """Demo all features working together"""
    print_header("DEMO 4: Combined Features - Real-World Scenario")
    
    engine = CommandExecutionEngine()
    session = TerminalSession("demo-session")
    session.mode = "exam"  # Clean output for demo
    
    print("Scenario: System administrator investigating server issues\n")
    
    print("Step 1: Create logs directory with elevated privileges")
    execute_and_show(engine, session, 'sudo mkdir /var/logs/webapp', delay=0.8)
    execute_and_show(engine, session, 'cd /var/logs/webapp')
    
    print("\nStep 2: Simulate application logs")
    execute_and_show(engine, session, 'echo "2024-05-04 ERROR: Authentication failed for user admin" > app.log')
    execute_and_show(engine, session, 'echo "2024-05-04 INFO: User john logged in successfully" >> app.log')
    execute_and_show(engine, session, 'echo "2024-05-04 ERROR: Database query timeout" >> app.log')
    execute_and_show(engine, session, 'echo "2024-05-04 ERROR: Failed to send email notification" >> app.log')
    execute_and_show(engine, session, 'echo "2024-05-04 INFO: Backup completed successfully" >> app.log')
    
    print("\nStep 3: Quick analysis - count critical errors")
    result = execute_and_show(engine, session, 'sudo grep -c "ERROR" app.log', delay=1)
    print(f"\n⚠️  Found {result.get('output', '0')} errors that need attention!")
    
    print("\nStep 4: View the actual errors")
    execute_and_show(engine, session, 'grep "ERROR" app.log', delay=1)
    
    print("\nStep 5: Create incident report")
    execute_and_show(engine, session, 'nano incident_report.txt', delay=1)
    print("   [Admin would document the 3 errors found]")
    
    print("\n✅ All features work seamlessly together!")
    print("   This demonstrates a realistic IT workflow.")


def main():
    """Run the complete demo"""
    print("\n" + "=" * 70)
    print("  🚀 LINUX BASH ENGINE - NEW FEATURES DEMONSTRATION")
    print("=" * 70)
    print("\n  Showcasing three powerful new capabilities:")
    print("    1. grep -c  - Count matching lines")
    print("    2. nano     - Simulated text editor")
    print("    3. sudo     - Privilege escalation")
    print("\n" + "=" * 70)
    
    input("\nPress Enter to start the demo...")
    
    try:
        demo_grep_count()
        input("\n\nPress Enter for next demo...")
        
        demo_nano()
        input("\n\nPress Enter for next demo...")
        
        demo_sudo()
        input("\n\nPress Enter for final demo...")
        
        demo_combined()
        
        print("\n" + "=" * 70)
        print("  🎉 DEMO COMPLETE!")
        print("=" * 70)
        print("\n  Key Takeaways:")
        print("    ✓ grep -c enables fast log analysis")
        print("    ✓ nano provides familiar file editing")
        print("    ✓ sudo creates realistic admin scenarios")
        print("    ✓ All features integrate seamlessly")
        print("\n  Ready for production deployment! 🚀")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
