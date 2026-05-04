# Quick Reference - New Features

## grep -c (Count Matches)

### Basic Usage
```bash
grep -c "pattern" file.txt
```

### Examples
```bash
# Count errors in log
grep -c "ERROR" system.log
# Output: 5

# Count with pipeline
cat app.log | grep -c "WARNING"
# Output: 12

# Count INFO messages
grep -c "INFO" /var/log/messages
# Output: 234
```

### Use Cases
- Log analysis
- Error counting
- Pattern frequency
- Quick statistics

---

## nano (Text Editor)

### Basic Usage
```bash
nano filename.txt
```

### Examples
```bash
# Edit existing file
nano config.json

# Create new file
nano script.sh

# Edit in subdirectory
nano /etc/app/settings.conf
```

### Response Format
```json
{
  "type": "nano",
  "data": {
    "filename": "config.json",
    "path": "/home/user/config.json",
    "content": "file content here"
  }
}
```

### Frontend Integration
1. Detect `type: "nano"` response
2. Open editor modal with content
3. User edits text
4. Send `nano_save` message:
```json
{
  "type": "nano_save",
  "data": {
    "file": "config.json",
    "content": "updated content"
  }
}
```

---

## sudo (Privilege Wrapper)

### Basic Usage
```bash
sudo command [args...]
```

### Examples
```bash
# Create directory
sudo mkdir /var/backups

# Remove file
sudo rm /tmp/cache.dat

# Change permissions
sudo chmod 755 script.sh

# With grep
sudo grep -c "ERROR" /var/log/secure
```

### Behavior
- Executes command normally
- Adds `[sudo]` to messages
- No password required
- Works with any command

---

## Combined Examples

### Scenario 1: Log Analysis
```bash
sudo mkdir /var/analysis
cd /var/analysis
sudo grep "ERROR" /var/log/system.log > errors.txt
grep -c "CRITICAL" errors.txt
nano report.txt
```

### Scenario 2: System Monitoring
```bash
grep -c "Failed" /var/log/auth.log
sudo grep -c "Accepted" /var/log/auth.log
nano security_summary.txt
```

### Scenario 3: Configuration Management
```bash
sudo nano /etc/app/config.json
cat /etc/app/config.json | grep -c "enabled"
sudo chmod 644 /etc/app/config.json
```

---

## Testing Commands

### Quick Test
```bash
# Test grep -c
echo "ERROR 1" > test.log
echo "ERROR 2" >> test.log
grep -c "ERROR" test.log  # Should return: 2

# Test nano
nano test.txt  # Should return nano response

# Test sudo
sudo mkdir testdir
ls  # Should show: testdir
```

### Run Full Test Suite
```bash
python test_new_features.py
```

### Run Interactive Demo
```bash
python demo_script.py
```

---

## Error Messages

### grep -c
```bash
grep -c           # Error: grep: missing pattern
grep -c "text"    # Error: grep: no input provided
```

### nano
```bash
nano              # Error: nano: missing file operand
nano dirname/     # Error: nano: dirname/: Is a directory
```

### sudo
```bash
sudo              # Error: sudo: missing command
sudo badcmd       # Error: sudo: badcmd: command not found
```

---

## Tips & Tricks

### grep -c
- Use with pipelines for complex filtering
- Combine with other commands for analysis
- Perfect for quick counts without scrolling

### nano
- Frontend must implement editor modal
- Content is returned for editing
- Save sends `nano_save` message back

### sudo
- Purely simulated (no real privileges)
- Great for training scenarios
- Shows `[sudo]` indicator in messages

---

## Documentation

- **Full Details**: [NEW_FEATURES.md](NEW_FEATURES.md)
- **Upgrade Summary**: [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)
- **Main README**: [README.md](README.md)
- **Test Suite**: [test_new_features.py](test_new_features.py)
- **Demo Script**: [demo_script.py](demo_script.py)
