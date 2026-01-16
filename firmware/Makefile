# STM32G031 Soft-Start Firmware Makefile

# Project name
TARGET = softstart

# Toolchain
PREFIX = arm-none-eabi-
CC = $(PREFIX)gcc
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
OD = $(PREFIX)objdump

# Directories
BUILD_DIR = build
SRC_DIR = src
STARTUP_DIR = startup
INC_DIR = include
LINKER_DIR = linker

# Source files
C_SOURCES = \
    $(SRC_DIR)/main.c \
    $(STARTUP_DIR)/startup_stm32g031.c

# Include paths
C_INCLUDES = \
    -I$(INC_DIR)

# MCU flags
CPU = -mcpu=cortex-m0plus
FPU =
FLOAT-ABI =
MCU = $(CPU) -mthumb $(FPU) $(FLOAT-ABI)

# Compiler flags
CFLAGS = $(MCU) $(C_INCLUDES) -O2 -Wall -Wextra
CFLAGS += -fdata-sections -ffunction-sections
CFLAGS += -g -gdwarf-2
CFLAGS += -std=c99

# Linker flags
LDSCRIPT = $(LINKER_DIR)/stm32g031.ld
LDFLAGS = $(MCU) -specs=nano.specs -T$(LDSCRIPT)
LDFLAGS += -Wl,--gc-sections
LDFLAGS += -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref
LDFLAGS += -lc -lm -lnosys

# Default target
all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

# Create object list
OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))

# Build directory
$(BUILD_DIR):
	mkdir -p $@

# Compile C sources
$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

# Link
$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile $(LDSCRIPT)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

# Create hex file
$(BUILD_DIR)/$(TARGET).hex: $(BUILD_DIR)/$(TARGET).elf
	$(CP) -O ihex $< $@

# Create binary file
$(BUILD_DIR)/$(TARGET).bin: $(BUILD_DIR)/$(TARGET).elf
	$(CP) -O binary -S $< $@

# Disassembly
disasm: $(BUILD_DIR)/$(TARGET).elf
	$(OD) -d -S $< > $(BUILD_DIR)/$(TARGET).dis

# Size info
size: $(BUILD_DIR)/$(TARGET).elf
	$(SZ) --format=berkeley $<

# Clean
clean:
	rm -rf $(BUILD_DIR)

# Flash using OpenOCD
flash: $(BUILD_DIR)/$(TARGET).bin
	openocd -f interface/stlink.cfg -f target/stm32g0x.cfg \
		-c "program $(BUILD_DIR)/$(TARGET).bin 0x08000000 verify reset exit"

# Flash using ST-Link utility
flash-stlink: $(BUILD_DIR)/$(TARGET).bin
	st-flash write $(BUILD_DIR)/$(TARGET).bin 0x08000000

# Debug with GDB
debug: $(BUILD_DIR)/$(TARGET).elf
	$(PREFIX)gdb -x gdbinit $<

# Start OpenOCD server
openocd:
	openocd -f interface/stlink.cfg -f target/stm32g0x.cfg

# Erase chip
erase:
	openocd -f interface/stlink.cfg -f target/stm32g0x.cfg \
		-c "init; reset halt; stm32g0x mass_erase 0; exit"

.PHONY: all clean flash flash-stlink debug openocd erase disasm size
