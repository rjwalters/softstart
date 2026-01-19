#!/bin/bash
# Softstart Power Supply Simulations
# Run all simulations or individual tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for ngspice
check_ngspice() {
    if ! command -v ngspice &> /dev/null; then
        echo -e "${RED}Error: ngspice not found${NC}"
        echo ""
        echo "Install ngspice:"
        echo "  macOS:   brew install ngspice"
        echo "  Ubuntu:  sudo apt-get install ngspice"
        echo "  Windows: Download from http://ngspice.sourceforge.net/"
        echo ""
        exit 1
    fi
    echo -e "${GREEN}Found ngspice: $(ngspice --version | head -1)${NC}"
}

# Run a simulation
run_sim() {
    local name=$1
    local file=$2

    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Running: $name${NC}"
    echo -e "${YELLOW}========================================${NC}"

    if [ -f "$file" ]; then
        ngspice -b "$file" 2>&1 | tee "results/${name}.log"
        echo -e "${GREEN}Completed: $name${NC}"
    else
        echo -e "${RED}File not found: $file${NC}"
        return 1
    fi
}

# Interactive mode
run_interactive() {
    local file=$1
    echo "Starting interactive ngspice session..."
    echo "Type 'run' to execute, 'plot v(node)' to visualize"
    ngspice "$file"
}

# Main
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all         Run all simulations (batch mode)"
    echo "  startup     Run startup transient simulation"
    echo "  droop       Run droop event simulation"
    echo "  brownout    Run brown-out threshold simulation"
    echo "  interactive <file>  Run simulation interactively"
    echo "  clean       Remove results"
    echo ""
    echo "Examples:"
    echo "  $0 all                          # Run all sims"
    echo "  $0 startup                      # Run just startup"
    echo "  $0 interactive startup_transient.cir"
}

# Create results directory
mkdir -p results

case "${1:-all}" in
    all)
        check_ngspice
        run_sim "startup_transient" "startup_transient.cir"
        run_sim "droop_event" "droop_event.cir"
        run_sim "brownout_threshold" "brownout_threshold.cir"
        echo ""
        echo -e "${GREEN}All simulations complete!${NC}"
        echo "Results in: $SCRIPT_DIR/results/"
        ;;
    startup)
        check_ngspice
        run_sim "startup_transient" "startup_transient.cir"
        ;;
    droop)
        check_ngspice
        run_sim "droop_event" "droop_event.cir"
        ;;
    brownout)
        check_ngspice
        run_sim "brownout_threshold" "brownout_threshold.cir"
        ;;
    interactive)
        check_ngspice
        if [ -z "$2" ]; then
            echo "Error: specify a .cir file"
            exit 1
        fi
        run_interactive "$2"
        ;;
    clean)
        echo "Cleaning results..."
        rm -rf results/*
        echo "Done"
        ;;
    *)
        usage
        exit 1
        ;;
esac
