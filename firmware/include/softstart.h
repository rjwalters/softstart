/*
 * Generator Soft-Start Firmware
 * Main Application Header
 */

#ifndef SOFTSTART_H
#define SOFTSTART_H

#include <stdint.h>
#include <stdbool.h>
#include "stm32g031.h"

/* System clock: 16 MHz HSI */
#define SYSCLK_FREQ     16000000UL
#define PWM_FREQ        20000       /* 20 kHz PWM */
#define PWM_PERIOD      (SYSCLK_FREQ / PWM_FREQ)  /* 800 counts */

/* Pin definitions (matching schematic) */
#define PIN_ZC_OUT          0   /* PA0 - Zero-crossing input */
#define PIN_V_AC_SENSE      1   /* PA1 - AC voltage ADC */
#define PIN_V_SC_POS        2   /* PA2 - Positive supercap voltage ADC */
#define PIN_V_SC_NEG        3   /* PA3 - Negative supercap voltage ADC */
#define PIN_I_SENSE         4   /* PA4 - Current sense ADC */
#define PIN_CHG_EN_POS      5   /* PA5 - Positive charge enable */
#define PIN_PWM_POS         6   /* PA6 - Positive discharge PWM (TIM3_CH1) */
#define PIN_PWM_NEG         7   /* PA7 - Negative discharge PWM (TIM3_CH2) */
#define PIN_CHG_EN_NEG      8   /* PA8 - Negative charge enable */
#define PIN_LED_STATUS      11  /* PA11 - Status LED */

/* ADC channels */
#define ADC_CH_V_AC         1
#define ADC_CH_V_SC_POS     2
#define ADC_CH_V_SC_NEG     3
#define ADC_CH_I_SENSE      4

/* Voltage/Current scaling
 * ADC: 12-bit, 3.3V reference
 * V_AC divider: 1M / 10k = 101:1, so 170Vpk -> 1.68V
 * V_SC divider: 820k / 10k = 83:1, so 81V -> 0.98V
 * I_SENSE: 5mR shunt * 50V/V gain = 0.25V/A
 */
#define ADC_VREF_MV         3300
#define ADC_MAX             4095

/* Voltage divider ratios (x100 for integer math) */
#define V_AC_RATIO          10100   /* 101:1 */
#define V_SC_RATIO          8300    /* 83:1 */

/* Current sense: 5mR * 50V/V = 250mV/A, so 1A = 310 ADC counts */
#define I_SENSE_COUNTS_PER_A    310

/* Protection limits */
#define V_AC_MIN_MV         100000  /* 100V RMS minimum */
#define V_AC_MAX_MV         140000  /* 140V RMS maximum */
#define V_SC_MAX_MV         85000   /* 85V supercap max */
#define I_LOAD_MAX_MA       40000   /* 40A peak current limit */

/* Timing constants (in ms) */
#define STARTUP_DETECT_MS   50      /* Time to detect motor startup */
#define BOOST_DURATION_MS   500     /* Maximum boost duration */
#define CHARGE_TIMEOUT_MS   120000  /* 2 minutes charge timeout */

/* State machine states */
typedef enum {
    STATE_INIT,
    STATE_IDLE,         /* Waiting for motor start */
    STATE_CHARGING,     /* Charging supercaps */
    STATE_READY,        /* Fully charged, waiting */
    STATE_BOOSTING,     /* Active discharge assist */
    STATE_COOLDOWN,     /* Post-boost cooldown */
    STATE_FAULT         /* Error condition */
} softstart_state_t;

/* Fault codes */
typedef enum {
    FAULT_NONE = 0,
    FAULT_OVERVOLTAGE,
    FAULT_UNDERVOLTAGE,
    FAULT_OVERCURRENT,
    FAULT_SUPERCAP_OV,
    FAULT_TIMEOUT
} fault_code_t;

/* ADC readings structure */
typedef struct {
    uint16_t v_ac;      /* AC voltage (peak, ADC counts) */
    uint16_t v_sc_pos;  /* Positive bank voltage */
    uint16_t v_sc_neg;  /* Negative bank voltage */
    uint16_t i_load;    /* Load current */
} adc_readings_t;

/* Global state */
extern volatile softstart_state_t g_state;
extern volatile fault_code_t g_fault;
extern volatile uint32_t g_systick_ms;
extern volatile bool g_zc_flag;
extern volatile bool g_zc_polarity;  /* true = positive half-cycle */
extern volatile adc_readings_t g_adc;

/* Function prototypes */

/* System initialization */
void system_init(void);
void gpio_init(void);
void adc_init(void);
void timer_init(void);
void exti_init(void);
void systick_init(void);

/* ADC functions */
void adc_start_conversion(void);
uint16_t adc_read_channel(uint8_t channel);
void adc_read_all(adc_readings_t *readings);

/* PWM control */
void pwm_set_pos(uint16_t duty);    /* 0-PWM_PERIOD */
void pwm_set_neg(uint16_t duty);
void pwm_disable(void);

/* Charging control */
void charge_enable_pos(bool enable);
void charge_enable_neg(bool enable);

/* LED control */
void led_set(bool on);
void led_toggle(void);

/* Utility functions */
uint32_t millis(void);
void delay_ms(uint32_t ms);

/* Voltage/current conversion */
uint32_t adc_to_voltage_mv(uint16_t adc_val, uint32_t ratio);
uint32_t adc_to_current_ma(uint16_t adc_val);

/* State machine */
void state_machine_run(void);
bool check_motor_start(void);
void enter_fault(fault_code_t code);

#endif /* SOFTSTART_H */
