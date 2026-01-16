# STM32G031F6P6 Pin Mapping

## Signal Assignments

| Pin | Port | Function | Signal | Description |
|-----|------|----------|--------|-------------|
| 7 | PA0 | GPIO/EXTI | ZC_OUT | Zero-crossing detector input |
| 8 | PA1 | ADC_IN1 | V_AC_SENSE | AC voltage sensing |
| 9 | PA2 | ADC_IN2 | V_SC_POS | Positive supercap bank voltage |
| 10 | PA3 | ADC_IN3 | V_SC_NEG | Negative supercap bank voltage |
| 11 | PA4 | ADC_IN4 | I_SENSE | Load current sensing |
| 12 | PA5 | GPIO | CHG_EN_POS | Positive bank charge enable |
| 13 | PA6 | TIM3_CH1 | PWM_POS | Positive half-cycle discharge PWM |
| 14 | PA7 | TIM3_CH2 | PWM_NEG | Negative half-cycle discharge PWM |
| 15 | PA8 | GPIO | CHG_EN_NEG | Negative bank charge enable |
| 16 | PA11 | GPIO | LED_STATUS | Status LED output |
| 18 | PA13 | SWD | SWDIO | Debug data |
| 19 | PA14 | SWD | SWCLK | Debug clock |
| 6 | PF2 | NRST | NRST | Reset (directly to header) |

## Power Pins

| Pin | Function | Connection |
|-----|----------|------------|
| 4 | VDD | 3.3V rail |
| 5 | VSS | Ground |

## Unused Pins

| Pin | Port | Notes |
|-----|------|-------|
| 1 | PB7/PB8 | Available for expansion |
| 2 | PB9/PC14 | Available for expansion |
| 3 | PC15 | Available for expansion |
| 17 | PA10/PA12 | Available for expansion |
| 20 | PB3-PB6 | Available for expansion |

## ADC Configuration

- ADC clock: 16 MHz (from PCLK/4)
- Resolution: 12-bit
- Sampling time: 12.5 cycles (for ~1 MHz sample rate)
- Channels: IN1, IN2, IN3, IN4 (scan mode)

## Timer Configuration

- TIM3: PWM generation for discharge MOSFETs
  - CH1 (PA6): PWM_POS
  - CH2 (PA7): PWM_NEG
  - Frequency: 20 kHz
  - Resolution: 10-bit (0-1000 duty)

## Interrupt Sources

- EXTI0 (PA0): Zero-crossing rising edge
- TIM3: PWM period interrupt for ADC trigger
- Systick: 1 kHz for state machine timing
