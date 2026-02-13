#!/bin/bash
# Diagnostic script for Practice Player freeze
# System works but OLED frozen, no sound, buttons unresponsive

OUTPUT_FILE="/home/claude/practice_player_freeze_$(date +%Y%m%d_%H%M%S).txt"

echo "========================================" | tee $OUTPUT_FILE
echo "PRACTICE PLAYER FREEZE DIAGNOSTIC" | tee -a $OUTPUT_FILE
echo "Generated: $(date)" | tee -a $OUTPUT_FILE
echo "========================================" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 1. FIND PRACTICE PLAYER PROCESS
echo "=== 1. PRACTICE PLAYER PROCESS STATUS ===" | tee -a $OUTPUT_FILE
PS_OUTPUT=$(ps aux | grep -i "practice" | grep -v grep)
if [ -z "$PS_OUTPUT" ]; then
    echo "⚠ No Practice Player process found!" | tee -a $OUTPUT_FILE
else
    echo "$PS_OUTPUT" | tee -a $OUTPUT_FILE
    PID=$(echo "$PS_OUTPUT" | awk '{print $2}')
    echo "" | tee -a $OUTPUT_FILE
    echo "Process ID: $PID" | tee -a $OUTPUT_FILE
    echo "CPU usage: $(echo "$PS_OUTPUT" | awk '{print $3}')%" | tee -a $OUTPUT_FILE
    echo "Memory usage: $(echo "$PS_OUTPUT" | awk '{print $4}')%" | tee -a $OUTPUT_FILE
    echo "Status: $(echo "$PS_OUTPUT" | awk '{print $8}')" | tee -a $OUTPUT_FILE
    
    # Check if process is in uninterruptible sleep (D state)
    STATE=$(ps -p $PID -o state --no-headers)
    if [ "$STATE" = "D" ]; then
        echo "⚠⚠⚠ PROCESS IN UNINTERRUPTIBLE SLEEP (D state) - likely I/O wait!" | tee -a $OUTPUT_FILE
    fi
fi
echo "" | tee -a $OUTPUT_FILE

# 2. ALL PYTHON PROCESSES
echo "=== 2. ALL PYTHON PROCESSES ===" | tee -a $OUTPUT_FILE
ps aux | grep python | grep -v grep | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 3. AUDIO SYSTEM STATUS
echo "=== 3. AUDIO SYSTEM STATUS ===" | tee -a $OUTPUT_FILE
echo "--- ALSA devices ---" | tee -a $OUTPUT_FILE
aplay -l 2>&1 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- Active audio processes ---" | tee -a $OUTPUT_FILE
lsof /dev/snd/* 2>&1 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- ALSA PCM info ---" | tee -a $OUTPUT_FILE
cat /proc/asound/pcm 2>&1 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 4. I2S AND AUDIO ERRORS (last 100 lines)
echo "=== 4. RECENT I2S/AUDIO ERRORS ===" | tee -a $OUTPUT_FILE
echo "--- Kernel messages (dmesg) ---" | tee -a $OUTPUT_FILE
dmesg | tail -100 | grep -i "i2s\|audio\|wm8731\|underrun\|overrun\|sync" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- System journal errors ---" | tee -a $OUTPUT_FILE
journalctl --since "10 minutes ago" -p err -b | grep -i "audio\|i2s\|sound\|alsa" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 5. I2C STATUS (for OLED)
echo "=== 5. I2C STATUS (OLED) ===" | tee -a $OUTPUT_FILE
echo "--- I2C devices detected ---" | tee -a $OUTPUT_FILE
i2cdetect -y 1 2>&1 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- I2C errors in dmesg ---" | tee -a $OUTPUT_FILE
dmesg | tail -100 | grep -i "i2c" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 6. GPIO STATUS
echo "=== 6. GPIO STATUS ===" | tee -a $OUTPUT_FILE
if [ -d "/sys/class/gpio" ]; then
    echo "Exported GPIO pins:" | tee -a $OUTPUT_FILE
    ls -l /sys/class/gpio/ | grep gpio | tee -a $OUTPUT_FILE
fi
echo "" | tee -a $OUTPUT_FILE

# 7. SYSTEM RESOURCES
echo "=== 7. SYSTEM RESOURCES ===" | tee -a $OUTPUT_FILE
echo "--- Memory ---" | tee -a $OUTPUT_FILE
free -h | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- CPU load ---" | tee -a $OUTPUT_FILE
uptime | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "--- Top CPU consumers ---" | tee -a $OUTPUT_FILE
ps aux --sort=-%cpu | head -10 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 8. POWER/THROTTLING
echo "=== 8. POWER STATUS ===" | tee -a $OUTPUT_FILE
THROTTLED=$(vcgencmd get_throttled)
echo "Throttling: $THROTTLED" | tee -a $OUTPUT_FILE
THROTTLED_HEX=$(echo $THROTTLED | cut -d= -f2)
if [ "$THROTTLED_HEX" != "0x0" ]; then
    echo "⚠⚠⚠ POWER ISSUES DETECTED!" | tee -a $OUTPUT_FILE
fi
echo "Temperature: $(vcgencmd measure_temp)" | tee -a $OUTPUT_FILE
echo "Voltage: $(vcgencmd measure_volts core)" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 9. RECENT SYSTEM ERRORS
echo "=== 9. RECENT SYSTEM ERRORS (last 5 min) ===" | tee -a $OUTPUT_FILE
journalctl --since "5 minutes ago" -p err -b 2>&1 | tail -50 | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# 10. PROCESS STACK TRACE (if we found the PID)
if [ ! -z "$PID" ]; then
    echo "=== 10. PROCESS STACK TRACE ===" | tee -a $OUTPUT_FILE
    echo "Stack trace for PID $PID:" | tee -a $OUTPUT_FILE
    cat /proc/$PID/stack 2>&1 | tee -a $OUTPUT_FILE
    echo "" | tee -a $OUTPUT_FILE
    
    echo "--- File descriptors ---" | tee -a $OUTPUT_FILE
    ls -l /proc/$PID/fd 2>&1 | tee -a $OUTPUT_FILE
    echo "" | tee -a $OUTPUT_FILE
fi

echo "========================================" | tee -a $OUTPUT_FILE
echo "DIAGNOSTIC COMPLETE" | tee -a $OUTPUT_FILE
echo "Report saved to: $OUTPUT_FILE" | tee -a $OUTPUT_FILE
echo "========================================" | tee -a $OUTPUT_FILE

# Quick summary
echo ""
echo "QUICK SUMMARY:"
if [ ! -z "$PID" ]; then
    echo "✓ Practice Player process found (PID: $PID)"
    if [ "$STATE" = "D" ]; then
        echo "⚠ CRITICAL: Process stuck in I/O wait!"
    fi
else
    echo "✗ Practice Player process NOT found - may have crashed"
fi

if [ "$THROTTLED_HEX" != "0x0" ]; then
    echo "⚠ POWER ISSUES detected - check supply!"
fi

echo ""
echo "To kill frozen process: sudo kill -9 $PID"
echo "To view full report: cat $OUTPUT_FILE"
