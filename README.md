# Generator Soft-Start

Help small portable generators (Honda EU1000i) start window air conditioners by supplementing current during motor startup.

## The Problem

A 1000W generator can run an 8000 BTU window AC (~720W) once it's running, but the compressor's startup surge (5-7× running current for 300-500ms) overwhelms the generator, causing it to bog down or trip.

## The Solution

A supercapacitor bank that:
1. Charges from the AC line during normal operation
2. Detects motor startup (current surge)
3. Injects supplemental current synchronized to the AC waveform
4. Shuts off after the motor reaches speed

## Design

```
GENERATOR ──┬──────────────────────────────────────┬── LOAD (AC Unit)
            │                                      │
            │   ┌────────────────────────────┐     │
            │   │      SUPERCAP BANK         │     │
            │   │   30 × 12F 2.7V = 81V      │     │
            └───┤                            ├─────┘
                │   Charging    Discharge    │
                │   Circuit     MOSFET       │
                │       ↑          ↑         │
                │       └────┬─────┘         │
                │            │               │
                │      ┌─────┴─────┐         │
                │      │  STM32    │         │
                │      │  MCU      │         │
                │      └───────────┘         │
                └────────────────────────────┘
                        × 2 banks
                  (positive & negative half-cycles)
```

## Specifications

| Parameter | Value |
|-----------|-------|
| Supercapacitors | 60 × Tecate 12F 2.7V |
| Bank voltage | 81V (30 series per bank) |
| AC coverage | 32% of waveform |
| Energy delivery | ~110J in 200ms |
| Effective current | ~14A RMS |
| MCU | STM32G031 |
| **Estimated BOM** | **~$85** |

## Key Components

| Component | Part Number | Qty | Unit Cost |
|-----------|-------------|-----|-----------|
| Supercapacitor | Tecate TPLH-2R7/12WR10X30 | 60 | $0.91 |
| MCU | STM32G031F6P6 | 1 | $1.50 |
| MOSFET | IRFB4110 | 2 | $1.50 |
| PCB | JLCPCB 2-layer | 1 | ~$15 |

## How It Works

1. **Charging:** Supercaps charge through current-limiting resistors when AC voltage is in safe range
2. **Detection:** MCU monitors load current; spike indicates motor starting
3. **Injection:** When V_ac < 81V (near zero-crossing), MOSFET connects supercap bank
4. **PWM Control:** MCU shapes injection current to approximate sinusoid
5. **Timeout:** Assist limited to 500ms to prevent overheating

### Phase Alignment Advantage

Motor current *lags* voltage by ~70° due to inductance. This means peak current occurs near voltage zero-crossing—exactly where our injection window is. The 32% coverage captures the most critical part of the cycle.

## Project Structure

```
softstart/
├── README.md                    # This file
├── hardware/
│   ├── design_spec.md           # Detailed design specification
│   └── kicad/
│       ├── softstart.kicad_pro  # KiCad project
│       └── softstart.kicad_dru  # JLCPCB design rules
├── src/                         # Analysis scripts
├── docs/                        # Design evolution & analysis
│   ├── design_evolution.md      # How we got here
│   └── *.png                    # Analysis plots
├── requirements.txt
└── pyproject.toml
```

## Status

- [x] Design analysis complete
- [x] Component selection finalized
- [x] KiCad project initialized
- [ ] Schematic capture
- [ ] PCB layout
- [ ] Firmware development
- [ ] Prototype build
- [ ] Testing

## Safety

**This device operates at mains voltage (120VAC) and stores significant energy (81V, ~1300J). It can cause injury or death if mishandled.**

- Always discharge supercaps before servicing
- Use proper enclosure
- Include appropriate fusing
- For experimental/educational use only

## Documentation

- [Design Specification](hardware/design_spec.md) - Complete technical specification
- [Design Evolution](docs/design_evolution.md) - How we explored different approaches

## License

MIT
