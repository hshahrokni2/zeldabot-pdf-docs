#!/bin/bash
#
# H100 Twin Agent Deployment with JWT Clock Skew Fix
# Deploys time-synchronized twin agent architecture (Qwen + Gemini) to H100
#
set -euo pipefail

REMOTE_HOST="root@45.135.56.10"
REMOTE_PORT="26983"
SSH_KEY="$HOME/.ssh/BrfGraphRag"
REMOTE_PATH="/root/zelda/Pure_LLM_Ftw"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S UTC') [H100-Deploy] $*"
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    if [[ ! -f "$SSH_KEY" ]]; then
        log "ERROR: SSH key not found at $SSH_KEY"
        exit 1
    fi
    
    # Test SSH connection
    if ! ssh -p "$REMOTE_PORT" -i "$SSH_KEY" -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'SSH OK'" >/dev/null 2>&1; then
        log "ERROR: Cannot connect to H100 server"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Deploy time sync script
deploy_time_sync() {
    log "Deploying time synchronization script..."
    
    scp -P "$REMOTE_PORT" -i "$SSH_KEY" \
        "$(dirname "$0")/h100_time_sync.sh" \
        "$REMOTE_HOST:$REMOTE_PATH/scripts/"
    
    ssh -p "$REMOTE_PORT" -i "$SSH_KEY" "$REMOTE_HOST" \
        "chmod +x $REMOTE_PATH/scripts/h100_time_sync.sh"
    
    log "Time sync script deployed"
}

# Deploy enhanced Gemini agent
deploy_gemini_agent() {
    log "Deploying enhanced Gemini agent with JWT fixes..."
    
    scp -P "$REMOTE_PORT" -i "$SSH_KEY" \
        "$(dirname "$0")/../src/agents/gemini_agent.py" \
        "$REMOTE_HOST:$REMOTE_PATH/src/agents/"
    
    log "Enhanced Gemini agent deployed"
}

# Run time sync on remote
sync_remote_time() {
    log "Synchronizing H100 system time..."
    
    ssh -p "$REMOTE_PORT" -i "$SSH_KEY" "$REMOTE_HOST" \
        "$REMOTE_PATH/scripts/h100_time_sync.sh sync" || {
        log "WARNING: Time sync failed, but continuing deployment"
    }
    
    # Check final drift
    local drift
    drift=$(ssh -p "$REMOTE_PORT" -i "$SSH_KEY" "$REMOTE_HOST" \
        "$REMOTE_PATH/scripts/h100_time_sync.sh check" || echo "unknown")
    
    log "Current time drift: ${drift}ms"
}

# Test twin agents
test_twin_agents() {
    log "Testing twin agent architecture..."
    
    # Set environment for test
    ssh -p "$REMOTE_PORT" -i "$SSH_KEY" "$REMOTE_HOST" "
        export DATABASE_URL='postgresql://zelda_user:\${ZELDA_DB_PWD}@localhost:15432/zelda_arsredovisning'
        export GEMINI_API_KEY='AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw'
        export GEMINI_ENDPOINT='https://europe-west4-aiplatform.googleapis.com/v1/projects/brf-graphrag-swedish/locations/europe-west4/publishers/google/models/gemini-2.5-pro:generateContent'
        export GOOGLE_APPLICATION_CREDENTIALS='$REMOTE_PATH/brf-graphrag-swedish-aug27.json'
        export TWIN_AGENTS=1
        export OBS_STRICT=1
        export JSON_SALVAGE=0
        
        cd $REMOTE_PATH
        python3 -c \"
from src.agents.gemini_agent import GeminiAgent
import logging
logging.basicConfig(level=logging.INFO)

print('Testing enhanced Gemini agent...')
agent = GeminiAgent()
health = agent.health_check()
print(f'Gemini health check: {health}')

if health:
    print('✅ Gemini agent is operational')
else:
    print('❌ Gemini agent failed health check')
\"
    "
    
    log "Twin agent test completed"
}

# Main deployment flow
main() {
    log "Starting H100 twin agent deployment with JWT fixes"
    
    check_prerequisites
    deploy_time_sync
    sync_remote_time
    deploy_gemini_agent
    test_twin_agents
    
    log "✅ H100 twin agent deployment completed successfully"
    log ""
    log "Next steps:"
    log "1. Run: ssh -p $REMOTE_PORT -i $SSH_KEY $REMOTE_HOST"
    log "2. Execute: cd $REMOTE_PATH && python scripts/run_prod.py --limit 1"
    log "3. Check receipts: tail -f artifacts/calls_log.ndjson"
}

main "$@"