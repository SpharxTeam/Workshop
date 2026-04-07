#!/bin/bash
# ============================================
# Workshop V2.0 Docker Container Entrypoint
# Handles initialization, health checks, and graceful shutdown
# ============================================

set -e

echo "============================================"
echo "🚀 Workshop V2.0 Container Starting..."
echo "============================================"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Environment: ${WORKSHOP_ENV:-development}"
echo "Python: $(python --version 2>&1)"
echo ""

# Function for error handling
error_exit() {
    echo "❌ ERROR: $1" >&2
    exit 1
}

# Function for warnings
warn() {
    echo "⚠️  WARNING: $1" >&2
}

# Create necessary directories if they don't exist
setup_directories() {
    echo "📁 Setting up directories..."
    
    local dirs=(
        "${WORKSHOP_DATA_DIR:-/app/data}"
        "${WORKSHOP_LOG_DIR:-/app/logs}"
        "${WORKSHOP_BACKUP_DIR:-/app/backups}"
        "${WORKSHOP_TEMP_DIR:-/app/temp}"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo "   ✅ Created: $dir"
        fi
    done
    
    # Set proper permissions (only if running as root)
    if [ "$(id -u)" = "0" ]; then
        chown -R workshop:workshop /app
    fi
}

# Validate environment variables
validate_environment() {
    echo "🔍 Validating environment configuration..."
    
    # Check required directories are writable
    local dirs=(
        "${WORKSHOP_DATA_DIR:-/app/data}"
        "${WORKSHOP_LOG_DIR:-/app/logs}"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -w "$dir" ]; then
            warn "Directory not writable: $dir"
        fi
    done
    
    # Log level validation
    case "${WORKSHOP_LOG_LEVEL:-INFO}" in
        DEBUG|INFO|WARNING|ERROR|CRITICAL)
            echo "   ✅ Log level: ${WORKSHOP_LOG_LEVEL}"
            ;;
        *)
            warn "Invalid log level: ${WORKSHOP_LOG_LEVEL}, defaulting to INFO"
            export WORKSHOP_LOG_LEVEL=INFO
            ;;
    esac
}

# Initialize logging system
initialize_logging() {
    echo "📝 Initializing logging system..."
    
    local log_dir="${WORKSHOP_LOG_DIR:-/app/logs}"
    local log_file="${log_dir}/workshop_$(date '+%Y%m%d').log"
    
    # Ensure log directory exists
    mkdir -p "$log_dir"
    
    echo "   📄 Log file: $log_file"
    export WORKSHOP_LOG_FILE="$log_file"
}

# Perform pre-flight checks
preflight_checks() {
    echo "✈️ Running pre-flight checks..."
    
    # Check Python imports
    python -c "
import sys
modules = [
    'common.core.base_pipeline',
    'common.core.config_manager',
    'common.core.exceptions',
    'common.core.logging_setup',
]
failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f'   ✅ {mod}')
    except ImportError as e:
        failed.append((mod, str(e)))
        print(f'   ❌ {mod}: {e}')

if failed:
    print(f'\n❌ Failed to import {len(failed)} module(s)')
    sys.exit(1)
else:
    print(f'\n✅ All core modules imported successfully')
" || error_exit "Pre-flight import check failed"
    
    # Check disk space (require at least 1GB free)
    local free_space=$(df -BG /app | awk 'NR==2 {print $4}' | tr -d 'G')
    if [ "$free_space" -lt 1 ] 2>/dev/null; then
        warn "Low disk space: only ${free_space}GB free"
    else
        echo "   💾 Disk space: ${free_space}GB free"
    fi
}

# Setup signal handlers for graceful shutdown
setup_signal_handlers() {
    echo "📡 Setting up signal handlers..."
    
    # Trap SIGTERM and SIGINT for graceful shutdown
    trap 'shutdown_handler' SIGTERM SIGINT INT
    
    echo "   ✅ Signal handlers configured"
}

# Graceful shutdown handler
shutdown_handler() {
    echo ""
    echo "============================================"
    echo "🛑 Received shutdown signal, gracefully stopping..."
    echo "============================================"
    
    # TODO: Add cleanup logic here
    # - Stop running pipelines
    # - Flush logs
    # - Close database connections
    # - Save state if needed
    
    echo "✅ Cleanup completed, exiting..."
    exit 0
}

# Main initialization sequence
main_init() {
    setup_directories
    validate_environment
    initialize_logging
    preflight_checks
    setup_signal_handlers
    
    echo ""
    echo "============================================"
    echo "✅ Initialization complete!"
    echo "🎯 Ready to execute: $*"
    echo "============================================"
    echo ""
}

# Run initialization
main_init

# Execute the main command
exec "$@"
