# Generator Power Assist (Soft Start)

## Problem Statement

Small portable generators (like the Honda EU1000i, ~1000W) struggle with inductive startup loads. When an air conditioner or refrigerator compressor starts, it draws 3-6x its running current for 1-3 seconds. This startup surge can exceed the generator's capacity, causing it to bog down or trip.

**Goal:** Supplement the generator with ~500-800W of additional power for 2-3 seconds during motor startup. The generator still provides most of the power - we just help it over the hump.

## Design Evolution

Through analysis and simulation, we explored several approaches:

1. **Multi-tier LiPo batteries** - Different voltage tiers (2S, 4S, 8S) for different parts of the AC waveform. Rejected due to BMS complexity and cycle life concerns.

2. **Supercap-only with PWM** - Simple and robust, but limited AC coverage means lower effective power delivery.

3. **Hybrid supercap + electrolytic stacking** - Best cost/performance ratio. Electrolytics provide voltage boost, supercaps provide energy storage.

## Recommended Design: Hybrid Stacking

### Core Concept

**Charge separately, discharge in series:**

```
CHARGING (separate windows):              DISCHARGING (series):

AC passes through 24V:                         Load
  → Supercaps charge to 24V                      ↑
                                           ┌─────┴─────┐
AC passes through 60V:                     │  Supercap │ 24V
  → Electrolytics charge to 60V            │   Bank    │
                                           ├───────────┤
                                           │Electrolytic│ 60V
                                           │   Bank    │
                                           └─────┬─────┘
                                              Neutral

                                    Stacked voltage: 84V
                                    Coverage: 33% of AC cycle
```

### Why Hybrid Stacking Works

| Component | Strength | Role in Hybrid |
|-----------|----------|----------------|
| Supercaps | High energy density, high current | Energy storage |
| Electrolytics | High voltage rating, cheap | Voltage boost |

**Key insight:** Electrolytics are cheap per volt, supercaps are cheap per joule. Combining them optimizes both.

### Configuration Analysis

We analyzed configurations across 12-20 supercaps × 40-64 electrolytics:

**Energy delivered in first 200ms (critical motor start window):**

```
        │   40E   │   44E   │   48E   │   52E   │   56E   │   60E   │
────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
  12SC  │   129J  │   142J  │   154J  │   166J  │   178J  │   180J  │
  14SC  │   140J  │   153J  │   166J  │   179J  │   192J  │   194J  │
  16SC  │   151J  │   165J  │   178J  │   192J  │   206J  │   208J  │
  18SC  │   162J  │   177J  │   191J  │   206J  │   220J  │   223J  │
  20SC  │   174J  │   190J  │   205J  │   220J  │   235J  │   238J  │
```

**Cost ($):**

```
        │   40E   │   44E   │   48E   │   52E   │   56E   │   60E   │
────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
  12SC  │  $163   │  $172   │  $181   │  $191   │  $200   │  $209   │
  14SC  │  $175   │  $184   │  $193   │  $203   │  $212   │  $221   │
  16SC  │  $187   │  $196   │  $205   │  $215   │  $224   │  $233   │
  18SC  │  $199   │  $208   │  $217   │  $227   │  $236   │  $245   │
  20SC  │  $211   │  $220   │  $229   │  $239   │  $248   │  $257   │
```

**Sweet spot: 56 electrolytics** - Provides ~197ms boost duration, just covering the critical 200ms window. More electrolytics beyond this don't help.

### Recommended Configurations

| Goal | Config | Cost | Energy | J/$ | Notes |
|------|--------|------|--------|-----|-------|
| **Budget** | 18SC+40E | $199 | 162J | 0.81 | Good balance |
| **Best value** | 16SC+56E | $224 | 206J | 0.92 | Optimal J/$ |
| **Maximum** | 20SC+56E | $248 | 235J | 0.95 | Best efficiency |

### Primary Recommendation: 16SC + 56E

| Parameter | Value |
|-----------|-------|
| Supercaps | 16 total (8 per bank) |
| Electrolytics | 56 total (28 per bank) |
| **Total Cost** | **$224** |
| Supercap voltage | 21.6V (8 × 2.7V) |
| Stacked voltage | 81.6V |
| AC coverage | 32% |
| Boost duration | 197ms |
| Energy in 200ms | 206J |
| Peak power | ~1,000W |

**Cost breakdown:**
- Supercaps (100F 2.7V): 16 × $6.00 = $96
- Electrolytics (4700µF 100V): 56 × $2.28 = $128

## Target Application: Window AC Units

### Motor Startup Characteristics

Window AC compressors are challenging inductive loads:

| Unit Size | Running | FLA | LRA (5.5×) | Startup Time |
|-----------|---------|-----|------------|--------------|
| 5000 BTU  | 450W    | 3.8A | 21A       | ~200ms       |
| 6000 BTU  | 540W    | 4.5A | 25A       | ~250ms       |
| 8000 BTU  | 720W    | 6.0A | 33A       | ~300ms       |
| 10000 BTU | 900W    | 7.5A | 41A       | ~350ms       |
| 12000 BTU | 1080W   | 9.0A | 50A       | ~400ms       |

**Key insight:** LRA (Locked Rotor Amps) is typically 5-7× the running current and lasts 0.5-1.5 seconds.

### Startup Current Profile

```
Current
  ↑
  │    ┌──────┐
  │    │      │ LRA (Locked Rotor)
  │    │      └──────┐
  │    │              └───────┐
  │    │                      └────────── FLA (Running)
  │    │
  └────┴──────────────────────────────────────→ Time
       0    100ms  200ms  300ms  500ms

  Phase 1: Initial surge (0-8ms) - up to 20× FLA
  Phase 2: Locked rotor (8-180ms) - ~5-7× FLA
  Phase 3: Acceleration (180-500ms) - decreasing
  Phase 4: Running - FLA steady state
```

### Phase Alignment Advantage

Our design benefits from motor inductance:

- **Motor current lags voltage by ~70°** at locked rotor (PF ≈ 0.35)
- **Peak motor current occurs near voltage zero-crossing**
- **Our injection window includes zero-crossing** (|V_ac| < 81.6V)
- **We inject maximum current exactly when motor needs it most!**

```
         V_ac                    I_motor (lagging 70°)
           │                           │
    Peak → │ ╱╲                        │    ╱╲
           │╱  ╲                       │   ╱  ╲
   ────────┼────╲─────────────────────┼──╱────╲──────
           │     ╲  ╱                  │ ╱      ╲
           │      ╲╱ ← Zero crossing   │╱        ╲ ← Peak current HERE
           │                           │

Our injection window: when |V_ac| < 81.6V (shaded region around zero crossing)
Motor peak current: at zero crossing due to 70° lag

Result: 32% AC coverage captures the most critical 32%!
```

### Capability Matrix

**Honda EU1000i + Our Hybrid Boost:**

| AC Unit | Energy Needed | Our Capacity | Margin | Can Start? |
|---------|---------------|--------------|--------|------------|
| 5000 BTU | ~77J in 200ms | 206J | +129J | ✓✓ HIGH |
| 6000 BTU | ~108J in 200ms | 206J | +98J | ✓✓ HIGH |
| **8000 BTU** | **~174J in 200ms** | **206J** | **+32J** | **✓ MEDIUM** |
| 10000 BTU | ~241J in 200ms | 206J | -35J | ? MARGINAL |
| 12000 BTU | ~308J in 200ms | 206J | -102J | ✗ NO |

### Detailed Analysis: 8000 BTU (Target Application)

**Without soft-start:**
- Motor demands 33A LRA
- Generator can supply 8.3A max
- Shortfall: 24.7A → **voltage collapses, motor stalls**

**With our soft-start:**
- Generator provides: 8.3A
- We inject: up to 40A peak (22.6A effective RMS)
- At zero-crossing: 45.9A combined vs 43.9A needed
- Current margin: +2.0A → **motor starts successfully**

### Recommendations by Unit Size

| Target Unit | Recommended Config | Cost | Confidence |
|-------------|-------------------|------|------------|
| 5000-6000 BTU | Budget (18SC+40E) | $199 | HIGH |
| **8000 BTU** | **Recommended (16SC+56E)** | **$224** | **MEDIUM** |
| 10000 BTU | Maximum (20SC+56E) | $248 | LOW |
| 12000+ BTU | Use EU2200i instead | - | - |

## Why Electrolytics Need Parallel Connection

Electrolytics are paralleled for two reasons:

### 1. Discharge Duration
```
Single 4700µF at 40A:
  dV/dt = 40A / 0.0047F = 8,511 V/s
  Time to discharge 60V: 7ms (way too short!)

28 × 4700µF at 40A:
  Time to discharge: 197ms ✓
```

### 2. Current Handling
```
Single 4700µF ripple current rating: ~3A
For 40A discharge: need 40A / 3A ≈ 14 caps minimum

We use 28 per bank for duration + current margin.
```

## Circuit Architecture

```
                        POSITIVE HALF-CYCLE BANK

AC Hot ────┬─────────────────────────────────────────────────┬──── Load
           │                                                 │
           │         CHARGING MODE                           │
           │    ┌────────────────────────┐                   │
           ├────┤ SW_sc_chg              │                   │
           │    │    ↓                   │                   │
           │    │ [Supercap Bank]        │                   │
           │    │   8S × 100F = 12.5F    │                   │
           │    │   @ 21.6V              │                   │
           │    └────────┬───────────────┘                   │
           │             │                                   │
           │    ┌────────┴───────────────┐                   │
           ├────┤ SW_el_chg              │                   │
           │    │    ↓                   │                   │
           │    │ [Electrolytic Bank]    │                   │
           │    │  28 × 4700µF = 0.13F   │                   │
           │    │   @ 60V                │                   │
           │    └────────────────────────┘                   │
           │                                                 │
           │         DISCHARGE MODE (SERIES)                 │
           │    ┌────────────────────────┐                   │
           │    │      [Supercap]        │                   │
           │    │         21.6V          │                   │
           │    │           +            │                   │
           │    │     [Electrolytic]     ├───[SW_discharge]──┤
           │    │         60V            │                   │
           │    │           =            │                   │
           │    │     81.6V stacked      │                   │
           │    └────────────────────────┘                   │
           │                                                 │
Neutral ───┴─────────────────────────────────────────────────┴──── Neutral

                    (Mirror for negative half-cycle bank)
```

### Operating Modes

**Charging (Normal Operation):**
1. Monitor V_ac continuously
2. When V_ac passes through ~22V: close SW_sc_chg briefly → supercaps charge
3. When V_ac passes through ~60V: close SW_el_chg briefly → electrolytics charge
4. Banks charge independently

**Discharging (Motor Start Assist):**
1. Detect motor start (current surge or voltage dip)
2. Reconfigure switches to connect banks in series
3. Close SW_discharge with PWM control when V_ac < 81.6V
4. Inject sinusoidal current synchronized to AC phase
5. After ~200ms, electrolytics depleted → falls back to supercap-only voltage

### Switching Requirements

| Switch | Voltage Rating | Current | Qty | Notes |
|--------|---------------|---------|-----|-------|
| SW_sc_chg | 50V | 20A | 2 | Supercap charging |
| SW_el_chg | 100V | 10A | 2 | Electrolytic charging |
| SW_discharge | 100V | 40A | 2 | Main power path |
| SW_series | 100V | 40A | 2 | Series connection |

## Bill of Materials

| Component | Spec | Qty | Unit | Total | Notes |
|-----------|------|-----|------|-------|-------|
| Supercapacitor | 100F 2.7V | 16 | $6.00 | $96 | 8S × 2 banks |
| Electrolytic | 4700µF 100V | 56 | $2.28 | $128 | 28 × 2 banks |
| MOSFET (charge) | 100V 20A | 4 | $1.00 | $4 | |
| MOSFET (discharge) | 100V 50A | 4 | $2.00 | $8 | IRFB4110 |
| Gate driver | IR2110 | 2 | $2.00 | $4 | |
| Current shunt | 0.01Ω 5W | 2 | $1.00 | $2 | |
| Inductor | 100µH 40A | 2 | $4.00 | $8 | PWM filtering |
| MCU | STM32F103 | 1 | $4.00 | $4 | |
| Voltage sensing | Dividers + opamp | 1 | $3.00 | $3 | |
| Connectors, fuses | Various | - | - | $15 | |
| PCB | JLCPCB 2-layer | 1 | $20.00 | $20 | ~150×200mm |
| **Total** | | | | **~$292** | |

### Alternative: Budget Build (18SC + 40E)

| Component | Qty | Cost |
|-----------|-----|------|
| Supercapacitors | 18 | $108 |
| Electrolytics | 40 | $91 |
| Electronics | - | ~$68 |
| **Total** | | **~$267** |

Delivers 162J in 200ms vs 206J for the recommended config.

## Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Input/Output | 120VAC 60Hz | Pass-through |
| Max continuous | 20A | |
| Stacked voltage | 81.6V | During boost |
| AC coverage | 32% | During boost |
| Boost duration | 197ms | Then supercap-only |
| Energy (200ms) | 206J | Critical window |
| Peak power | ~1,000W | During boost |
| Recovery time | ~60s | Full recharge |

## Comparison: Hybrid vs Supercap-Only

| Metric | Supercap Only (50SC) | Hybrid (16SC+56E) |
|--------|---------------------|-------------------|
| Cost | $300 | $224 |
| Voltage | 67.5V | 81.6V |
| Coverage | 26% | 32% |
| Energy/200ms | ~85J | 206J |
| Peak power | ~700W | ~1,000W |
| Complexity | Simple | Moderate |

**Hybrid delivers 2.4× more energy at 25% lower cost.**

## Firmware Architecture

### State Machine

```
                      ┌─────────┐
                      │  INIT   │
                      └────┬────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │          CHARGING               │
         │  - Monitor V_ac                 │
         │  - Charge supercaps at ~22V     │
         │  - Charge electrolytics at ~60V │
         └───────────────┬─────────────────┘
                         │ Both banks charged
                         ▼
                    ┌─────────┐
         ┌─────────│  READY  │←────────────┐
         │         └────┬────┘             │
         │              │ Motor start      │ Assist complete
         │              │ detected         │
         │              ▼                  │
         │    ┌──────────────────┐         │
         │    │     BOOST        │         │
         │    │  Series discharge│─────────┤
         │    │  @ 81.6V         │         │
         │    └────────┬─────────┘         │
         │             │ Electrolytics     │
         │             │ depleted          │
         │             ▼                   │
         │    ┌──────────────────┐         │
         └───→│   SUSTAIN        │─────────┘
              │  Supercap-only   │
              │  @ 21.6V         │
              └──────────────────┘
```

### Control Loop (20kHz)

```c
void control_loop(void) {
    float v_ac = sample_voltage();
    float i_load = sample_current();

    switch (state) {
        case CHARGING:
            // Charge supercaps when V_ac ~ 22V
            if (fabs(v_ac - 22.0) < 3.0 && v_supercap < 21.0) {
                enable_supercap_charge();
            }
            // Charge electrolytics when V_ac ~ 60V
            if (fabs(v_ac - 60.0) < 5.0 && v_elec < 58.0) {
                enable_electrolytic_charge();
            }
            // Check if ready
            if (v_supercap > 20.0 && v_elec > 55.0) {
                state = READY;
            }
            break;

        case READY:
            // Detect motor start
            if (i_load > I_THRESHOLD || detect_voltage_dip()) {
                configure_series_discharge();
                state = BOOST;
                boost_timer = 0;
            }
            break;

        case BOOST:
            // PWM discharge at stacked voltage
            if (fabs(v_ac) < v_supercap + v_elec) {
                float i_target = I_MAX * fabs(sin(phase));
                pwm_current_control(i_target);
            }
            // Check if electrolytics depleted
            if (v_elec < 10.0 || boost_timer > 300) {
                configure_supercap_only();
                state = SUSTAIN;
            }
            break;

        case SUSTAIN:
            // Continue with supercap-only
            if (fabs(v_ac) < v_supercap) {
                float i_target = I_MAX * fabs(sin(phase));
                pwm_current_control(i_target);
            }
            // Return to charging when assist complete
            if (assist_complete()) {
                state = CHARGING;
            }
            break;
    }
}
```

## Safety Features

### Hardware
- Input fuse: 25A fast-blow
- MOSFETs derated 2× for voltage and current
- Thermal shutdown via NTC on heatsink
- Current limiting via series inductor

### Firmware
- Overcurrent shutdown (>50A)
- Overvoltage lockout (supercap >24V, electrolytic >65V)
- Undervoltage lockout (supercap <15V)
- Assist timeout (5 second max)
- Watchdog timer

### Operational
- No backfeed capability (current source, not voltage source)
- Fail-safe: all switches open on fault
- Soft-start charging to limit inrush

## Development Roadmap

### Phase 1: Simulation ✓
- [x] Supercap-only analysis
- [x] Hybrid stacking concept
- [x] Cost optimization matrix
- [x] Energy delivery modeling
- [x] Motor startup requirements analysis
- [x] Phase alignment analysis (inductive load)
- [x] Comprehensive capability assessment

### Phase 2: Hardware Design
- [ ] Detailed schematic (KiCad)
- [ ] PCB layout with high-current paths
- [ ] Thermal analysis
- [ ] Component sourcing

### Phase 3: Firmware
- [ ] Zero-crossing detection
- [ ] Charge management
- [ ] Series/parallel reconfiguration
- [ ] PWM current control
- [ ] Protection features

### Phase 4: Prototype & Test
- [ ] PCB fabrication
- [ ] Assembly
- [ ] Bench testing
- [ ] Motor load testing

## Files

```
softstart/
├── README.md                           # This file
├── src/
│   ├── analyze_supercap_configs.py     # Supercap-only analysis
│   ├── analyze_hybrid_stacking.py      # Hybrid concept analysis
│   ├── optimize_minimal_hybrid.py      # Cost optimization
│   ├── analyze_motor_startup.py        # Motor startup requirements
│   ├── analyze_phase_coverage.py       # Phase alignment analysis
│   └── comprehensive_analysis.py       # Full capability analysis
├── supercap_analysis.png               # Supercap-only plots
├── hybrid_stacking_analysis.png        # Hybrid comparison plots
├── minimal_hybrid_optimization.png     # Cost optimization plots
├── motor_startup_analysis.png          # Motor startup plots
├── phase_coverage_analysis.png         # Phase alignment plots
└── comprehensive_analysis.png          # Capability matrix plots
```

## References

- Honda EU1000i specifications
- Maxwell/UCAP supercapacitor datasheets (100F 2.7V)
- Nichicon/Panasonic electrolytic capacitor datasheets
- IR2110 gate driver application notes
- Motor inrush current characteristics
- [EcoFlow battery/inverter matching guide](https://www.ecoflow.com/us/blog/battery-start-air-conditioner-guide)
- [HVAC School - Start capacitor and inrush](http://www.hvacrschool.com/start-capacitor-inrush-facts-myths-part-4/)
- [Ametherm - AC motor inrush current](https://www.ametherm.com/blog/inrush-current/ac-motor-inrush/)

## License

TBD
