/*
 * STM32G031 Startup Code
 * Minimal vector table and startup routine
 */

#include <stdint.h>

/* Linker symbols */
extern uint32_t _estack;
extern uint32_t _sidata;
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sbss;
extern uint32_t _ebss;

/* Main function */
extern int main(void);

/* Default handler for unused interrupts */
void Default_Handler(void) {
    while (1) {
        /* Hang on unexpected interrupt */
    }
}

/* Reset handler - entry point */
void Reset_Handler(void) {
    uint32_t *src, *dst;

    /* Copy initialized data from flash to RAM */
    src = &_sidata;
    dst = &_sdata;
    while (dst < &_edata) {
        *dst++ = *src++;
    }

    /* Zero-fill BSS section */
    dst = &_sbss;
    while (dst < &_ebss) {
        *dst++ = 0;
    }

    /* Call main */
    main();

    /* Should never reach here */
    while (1);
}

/* Weak aliases for interrupt handlers */
void NMI_Handler(void)              __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void)        __attribute__((weak, alias("Default_Handler")));
void SVC_Handler(void)              __attribute__((weak, alias("Default_Handler")));
void PendSV_Handler(void)           __attribute__((weak, alias("Default_Handler")));
void SysTick_Handler(void)          __attribute__((weak, alias("Default_Handler")));
void WWDG_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void PVD_IRQHandler(void)           __attribute__((weak, alias("Default_Handler")));
void RTC_TAMP_IRQHandler(void)      __attribute__((weak, alias("Default_Handler")));
void FLASH_IRQHandler(void)         __attribute__((weak, alias("Default_Handler")));
void RCC_IRQHandler(void)           __attribute__((weak, alias("Default_Handler")));
void EXTI0_1_IRQHandler(void)       __attribute__((weak, alias("Default_Handler")));
void EXTI2_3_IRQHandler(void)       __attribute__((weak, alias("Default_Handler")));
void EXTI4_15_IRQHandler(void)      __attribute__((weak, alias("Default_Handler")));
void DMA1_Channel1_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));
void DMA1_Channel2_3_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));
void DMA1_Channel4_5_6_7_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));
void ADC_IRQHandler(void)           __attribute__((weak, alias("Default_Handler")));
void TIM1_BRK_UP_TRG_COM_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));
void TIM1_CC_IRQHandler(void)       __attribute__((weak, alias("Default_Handler")));
void TIM2_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void TIM3_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void TIM14_IRQHandler(void)         __attribute__((weak, alias("Default_Handler")));
void TIM16_IRQHandler(void)         __attribute__((weak, alias("Default_Handler")));
void TIM17_IRQHandler(void)         __attribute__((weak, alias("Default_Handler")));
void I2C1_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void I2C2_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void SPI1_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void SPI2_IRQHandler(void)          __attribute__((weak, alias("Default_Handler")));
void USART1_IRQHandler(void)        __attribute__((weak, alias("Default_Handler")));
void USART2_IRQHandler(void)        __attribute__((weak, alias("Default_Handler")));
void LPUART1_IRQHandler(void)       __attribute__((weak, alias("Default_Handler")));

/* Vector table */
__attribute__((section(".isr_vector")))
const void *g_pfnVectors[] = {
    &_estack,                           /* Initial stack pointer */
    Reset_Handler,                      /* Reset handler */
    NMI_Handler,                        /* NMI handler */
    HardFault_Handler,                  /* Hard fault handler */
    0, 0, 0, 0, 0, 0, 0,               /* Reserved */
    SVC_Handler,                        /* SVC handler */
    0, 0,                               /* Reserved */
    PendSV_Handler,                     /* PendSV handler */
    SysTick_Handler,                    /* SysTick handler */

    /* External interrupts */
    WWDG_IRQHandler,                    /* 0: Window watchdog */
    PVD_IRQHandler,                     /* 1: PVD through EXTI */
    RTC_TAMP_IRQHandler,                /* 2: RTC through EXTI */
    FLASH_IRQHandler,                   /* 3: Flash */
    RCC_IRQHandler,                     /* 4: RCC */
    EXTI0_1_IRQHandler,                 /* 5: EXTI lines 0-1 */
    EXTI2_3_IRQHandler,                 /* 6: EXTI lines 2-3 */
    EXTI4_15_IRQHandler,                /* 7: EXTI lines 4-15 */
    0,                                  /* 8: Reserved */
    DMA1_Channel1_IRQHandler,           /* 9: DMA1 channel 1 */
    DMA1_Channel2_3_IRQHandler,         /* 10: DMA1 channels 2-3 */
    DMA1_Channel4_5_6_7_IRQHandler,     /* 11: DMA1 channels 4-7 */
    ADC_IRQHandler,                     /* 12: ADC */
    TIM1_BRK_UP_TRG_COM_IRQHandler,     /* 13: TIM1 break/update/trigger/com */
    TIM1_CC_IRQHandler,                 /* 14: TIM1 capture compare */
    TIM2_IRQHandler,                    /* 15: TIM2 */
    TIM3_IRQHandler,                    /* 16: TIM3 */
    0, 0,                               /* 17-18: Reserved */
    TIM14_IRQHandler,                   /* 19: TIM14 */
    0,                                  /* 20: Reserved */
    TIM16_IRQHandler,                   /* 21: TIM16 */
    TIM17_IRQHandler,                   /* 22: TIM17 */
    I2C1_IRQHandler,                    /* 23: I2C1 */
    I2C2_IRQHandler,                    /* 24: I2C2 */
    SPI1_IRQHandler,                    /* 25: SPI1 */
    SPI2_IRQHandler,                    /* 26: SPI2 */
    USART1_IRQHandler,                  /* 27: USART1 */
    USART2_IRQHandler,                  /* 28: USART2 */
    LPUART1_IRQHandler,                 /* 29: LPUART1 */
};
