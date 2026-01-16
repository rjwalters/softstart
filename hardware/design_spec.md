# Generator Soft-Start Board Design Specification

## Overview

**Project:** Generator Power Assist (Soft Start)
**Version:** 1.0
**Target:** 8000 BTU Window AC with Honda EU1000i Generator

## Block Diagram

```
                                    ┌─────────────────────────────────────────────────────────────┐
                                    │                    SOFT-START BOARD                         │
                                    │                                                             │
   GENERATOR                        │   ┌─────────────┐      ┌─────────────┐      ┌──────────┐   │          LOAD
   120VAC 60Hz                      │   │   INPUT     │      │  SUPERCAP   │      │  OUTPUT  │   │       (Window AC)
  ══════════════════════════════════╪═══╡   STAGE     ╞══════╡   BANKS     ╞══════╡  STAGE   ╞═══╪════════════════════
       │                            │   │             │      │             │      │          │   │
       │                            │   │ • Fuse      │      │ • 30 × 12F  │      │ • MOSFET │   │
       │                            │   │ • Varistor  │      │   per bank  │      │   switch │   │
       │                            │   │ • Filter    │      │ • Charging  │      │ • Sync   │   │
       │                            │   └──────┬──────┘      │   circuit   │      └────┬─────┘   │
       │                            │          │             └──────┬──────┘           │         │
       │                            │          │                    │                  │         │
       │                            │   ┌──────┴────────────────────┴──────────────────┴─────┐   │
       │                            │   │                    MCU (STM32G031)                 │   │
       │                            │   │                                                    │   │
       │  ┌──────────────────────┐  │   │  • Zero-crossing detection                         │   │
       └──┤  VOLTAGE SENSE       ├──╫───┤  • Voltage monitoring (V_ac, V_supercap)           │   │
          │  (resistive divider) │  │   │  • Current sensing (load current)                  │   │
          └──────────────────────┘  │   │  • Motor start detection                           │   │
                                    │   │  • PWM control for sinusoidal injection            │   │
                                    │   │  • Protection (overcurrent, timeout)               │   │
                                    │   │  • Status LED                                      │   │
                                    │   └────────────────────────────────────────────────────┘   │
                                    │                                                             │
                                    └─────────────────────────────────────────────────────────────┘
```

## Electrical Specifications

### Power Path
| Parameter | Value | Notes |
|-----------|-------|-------|
| Input voltage | 120VAC ± 10% | 60Hz nominal |
| Output voltage | 120VAC | Pass-through |
| Max continuous current | 15A | Limited by PCB traces |
| Max surge current | 40A | During motor start, <1s |
| Isolation | None | Common neutral design |

### Supercapacitor Banks
| Parameter | Value | Notes |
|-----------|-------|-------|
| Supercap model | Tecate TPLH-2R7/12WR10X30 | 12F 2.7V |
| Cells per bank | 30 (series) | 81V per bank |
| Total cells | 60 | 2 banks (pos/neg half-cycle) |
| Bank voltage | 81.0V | 30 × 2.7V |
| Bank capacitance | 0.4F | 12F / 30 |
| Bank ESR | ~1.1Ω | 30 × 36mΩ |
| Energy storage | ~1300J total | To 50% voltage |
| Usable energy | ~650J per bank | 75% of stored |

### Boost Performance
| Parameter | Value | Notes |
|-----------|-------|-------|
| AC coverage | 32% | When V_ac < 81V |
| Discharge current | 25A max | Limited by ESR/thermal |
| Effective RMS current | 14A | Coverage-adjusted |
| Energy in 200ms | ~110J | Critical motor start window |
| Energy in 500ms | ~210J | Extended assist |
| Discharge to 50% | ~650ms | At 25A average |

### Charging
| Parameter | Value | Notes |
|-----------|-------|-------|
| Charge method | Resistor-limited from AC | Simple, robust |
| Charge current | 0.5-1A | Through 100Ω resistor |
| Charge time | ~60s from empty | To 95% voltage |
| Charge enable | When V_ac in range | MCU controlled |
| Safe voltage range | 100-140VAC peak | Disable outside range |

## Microcontroller

### MCU Selection
| Parameter | Value | Notes |
|-----------|-------|-------|
| Part number | STM32G031F6P6 | Or STM32G031K6T6 |
| Package | TSSOP20 or LQFP32 | Hand-solderable |
| Core | ARM Cortex-M0+ | 64MHz |
| Flash | 32KB | Plenty for this app |
| RAM | 8KB | Sufficient |
| ADC | 12-bit, 6 channels | For voltage/current sensing |
| Timers | TIM1 (advanced), TIM3, TIM14 | For PWM |
| Price | ~$1.50 | LCSC |

### MCU Pin Allocation
| Function | Pin | Type | Notes |
|----------|-----|------|-------|
| V_AC_SENSE | PA0 | ADC | AC voltage (divided) |
| V_SC_POS | PA1 | ADC | Positive bank voltage |
| V_SC_NEG | PA4 | ADC | Negative bank voltage |
| I_LOAD | PA5 | ADC | Load current sense |
| ZERO_CROSS | PA6 | EXTI | Zero-crossing interrupt |
| PWM_POS | PA8 | TIM1_CH1 | Positive bank MOSFET |
| PWM_NEG | PA9 | TIM1_CH2 | Negative bank MOSFET |
| CHARGE_EN | PB0 | GPIO | Charge enable |
| LED_STATUS | PB1 | GPIO | Status LED |
| UART_TX | PA2 | USART2 | Debug (optional) |

### Firmware Features
1. **Zero-crossing detection** - Interrupt on AC zero-cross
2. **Phase-locked loop** - Track AC frequency (50/60Hz auto)
3. **Motor start detection** - Current surge or voltage dip
4. **PWM current control** - Sinusoidal injection profile
5. **Protections:**
   - Overcurrent shutdown (>30A)
   - Assist timeout (500ms max)
   - Undervoltage lockout (supercap <40V)
   - Overvoltage lockout (supercap >85V)
   - Input voltage range check
6. **Status LED** - Indicate ready/charging/assisting/fault

## Circuit Blocks

### Input Stage
- **Fuse:** 20A fast-blow, 5×20mm
- **Varistor:** 150V MOV for surge protection
- **EMI filter:** Optional, common-mode choke

### Voltage Sensing
- **AC sense:** Resistive divider 470kΩ/10kΩ → 3.3V max at 170V peak
- **Supercap sense:** Resistive divider 47kΩ/10kΩ → 3.3V max at 85V
- **Isolation:** Optocoupler for zero-crossing (H11AA1)

### Current Sensing
- **Shunt resistor:** 0.005Ω 5W (low-side sensing)
- **Amplifier:** INA180 or similar, gain = 50
- **Range:** 0-40A → 0-3.3V

### Charging Circuit
- **Positive bank:** Diode + resistor from AC hot to supercap+
- **Negative bank:** Diode + resistor from AC neutral to supercap-
- **Diodes:** 1N5408 (1000V 3A) or similar
- **Resistor:** 100Ω 10W wirewound
- **Enable:** MOSFET switch controlled by MCU

### Discharge Circuit (per bank)
- **MOSFET:** IRFB4110 (100V, 180A, 3.7mΩ)
- **Gate driver:** Simple transistor driver or IR2110
- **Freewheeling diode:** Body diode of MOSFET sufficient
- **Snubber:** Optional RC (100Ω + 10nF)

## PCB Design

### Board Specifications
| Parameter | Value |
|-----------|-------|
| Dimensions | ~150mm × 100mm |
| Layers | 2 |
| Copper weight | 2oz (70µm) |
| Min trace/space | 0.2mm/0.2mm |
| Min via | 0.3mm drill |
| Surface finish | HASL or ENIG |
| Manufacturer | JLCPCB |

### High-Current Traces
| Net | Width | Notes |
|-----|-------|-------|
| AC_HOT | 3mm + polygon | 20A continuous |
| AC_NEUTRAL | 3mm + polygon | 20A continuous |
| SUPERCAP_BUS | 5mm + polygon | 25A surge |
| MOSFET_DRAIN | 5mm + polygon | 25A surge |

### Thermal Considerations
- MOSFETs: TO-220 with heatsink pad on PCB
- Charging resistors: Stand-off from PCB
- Supercaps: Ventilation spacing

### Layout Guidelines
1. Keep high-current loops small
2. Separate power and signal grounds (star ground)
3. Place current shunt near MOSFET source
4. Keep ADC traces away from switching nodes
5. Provide test points for debugging

## Bill of Materials

### Capacitors (Hand-Solder)
| Ref | Part | Qty | Unit | Total | Source |
|-----|------|-----|------|-------|--------|
| C1-C60 | Tecate 12F 2.7V TPLH-2R7/12WR10X30 | 60 | $0.91 | $54.60 | DigiKey |

### Semiconductors (JLCPCB or Hand)
| Ref | Part | Qty | Unit | Total | Source |
|-----|------|-----|------|-------|--------|
| U1 | STM32G031F6P6 | 1 | $1.50 | $1.50 | LCSC |
| Q1,Q2 | IRFB4110 MOSFET | 2 | $1.50 | $3.00 | LCSC |
| U2 | H11AA1 optocoupler | 1 | $0.50 | $0.50 | LCSC |
| U3 | INA180A1 current amp | 1 | $1.00 | $1.00 | LCSC |
| D1-D4 | 1N5408 diode | 4 | $0.10 | $0.40 | LCSC |
| D5 | LED 3mm green | 1 | $0.05 | $0.05 | LCSC |

### Passives
| Ref | Part | Qty | Unit | Total | Source |
|-----|------|-----|------|-------|--------|
| R1,R2 | 100Ω 10W wirewound | 2 | $0.50 | $1.00 | LCSC |
| R3,R4 | 0.005Ω 5W shunt | 2 | $0.50 | $1.00 | LCSC |
| R_dividers | Resistors, misc | 1 | $2.00 | $2.00 | LCSC |
| C_bypass | 100nF 50V 0805 | 10 | $0.02 | $0.20 | LCSC |
| C_bulk | 10µF 16V 0805 | 2 | $0.05 | $0.10 | LCSC |

### Protection & Connectors
| Ref | Part | Qty | Unit | Total | Source |
|-----|------|-----|------|-------|--------|
| F1 | Fuse 20A 5×20mm + holder | 1 | $0.50 | $0.50 | LCSC |
| MOV1 | Varistor 150V | 1 | $0.30 | $0.30 | LCSC |
| J1,J2 | Screw terminal 2-pos 30A | 2 | $1.00 | $2.00 | LCSC |
| J3 | Pin header 4-pos (debug) | 1 | $0.10 | $0.10 | LCSC |

### Mechanical
| Item | Qty | Unit | Total | Source |
|------|-----|------|-------|--------|
| PCB 150×100mm 2-layer | 5 | $3.00 | $15.00 | JLCPCB |
| Heatsink TO-220 | 2 | $0.50 | $1.00 | AliExpress |
| Standoffs M3 | 4 | $0.10 | $0.40 | - |
| Enclosure (optional) | 1 | $10.00 | $10.00 | - |

### BOM Summary
| Category | Cost |
|----------|------|
| Supercapacitors | $54.60 |
| Semiconductors | $6.45 |
| Passives | $4.30 |
| Protection/Connectors | $2.90 |
| PCB | $15.00 |
| Mechanical | $1.40 |
| **TOTAL** | **$84.65** |

## Assembly Notes

### Hand-Solder Components
- All 60 supercapacitors (through-hole)
- Power resistors (through-hole)
- Fuse holder
- Screw terminals
- MOSFETs with heatsinks

### JLCPCB Assembly (Optional)
Could have JLCPCB assemble:
- MCU (TSSOP20)
- Small SMD passives
- Optocoupler

### Assembly Sequence
1. SMD components first (if any)
2. Low-profile through-hole (resistors, ICs)
3. Supercapacitors (match polarity!)
4. Power components (MOSFETs, terminal blocks)
5. Test power rails before connecting AC

## Testing Procedure

### Bench Tests (No AC)
1. Verify continuity of supercap banks
2. Check for shorts to ground
3. Program MCU, verify LED blinks
4. Inject DC to test voltage sensing ADCs

### Low-Voltage AC Tests (Variac)
1. Start at 30VAC, verify zero-crossing detection
2. Increase to 60VAC, verify charging begins
3. Verify supercap voltages track expected values
4. Check charge current with ammeter

### Full Voltage Tests (120VAC)
1. Connect through isolation transformer if available
2. Verify charge to 81V on both banks
3. Simulate motor start (resistive load + switch)
4. Verify boost activates and times out correctly
5. Check thermal rise on MOSFETs and resistors

### Motor Load Tests
1. Connect to actual window AC
2. Verify assist triggers on compressor start
3. Measure generator voltage/frequency during start
4. Compare with/without soft-start

## Safety Warnings

1. **LETHAL VOLTAGES** - 120VAC and 81VDC can kill
2. **Stored energy** - Supercaps hold charge; discharge before servicing
3. **No isolation** - Device is connected to AC mains
4. **Fuse required** - Never bypass fuse
5. **Enclosure required** - Do not operate without proper enclosure
6. **Not UL listed** - For experimental/educational use only
