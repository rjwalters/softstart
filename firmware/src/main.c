/*
 * Generator Soft-Start Firmware
 * Main Application
 *
 * Provides supplemental current during AC motor startup using
 * supercapacitor banks, synchronized to AC line phase.
 */

#include "softstart.h"

/* Global state variables */
volatile softstart_state_t g_state = STATE_INIT;
volatile fault_code_t g_fault = FAULT_NONE;
volatile uint32_t g_systick_ms = 0;
volatile bool g_zc_flag = false;
volatile bool g_zc_polarity = false;
volatile adc_readings_t g_adc = {0};

/* Local variables */
static uint32_t state_entry_time = 0;
static uint16_t boost_duty = 0;

/*
 * System Initialization
 */
void system_init(void) {
    /* Enable HSI (16 MHz internal oscillator) */
    RCC->CR |= RCC_CR_HSION;
    while (!(RCC->CR & RCC_CR_HSIRDY));

    /* Configure flash wait states for 16 MHz */
    /* (0 wait states for up to 24 MHz) */

    /* Enable GPIO clocks */
    RCC->IOPENR |= RCC_IOPENR_GPIOAEN | RCC_IOPENR_GPIOBEN;

    /* Enable peripheral clocks */
    RCC->APBENR1 |= RCC_APBENR1_TIM3EN;
    RCC->APBENR2 |= RCC_APBENR2_ADCEN | RCC_APBENR2_SYSCFGEN;
}

/*
 * GPIO Initialization
 */
void gpio_init(void) {
    /* PA0: Input (zero-crossing) with pull-down */
    GPIOA->MODER &= ~(3UL << (PIN_ZC_OUT * 2));      /* Input mode */
    GPIOA->PUPDR |= (2UL << (PIN_ZC_OUT * 2));      /* Pull-down */

    /* PA1-PA4: Analog inputs (ADC) */
    GPIOA->MODER |= (3UL << (PIN_V_AC_SENSE * 2));
    GPIOA->MODER |= (3UL << (PIN_V_SC_POS * 2));
    GPIOA->MODER |= (3UL << (PIN_V_SC_NEG * 2));
    GPIOA->MODER |= (3UL << (PIN_I_SENSE * 2));

    /* PA5, PA8: Output (charge enable) - start disabled */
    GPIOA->MODER &= ~(3UL << (PIN_CHG_EN_POS * 2));
    GPIOA->MODER |= (1UL << (PIN_CHG_EN_POS * 2));  /* Output */
    GPIOA->BSRR = (1UL << (PIN_CHG_EN_POS + 16));   /* Set low */

    GPIOA->MODER &= ~(3UL << (PIN_CHG_EN_NEG * 2));
    GPIOA->MODER |= (1UL << (PIN_CHG_EN_NEG * 2));  /* Output */
    GPIOA->BSRR = (1UL << (PIN_CHG_EN_NEG + 16));   /* Set low */

    /* PA6, PA7: Alternate function (TIM3 CH1/CH2 PWM) */
    GPIOA->MODER &= ~(3UL << (PIN_PWM_POS * 2));
    GPIOA->MODER |= (2UL << (PIN_PWM_POS * 2));     /* Alt function */
    GPIOA->AFRL &= ~(0xFUL << (PIN_PWM_POS * 4));
    GPIOA->AFRL |= (1UL << (PIN_PWM_POS * 4));      /* AF1 = TIM3 */

    GPIOA->MODER &= ~(3UL << (PIN_PWM_NEG * 2));
    GPIOA->MODER |= (2UL << (PIN_PWM_NEG * 2));     /* Alt function */
    GPIOA->AFRL &= ~(0xFUL << (PIN_PWM_NEG * 4));
    GPIOA->AFRL |= (1UL << (PIN_PWM_NEG * 4));      /* AF1 = TIM3 */

    /* PA11: Output (LED) - start off */
    GPIOA->MODER &= ~(3UL << (PIN_LED_STATUS * 2));
    GPIOA->MODER |= (1UL << (PIN_LED_STATUS * 2));  /* Output */
    GPIOA->BSRR = (1UL << (PIN_LED_STATUS + 16));   /* Set low */
}

/*
 * ADC Initialization
 */
void adc_init(void) {
    /* Ensure ADC is disabled */
    if (ADC1->CR & ADC_CR_ADEN) {
        ADC1->CR |= ADC_CR_ADDIS;
        while (ADC1->CR & ADC_CR_ADEN);
    }

    /* Configure ADC clock (PCLK/4 = 4 MHz) */
    ADC1->CFGR2 = (2UL << 30);  /* PCLK/4 */

    /* Calibrate ADC */
    ADC1->CR |= ADC_CR_ADCAL;
    while (ADC1->CR & ADC_CR_ADCAL);

    /* Configure sampling time (12.5 cycles for all channels) */
    ADC1->SMPR = (2UL << 0);  /* 12.5 cycles */

    /* Enable ADC voltage regulator (if present) */
    /* Wait for stabilization */
    for (volatile int i = 0; i < 1000; i++);

    /* Enable ADC */
    ADC1->ISR |= ADC_ISR_ADRDY;  /* Clear ready flag */
    ADC1->CR |= ADC_CR_ADEN;
    while (!(ADC1->ISR & ADC_ISR_ADRDY));

    /* Configure for single conversion, right-aligned */
    ADC1->CFGR1 = 0;
}

/*
 * Timer Initialization (PWM)
 */
void timer_init(void) {
    /* TIM3: 20 kHz PWM on CH1 and CH2 */

    /* Set prescaler and period for 20 kHz */
    TIM3->PSC = 0;                      /* No prescaler */
    TIM3->ARR = PWM_PERIOD - 1;         /* Auto-reload value */

    /* Configure CH1 and CH2 for PWM mode 1 */
    TIM3->CCMR1 = TIM_CCMR1_OC1M_PWM1 | TIM_CCMR1_OC1PE |
                  TIM_CCMR1_OC2M_PWM1 | TIM_CCMR1_OC2PE;

    /* Set initial duty cycle to 0 */
    TIM3->CCR1 = 0;
    TIM3->CCR2 = 0;

    /* Enable CH1 and CH2 outputs */
    TIM3->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E;

    /* Enable auto-reload preload */
    TIM3->CR1 = TIM_CR1_ARPE;

    /* Generate update event to load registers */
    TIM3->EGR = TIM_EGR_UG;

    /* Enable timer */
    TIM3->CR1 |= TIM_CR1_CEN;
}

/*
 * EXTI Initialization (Zero-crossing interrupt)
 */
void exti_init(void) {
    /* Configure EXTI line 0 for PA0 */
    /* On STM32G0, EXTICR is in EXTI peripheral, not SYSCFG */
    EXTI->EXTICR[0] = 0;  /* PA0 as EXTI0 source */

    /* Enable rising edge trigger for EXTI0 */
    EXTI->RTSR1 |= (1UL << 0);
    EXTI->FTSR1 &= ~(1UL << 0);

    /* Enable EXTI0 interrupt mask */
    EXTI->IMR1 |= (1UL << 0);

    /* Enable EXTI0_1 interrupt in NVIC */
    *NVIC_ISER |= (1UL << EXTI0_1_IRQn);
}

/*
 * SysTick Initialization (1ms tick)
 */
void systick_init(void) {
    *SYSTICK_LOAD = (SYSCLK_FREQ / 1000) - 1;  /* 1ms period */
    *SYSTICK_VAL = 0;
    *SYSTICK_CTRL = SYSTICK_CTRL_ENABLE | SYSTICK_CTRL_TICKINT |
                    SYSTICK_CTRL_CLKSOURCE;
}

/*
 * SysTick Interrupt Handler
 */
void SysTick_Handler(void) {
    g_systick_ms++;
}

/*
 * EXTI0_1 Interrupt Handler (Zero-crossing)
 */
void EXTI0_1_IRQHandler(void) {
    if (EXTI->RPR1 & (1UL << 0)) {
        /* Rising edge detected */
        EXTI->RPR1 = (1UL << 0);  /* Clear pending flag */

        g_zc_flag = true;
        g_zc_polarity = !g_zc_polarity;  /* Toggle polarity */
    }
}

/*
 * Millisecond counter
 */
uint32_t millis(void) {
    return g_systick_ms;
}

/*
 * Delay in milliseconds
 */
void delay_ms(uint32_t ms) {
    uint32_t start = g_systick_ms;
    while ((g_systick_ms - start) < ms);
}

/*
 * ADC single channel read
 */
uint16_t adc_read_channel(uint8_t channel) {
    /* Select channel */
    ADC1->CHSELR = (1UL << channel);

    /* Start conversion */
    ADC1->CR |= ADC_CR_ADSTART;

    /* Wait for conversion complete */
    while (!(ADC1->ISR & ADC_ISR_EOC));

    /* Return result */
    return (uint16_t)ADC1->DR;
}

/*
 * Read all ADC channels
 */
void adc_read_all(adc_readings_t *readings) {
    readings->v_ac = adc_read_channel(ADC_CH_V_AC);
    readings->v_sc_pos = adc_read_channel(ADC_CH_V_SC_POS);
    readings->v_sc_neg = adc_read_channel(ADC_CH_V_SC_NEG);
    readings->i_load = adc_read_channel(ADC_CH_I_SENSE);
}

/*
 * Set positive bank PWM duty cycle
 */
void pwm_set_pos(uint16_t duty) {
    if (duty > PWM_PERIOD) duty = PWM_PERIOD;
    TIM3->CCR1 = duty;
}

/*
 * Set negative bank PWM duty cycle
 */
void pwm_set_neg(uint16_t duty) {
    if (duty > PWM_PERIOD) duty = PWM_PERIOD;
    TIM3->CCR2 = duty;
}

/*
 * Disable all PWM outputs
 */
void pwm_disable(void) {
    TIM3->CCR1 = 0;
    TIM3->CCR2 = 0;
}

/*
 * Enable/disable positive bank charging
 */
void charge_enable_pos(bool enable) {
    if (enable) {
        GPIOA->BSRR = (1UL << PIN_CHG_EN_POS);
    } else {
        GPIOA->BSRR = (1UL << (PIN_CHG_EN_POS + 16));
    }
}

/*
 * Enable/disable negative bank charging
 */
void charge_enable_neg(bool enable) {
    if (enable) {
        GPIOA->BSRR = (1UL << PIN_CHG_EN_NEG);
    } else {
        GPIOA->BSRR = (1UL << (PIN_CHG_EN_NEG + 16));
    }
}

/*
 * Set LED state
 */
void led_set(bool on) {
    if (on) {
        GPIOA->BSRR = (1UL << PIN_LED_STATUS);
    } else {
        GPIOA->BSRR = (1UL << (PIN_LED_STATUS + 16));
    }
}

/*
 * Toggle LED
 */
void led_toggle(void) {
    GPIOA->ODR ^= (1UL << PIN_LED_STATUS);
}

/*
 * Convert ADC reading to voltage in mV
 */
uint32_t adc_to_voltage_mv(uint16_t adc_val, uint32_t ratio) {
    /* voltage = adc * vref / 4096 * ratio / 100 */
    uint32_t mv = ((uint32_t)adc_val * ADC_VREF_MV * ratio) / (ADC_MAX * 100);
    return mv;
}

/*
 * Convert ADC reading to current in mA
 */
uint32_t adc_to_current_ma(uint16_t adc_val) {
    /* current = adc * 1000 / 310 */
    return ((uint32_t)adc_val * 1000) / I_SENSE_COUNTS_PER_A;
}

/*
 * Enter fault state
 */
void enter_fault(fault_code_t code) {
    g_fault = code;
    g_state = STATE_FAULT;

    /* Disable all outputs */
    pwm_disable();
    charge_enable_pos(false);
    charge_enable_neg(false);
}

/*
 * Check if motor startup detected
 * Returns true if current draw indicates motor starting
 */
bool check_motor_start(void) {
    /* Motor startup indicated by current spike above threshold */
    uint32_t current_ma = adc_to_current_ma(g_adc.i_load);
    return (current_ma > 5000);  /* > 5A indicates startup */
}

/*
 * Check if supercaps are fully charged
 */
static bool supercaps_charged(void) {
    uint32_t v_pos = adc_to_voltage_mv(g_adc.v_sc_pos, V_SC_RATIO);
    uint32_t v_neg = adc_to_voltage_mv(g_adc.v_sc_neg, V_SC_RATIO);

    /* Consider charged if both banks > 75V */
    return (v_pos > 75000 && v_neg > 75000);
}

/*
 * Check safety limits
 */
static bool check_safety(void) {
    uint32_t v_ac = adc_to_voltage_mv(g_adc.v_ac, V_AC_RATIO);
    uint32_t v_pos = adc_to_voltage_mv(g_adc.v_sc_pos, V_SC_RATIO);
    uint32_t v_neg = adc_to_voltage_mv(g_adc.v_sc_neg, V_SC_RATIO);
    uint32_t i_load = adc_to_current_ma(g_adc.i_load);

    /* Check AC voltage range */
    if (v_ac < 90000) {  /* Below ~90V peak */
        enter_fault(FAULT_UNDERVOLTAGE);
        return false;
    }
    if (v_ac > 200000) {  /* Above ~200V peak */
        enter_fault(FAULT_OVERVOLTAGE);
        return false;
    }

    /* Check supercap overvoltage */
    if (v_pos > V_SC_MAX_MV || v_neg > V_SC_MAX_MV) {
        enter_fault(FAULT_SUPERCAP_OV);
        return false;
    }

    /* Check overcurrent */
    if (i_load > I_LOAD_MAX_MA) {
        enter_fault(FAULT_OVERCURRENT);
        return false;
    }

    return true;
}

/*
 * Main state machine
 */
void state_machine_run(void) {
    uint32_t now = millis();

    /* Read ADC values */
    adc_read_all((adc_readings_t *)&g_adc);

    /* Check safety limits (except in fault state) */
    if (g_state != STATE_FAULT && g_state != STATE_INIT) {
        if (!check_safety()) {
            return;
        }
    }

    switch (g_state) {
        case STATE_INIT:
            /* Initialization complete, go to charging */
            g_state = STATE_CHARGING;
            state_entry_time = now;
            led_set(false);
            break;

        case STATE_CHARGING:
            /* Enable charging for both banks */
            charge_enable_pos(true);
            charge_enable_neg(true);

            /* Blink LED slowly while charging */
            if ((now / 500) & 1) {
                led_set(true);
            } else {
                led_set(false);
            }

            /* Check if fully charged */
            if (supercaps_charged()) {
                g_state = STATE_READY;
                state_entry_time = now;
            }

            /* Timeout check */
            if ((now - state_entry_time) > CHARGE_TIMEOUT_MS) {
                enter_fault(FAULT_TIMEOUT);
            }
            break;

        case STATE_READY:
            /* Keep charging to maintain voltage */
            charge_enable_pos(true);
            charge_enable_neg(true);

            /* Solid LED when ready */
            led_set(true);

            /* Check for motor start */
            if (check_motor_start()) {
                g_state = STATE_BOOSTING;
                state_entry_time = now;
                boost_duty = PWM_PERIOD / 2;  /* Start at 50% duty */

                /* Disable charging during boost */
                charge_enable_pos(false);
                charge_enable_neg(false);
            }
            break;

        case STATE_BOOSTING:
            /* Active discharge assist */
            /* Apply PWM based on AC phase */
            if (g_zc_flag) {
                g_zc_flag = false;

                /* Ramp up PWM over first few cycles */
                if (boost_duty < PWM_PERIOD * 8 / 10) {
                    boost_duty += PWM_PERIOD / 20;
                }
            }

            /* Apply appropriate PWM based on polarity */
            if (g_zc_polarity) {
                pwm_set_pos(boost_duty);
                pwm_set_neg(0);
            } else {
                pwm_set_pos(0);
                pwm_set_neg(boost_duty);
            }

            /* Fast LED blink during boost */
            led_set((now / 50) & 1);

            /* Check if boost duration exceeded */
            if ((now - state_entry_time) > BOOST_DURATION_MS) {
                g_state = STATE_COOLDOWN;
                state_entry_time = now;
                pwm_disable();
            }

            /* Check if motor has started (current dropped) */
            if (!check_motor_start() && (now - state_entry_time) > STARTUP_DETECT_MS) {
                g_state = STATE_COOLDOWN;
                state_entry_time = now;
                pwm_disable();
            }
            break;

        case STATE_COOLDOWN:
            /* Brief cooldown before returning to charging */
            pwm_disable();
            led_set(false);

            if ((now - state_entry_time) > 1000) {
                g_state = STATE_CHARGING;
                state_entry_time = now;
            }
            break;

        case STATE_FAULT:
            /* All outputs disabled, fast LED blink */
            pwm_disable();
            charge_enable_pos(false);
            charge_enable_neg(false);

            /* Blink pattern indicates fault code */
            led_set(((now / 200) % (g_fault + 1)) == 0);
            break;

        case STATE_IDLE:
        default:
            /* Idle state - outputs disabled, waiting */
            pwm_disable();
            charge_enable_pos(false);
            charge_enable_neg(false);
            led_set(false);
            break;
    }
}

/*
 * Main entry point
 */
int main(void) {
    /* Initialize peripherals */
    system_init();
    gpio_init();
    adc_init();
    timer_init();
    exti_init();
    systick_init();

    /* Main loop */
    while (1) {
        state_machine_run();

        /* Small delay to limit loop rate */
        delay_ms(1);
    }

    return 0;
}
