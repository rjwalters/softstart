# Softstart Power Supply Simulations

SPICE simulations for validating MCU power supply stability under various operating conditions.

## Overview

The softstart board uses a supercapacitor-based power assist system. The MCU power supply chain is:

```
AC Input → Bridge Rectifier (D5) → C8 (1000µF) → LM7812 → AMS1117-3.3 → STM32
```

These simulations verify that the MCU supply remains stable during:
1. **Startup** - when supercaps are discharged and drawing charging current
2. **Droop events** - when generator voltage sags and supercaps discharge
3. **Brown-out conditions** - finding minimum operating voltage

## Prerequisites

Install ngspice:

```bash
# macOS
brew install ngspice

# Ubuntu/Debian
sudo apt-get install ngspice

# Windows
# Download from http://ngspice.sourceforge.net/
```

## Running Simulations

### Run All Simulations
```bash
./run_simulations.sh all
```

### Run Individual Simulations
```bash
./run_simulations.sh startup    # Startup transient
./run_simulations.sh droop      # Droop event
./run_simulations.sh brownout   # Brown-out threshold
```

### Interactive Mode
For debugging or exploring waveforms:
```bash
./run_simulations.sh interactive startup_transient.cir
```

In ngspice interactive mode:
```
ngspice> run
ngspice> plot v(rail_3v3) v(rail_12v)
ngspice> meas tran v_min MIN v(rail_3v3)
```

## Simulation Descriptions

### 1. Startup Transient (`startup_transient.cir`)

Simulates power-on with fully discharged supercaps (worst case).

**What it tests:**
- Rectified voltage sag due to supercap charging current
- LM7812 behavior during input voltage dips
- Time to stable 3.3V rail
- MCU brown-out reset risk

**Key parameters:**
- Generator: 120V RMS, 60Hz, 2Ω internal impedance
- Supercaps: 0V initial (worst case)
- Precharge: 100Ω/220Ω resistors

**Pass criteria:**
- 3.3V rail never drops below 2.0V (BOR threshold)
- 12V rail stays above 10V

### 2. Droop Event (`droop_event.cir`)

Simulates generator voltage droop that triggers supercap assist.

**What it tests:**
- MCU supply during 25% voltage droop
- Transition behavior when supercaps start discharging
- Recovery when voltage returns to normal

**Key parameters:**
- Normal: 120V RMS
- Droop: 90V RMS (25% reduction)
- Droop duration: 200ms
- Supercaps: 60V initial (charged)

**Pass criteria:**
- No MCU reset during droop event
- 3.3V rail stays above 3.0V

### 3. Brown-out Threshold (`brownout_threshold.cir`)

Determines minimum AC input voltage for stable MCU operation.

**What it tests:**
- Slow ramp from 120V to 40V RMS
- Find exact voltage where each rail loses regulation
- Calculate safety margins

**Key measurements:**
- AC voltage where 12V rail < 11V (dropout)
- AC voltage where 3.3V rail < 3.0V (warning)
- AC voltage where 3.3V rail < 2.0V (BOR)

## Component Models

Models are in `lib/components.lib`:

| Model | Description |
|-------|-------------|
| `LM7812` | 12V linear regulator with dropout behavior |
| `AMS1117` | 3.3V LDO with 1.1V dropout |
| `SUPERCAP_BANK_30S` | 30-series supercap bank (0.4F, 0.9Ω ESR) |
| `BRIDGE_RECT` | MB6S equivalent bridge rectifier |
| `GENERATOR` | AC source with internal impedance |
| `GENERATOR_DROOP` | AC source with controllable voltage droop |
| `STM32_LOAD` | MCU current draw and BOR detection |

## Results

Results are saved to `results/`:
- `.csv` files with waveform data
- `.log` files with measurement outputs

## Interpreting Results

### Good Results
```
PASS: 3.3V rail stayed above brownout threshold
      Minimum was: 3.15 V
PASS: No MCU reset during droop
```

### Concerning Results
```
WARNING: 3.3V rail dropped below 3.0V during droop
         Minimum: 2.85 V
```

### Failing Results
```
FAIL: 3.3V rail dropped below brownout threshold (2.0V)
      Minimum was: 1.8 V
FAIL: MCU reset during droop event!
```

## Potential Mitigations

If simulations show MCU supply instability:

1. **Increase C8** - More bulk capacitance on LM7812 input
2. **Add capacitance on 3.3V** - More local bypass (C1/C2)
3. **Supervisor IC** - Add voltage monitor with reset hold-off
4. **Separate supply** - Dedicated small transformer for MCU
5. **Pre-regulator** - Add switching pre-reg before LM7812
6. **Delay MCU startup** - Wait for supercaps to charge

## Files

```
simulation/
├── README.md                 # This file
├── run_simulations.sh        # Run script
├── lib/
│   └── components.lib        # SPICE component models
├── startup_transient.cir     # Startup test bench
├── droop_event.cir           # Droop test bench
├── brownout_threshold.cir    # Brown-out test bench
└── results/                  # Output directory
```
