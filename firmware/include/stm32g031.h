/*
 * STM32G031 Register Definitions (Minimal)
 * Generator Soft-Start Project
 */

#ifndef STM32G031_H
#define STM32G031_H

#include <stdint.h>

/* Base addresses */
#define FLASH_BASE      0x08000000UL
#define SRAM_BASE       0x20000000UL
#define PERIPH_BASE     0x40000000UL

#define APB1_BASE       (PERIPH_BASE)
#define APB2_BASE       (PERIPH_BASE + 0x00010000UL)
#define AHB_BASE        (PERIPH_BASE + 0x00020000UL)

/* Peripheral base addresses */
#define TIM3_BASE       (APB1_BASE + 0x0400UL)
#define RCC_BASE        (AHB_BASE + 0x1000UL)
#define FLASH_R_BASE    (AHB_BASE + 0x2000UL)
#define PWR_BASE        (APB1_BASE + 0x7000UL)
#define EXTI_BASE       (APB2_BASE + 0x0400UL)
#define ADC_BASE        (APB2_BASE + 0x2400UL)
#define SYSCFG_BASE     (APB2_BASE + 0x0000UL)

#define GPIOA_BASE      (AHB_BASE + 0x0000UL)
#define GPIOB_BASE      (AHB_BASE + 0x0400UL)
#define GPIOC_BASE      (AHB_BASE + 0x0800UL)
#define GPIOF_BASE      (AHB_BASE + 0x1400UL)

/* RCC Registers */
typedef struct {
    volatile uint32_t CR;
    volatile uint32_t ICSCR;
    volatile uint32_t CFGR;
    volatile uint32_t PLLCFGR;
    volatile uint32_t RESERVED0;
    volatile uint32_t RESERVED1;
    volatile uint32_t CIER;
    volatile uint32_t CIFR;
    volatile uint32_t CICR;
    volatile uint32_t IOPRSTR;
    volatile uint32_t AHBRSTR;
    volatile uint32_t APBRSTR1;
    volatile uint32_t APBRSTR2;
    volatile uint32_t IOPENR;
    volatile uint32_t AHBENR;
    volatile uint32_t APBENR1;
    volatile uint32_t APBENR2;
    volatile uint32_t IOPSMENR;
    volatile uint32_t AHBSMENR;
    volatile uint32_t APBSMENR1;
    volatile uint32_t APBSMENR2;
    volatile uint32_t CCIPR;
    volatile uint32_t RESERVED2;
    volatile uint32_t BDCR;
    volatile uint32_t CSR;
} RCC_TypeDef;

/* GPIO Registers */
typedef struct {
    volatile uint32_t MODER;
    volatile uint32_t OTYPER;
    volatile uint32_t OSPEEDR;
    volatile uint32_t PUPDR;
    volatile uint32_t IDR;
    volatile uint32_t ODR;
    volatile uint32_t BSRR;
    volatile uint32_t LCKR;
    volatile uint32_t AFRL;
    volatile uint32_t AFRH;
    volatile uint32_t BRR;
} GPIO_TypeDef;

/* ADC Registers */
typedef struct {
    volatile uint32_t ISR;
    volatile uint32_t IER;
    volatile uint32_t CR;
    volatile uint32_t CFGR1;
    volatile uint32_t CFGR2;
    volatile uint32_t SMPR;
    volatile uint32_t RESERVED0;
    volatile uint32_t RESERVED1;
    volatile uint32_t AWD1TR;
    volatile uint32_t AWD2TR;
    volatile uint32_t CHSELR;
    volatile uint32_t AWD3TR;
    volatile uint32_t RESERVED2[4];
    volatile uint32_t DR;
    volatile uint32_t RESERVED3[23];
    volatile uint32_t AWD2CR;
    volatile uint32_t AWD3CR;
    volatile uint32_t RESERVED4[3];
    volatile uint32_t CALFACT;
    volatile uint32_t RESERVED5[148];
    volatile uint32_t CCR;
} ADC_TypeDef;

/* Timer Registers */
typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMCR;
    volatile uint32_t DIER;
    volatile uint32_t SR;
    volatile uint32_t EGR;
    volatile uint32_t CCMR1;
    volatile uint32_t CCMR2;
    volatile uint32_t CCER;
    volatile uint32_t CNT;
    volatile uint32_t PSC;
    volatile uint32_t ARR;
    volatile uint32_t RESERVED0;
    volatile uint32_t CCR1;
    volatile uint32_t CCR2;
    volatile uint32_t CCR3;
    volatile uint32_t CCR4;
    volatile uint32_t RESERVED1;
    volatile uint32_t DCR;
    volatile uint32_t DMAR;
    volatile uint32_t OR1;
    volatile uint32_t RESERVED2[3];
    volatile uint32_t AF1;
    volatile uint32_t RESERVED3;
    volatile uint32_t TISEL;
} TIM_TypeDef;

/* EXTI Registers */
typedef struct {
    volatile uint32_t RTSR1;
    volatile uint32_t FTSR1;
    volatile uint32_t SWIER1;
    volatile uint32_t RPR1;
    volatile uint32_t FPR1;
    volatile uint32_t RESERVED0[19];
    volatile uint32_t EXTICR[4];
    volatile uint32_t RESERVED1[4];
    volatile uint32_t IMR1;
    volatile uint32_t EMR1;
} EXTI_TypeDef;

/* SYSCFG Registers */
typedef struct {
    volatile uint32_t CFGR1;
    volatile uint32_t RESERVED0[5];
    volatile uint32_t CFGR2;
    volatile uint32_t RESERVED1[25];
    volatile uint32_t ITLINE[32];
} SYSCFG_TypeDef;

/* Peripheral pointers */
#define RCC         ((RCC_TypeDef *)RCC_BASE)
#define GPIOA       ((GPIO_TypeDef *)GPIOA_BASE)
#define GPIOB       ((GPIO_TypeDef *)GPIOB_BASE)
#define GPIOC       ((GPIO_TypeDef *)GPIOC_BASE)
#define GPIOF       ((GPIO_TypeDef *)GPIOF_BASE)
#define ADC1        ((ADC_TypeDef *)ADC_BASE)
#define TIM3        ((TIM_TypeDef *)TIM3_BASE)
#define EXTI        ((EXTI_TypeDef *)EXTI_BASE)
#define SYSCFG      ((SYSCFG_TypeDef *)SYSCFG_BASE)

/* RCC bit definitions */
#define RCC_CR_HSION            (1UL << 8)
#define RCC_CR_HSIRDY           (1UL << 10)

#define RCC_IOPENR_GPIOAEN      (1UL << 0)
#define RCC_IOPENR_GPIOBEN      (1UL << 1)
#define RCC_IOPENR_GPIOCEN      (1UL << 2)
#define RCC_IOPENR_GPIOFEN      (1UL << 5)

#define RCC_APBENR1_TIM3EN      (1UL << 1)
#define RCC_APBENR2_ADCEN       (1UL << 20)
#define RCC_APBENR2_SYSCFGEN    (1UL << 0)

/* GPIO mode definitions */
#define GPIO_MODE_INPUT         0x00
#define GPIO_MODE_OUTPUT        0x01
#define GPIO_MODE_ALTFN         0x02
#define GPIO_MODE_ANALOG        0x03

/* ADC bit definitions */
#define ADC_ISR_ADRDY           (1UL << 0)
#define ADC_ISR_EOC             (1UL << 2)
#define ADC_ISR_EOS             (1UL << 3)
#define ADC_CR_ADEN             (1UL << 0)
#define ADC_CR_ADDIS            (1UL << 1)
#define ADC_CR_ADSTART          (1UL << 2)
#define ADC_CR_ADCAL            (1UL << 31)
#define ADC_CFGR1_CONT          (1UL << 13)
#define ADC_CFGR1_SCANDIR       (1UL << 2)

/* Timer bit definitions */
#define TIM_CR1_CEN             (1UL << 0)
#define TIM_CR1_ARPE            (1UL << 7)
#define TIM_CCMR1_OC1M_PWM1     (0x06UL << 4)
#define TIM_CCMR1_OC2M_PWM1     (0x06UL << 12)
#define TIM_CCMR1_OC1PE         (1UL << 3)
#define TIM_CCMR1_OC2PE         (1UL << 11)
#define TIM_CCER_CC1E           (1UL << 0)
#define TIM_CCER_CC2E           (1UL << 4)
#define TIM_EGR_UG              (1UL << 0)

/* NVIC */
#define NVIC_ISER               ((volatile uint32_t *)0xE000E100UL)
#define NVIC_ICER               ((volatile uint32_t *)0xE000E180UL)
#define NVIC_ISPR               ((volatile uint32_t *)0xE000E200UL)
#define NVIC_ICPR               ((volatile uint32_t *)0xE000E280UL)
#define NVIC_IPR                ((volatile uint32_t *)0xE000E400UL)

/* SysTick */
#define SYSTICK_CTRL            ((volatile uint32_t *)0xE000E010UL)
#define SYSTICK_LOAD            ((volatile uint32_t *)0xE000E014UL)
#define SYSTICK_VAL             ((volatile uint32_t *)0xE000E018UL)

#define SYSTICK_CTRL_ENABLE     (1UL << 0)
#define SYSTICK_CTRL_TICKINT    (1UL << 1)
#define SYSTICK_CTRL_CLKSOURCE  (1UL << 2)

/* IRQ numbers for STM32G031 */
#define EXTI0_1_IRQn            5
#define EXTI2_3_IRQn            6
#define EXTI4_15_IRQn           7
#define ADC_IRQn                12
#define TIM3_IRQn               16

#endif /* STM32G031_H */
