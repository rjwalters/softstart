#!/bin/bash
#
# STM32G031 Flash Programming Script
# Generator Soft-Start Firmware
#
# Usage: ./flash.sh [options]
#   Options:
#     -b, --build     Build before flashing
#     -e, --erase     Erase chip before programming
#     -v, --verify    Verify after programming
#     -r, --reset     Reset after programming
#     -d, --debug     Start GDB debug session after flash
#     -s, --stlink    Use st-flash instead of OpenOCD
#     -h, --help      Show this help
#

set -e

# Configuration
BUILD_DIR="build"
TARGET="softstart"
BINARY="${BUILD_DIR}/${TARGET}.bin"
ELF="${BUILD_DIR}/${TARGET}.elf"
FLASH_ADDR="0x08000000"

# OpenOCD configuration
OPENOCD_INTERFACE="interface/stlink.cfg"
OPENOCD_TARGET="target/stm32g0x.cfg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Flags
DO_BUILD=0
DO_ERASE=0
DO_VERIFY=1
DO_RESET=1
DO_DEBUG=0
USE_STLINK=0

print_help() {
    head -20 "$0" | tail -15
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            DO_BUILD=1
            shift
            ;;
        -e|--erase)
            DO_ERASE=1
            shift
            ;;
        -v|--verify)
            DO_VERIFY=1
            shift
            ;;
        -r|--reset)
            DO_RESET=1
            shift
            ;;
        -d|--debug)
            DO_DEBUG=1
            shift
            ;;
        -s|--stlink)
            USE_STLINK=1
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Check for required tools
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 not found. Please install it."
        exit 1
    fi
}

if [ $USE_STLINK -eq 1 ]; then
    check_tool "st-flash"
else
    check_tool "openocd"
fi

# Build if requested
if [ $DO_BUILD -eq 1 ]; then
    log_info "Building firmware..."
    make clean
    make
fi

# Check binary exists
if [ ! -f "$BINARY" ]; then
    log_error "Binary not found: $BINARY"
    log_info "Run 'make' first or use -b flag"
    exit 1
fi

# Show binary info
log_info "Binary: $BINARY"
log_info "Size: $(stat -f%z "$BINARY" 2>/dev/null || stat -c%s "$BINARY") bytes"

# Flash using st-flash
if [ $USE_STLINK -eq 1 ]; then
    if [ $DO_ERASE -eq 1 ]; then
        log_info "Erasing chip..."
        st-flash erase
    fi

    log_info "Programming with st-flash..."
    st-flash write "$BINARY" "$FLASH_ADDR"

    if [ $DO_RESET -eq 1 ]; then
        log_info "Resetting target..."
        st-flash reset
    fi
else
    # Flash using OpenOCD
    OPENOCD_CMD="init; reset halt;"

    if [ $DO_ERASE -eq 1 ]; then
        log_info "Erasing chip..."
        OPENOCD_CMD+=" flash erase_sector 0 0 last;"
    fi

    log_info "Programming with OpenOCD..."
    OPENOCD_CMD+=" program $BINARY $FLASH_ADDR"

    if [ $DO_VERIFY -eq 1 ]; then
        OPENOCD_CMD+=" verify"
    fi

    if [ $DO_RESET -eq 1 ]; then
        OPENOCD_CMD+=" reset"
    fi

    OPENOCD_CMD+="; exit"

    openocd -f "$OPENOCD_INTERFACE" -f "$OPENOCD_TARGET" -c "$OPENOCD_CMD"
fi

log_info "Flash complete!"

# Start debug session if requested
if [ $DO_DEBUG -eq 1 ]; then
    if [ ! -f "$ELF" ]; then
        log_error "ELF file not found for debugging: $ELF"
        exit 1
    fi

    log_info "Starting debug session..."

    # Start OpenOCD in background
    openocd -f "$OPENOCD_INTERFACE" -f "$OPENOCD_TARGET" &
    OPENOCD_PID=$!

    # Give OpenOCD time to start
    sleep 1

    # Start GDB
    arm-none-eabi-gdb -x gdbinit "$ELF"

    # Kill OpenOCD when done
    kill $OPENOCD_PID 2>/dev/null || true
fi
