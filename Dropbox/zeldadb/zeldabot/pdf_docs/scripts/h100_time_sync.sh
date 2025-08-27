#!/bin/bash
#
# H100 Time Sync Script - Handles container clock drift for JWT authentication
# Designed for containerized H100 GPU environments with persistent clock skew
#
set -euo pipefail

LOG_FILE="/tmp/h100_time_sync.log"
MAX_RETRIES=5
ACCEPTABLE_DRIFT_MS=30000  # 30 seconds max drift

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S UTC') [H100-TimeSync] $*" | tee -a "$LOG_FILE"
}

check_drift() {
    local drift_line
    drift_line=$(ntpdate -q pool.ntp.org 2>/dev/null | head -n1 || echo "offset 999.999")
    
    # Extract offset value (e.g., "-517.468625" from the ntpdate output)
    local offset
    offset=$(echo "$drift_line" | grep -oE '[-+]?[0-9]+\.[0-9]+' | head -n1 || echo "999.999")
    
    # Convert to milliseconds and get absolute value
    local drift_ms
    drift_ms=$(echo "$offset * 1000" | bc -l | sed 's/\..*//' | tr -d '-')
    
    log "Current time drift: ${offset}s (${drift_ms}ms)"
    echo "$drift_ms"
}

force_time_sync() {
    local attempt="$1"
    log "Time sync attempt $attempt/$MAX_RETRIES"
    
    # Kill existing NTP processes that might interfere
    pkill ntpd || true
    pkill chronyd || true
    
    # Multiple aggressive sync attempts
    if ntpdate -s pool.ntp.org 2>/dev/null; then
        log "ntpdate sync successful"
        return 0
    elif ntpdate -s time.nist.gov 2>/dev/null; then
        log "NIST time sync successful"  
        return 0
    elif ntpdate -s time.google.com 2>/dev/null; then
        log "Google time sync successful"
        return 0
    else
        log "All time servers failed"
        return 1
    fi
}

# Main sync logic
main() {
    log "Starting H100 time sync for JWT authentication"
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        local current_drift
        current_drift=$(check_drift)
        
        if (( current_drift < ACCEPTABLE_DRIFT_MS )); then
            log "Time drift acceptable: ${current_drift}ms < ${ACCEPTABLE_DRIFT_MS}ms"
            exit 0
        fi
        
        log "Time drift too high: ${current_drift}ms, attempting sync..."
        
        if force_time_sync "$attempt"; then
            sleep 2  # Allow time to settle
            local post_sync_drift
            post_sync_drift=$(check_drift)
            
            if (( post_sync_drift < ACCEPTABLE_DRIFT_MS )); then
                log "Sync successful! Post-sync drift: ${post_sync_drift}ms"
                exit 0
            else
                log "Sync partial - drift now ${post_sync_drift}ms"
            fi
        else
            log "Sync attempt $attempt failed"
        fi
        
        if (( attempt < MAX_RETRIES )); then
            local backoff=$((attempt * 5))
            log "Retrying in ${backoff} seconds..."
            sleep "$backoff"
        fi
    done
    
    log "ERROR: Failed to achieve acceptable time sync after $MAX_RETRIES attempts"
    log "This will likely cause JWT authentication failures"
    exit 1
}

# Handle script arguments
case "${1:-sync}" in
    "sync")
        main
        ;;
    "check")
        check_drift
        ;;
    "status")
        echo "Last sync log:"
        tail -n 10 "$LOG_FILE" 2>/dev/null || echo "No sync history"
        ;;
    *)
        echo "Usage: $0 {sync|check|status}"
        echo "  sync   - Perform aggressive time synchronization"
        echo "  check  - Check current drift in milliseconds"
        echo "  status - Show recent sync activity"
        exit 1
        ;;
esac