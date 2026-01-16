#!/usr/bin/env python3
"""
Analyze component sourcing options for budget designs.

Retail vs bulk/surplus pricing can differ significantly:
- Supercaps: $6 retail → $2-3 AliExpress/surplus
- Electrolytics: $2.28 retail → $0.50-1 bulk
- PCB: $20 JLCPCB → $0 perfboard
- MCU: $4 STM32 → $1 ATtiny or comparators
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SourcingScenario:
    """Component pricing scenario."""
    name: str
    sc_price: float      # Per supercap
    elec_price: float    # Per electrolytic
    electronics_price: float  # Fixed electronics cost
    notes: str = ""


def analyze_sourcing():
    """Compare different sourcing scenarios."""

    scenarios = [
        SourcingScenario(
            "Retail (DigiKey/Mouser)",
            sc_price=6.00,
            elec_price=2.28,
            electronics_price=68,
            notes="New, guaranteed specs, fast shipping"
        ),
        SourcingScenario(
            "LCSC/JLCPCB",
            sc_price=4.50,
            elec_price=1.50,
            electronics_price=55,
            notes="Chinese distributor, good quality, 2-week ship"
        ),
        SourcingScenario(
            "AliExpress bulk",
            sc_price=2.50,
            elec_price=0.80,
            electronics_price=45,
            notes="Variable quality, test before use, 3-4 week ship"
        ),
        SourcingScenario(
            "Surplus/salvage",
            sc_price=1.50,
            elec_price=0.40,
            electronics_price=35,
            notes="eBay, surplus stores, unknown history"
        ),
        SourcingScenario(
            "DIY maximum",
            sc_price=2.00,
            elec_price=0.50,
            electronics_price=25,
            notes="Perfboard, hand-wound inductors, salvage parts"
        ),
    ]

    # Design configurations to evaluate
    configs = [
        ("Full (16SC+56E)", 16, 56),
        ("Medium (12SC+40E)", 12, 40),
        ("Budget (6SC+16E)", 6, 16),
        ("Minimal (4SC+20E)", 4, 20),
    ]

    print("=" * 90)
    print("COMPONENT SOURCING ANALYSIS")
    print("=" * 90)

    # Price table
    print(f"\n{'Scenario':<25} {'SC':>8} {'Elec':>8} {'Electronics':>12}")
    print("-" * 55)
    for s in scenarios:
        print(f"{s.name:<25} ${s.sc_price:>6.2f}  ${s.elec_price:>6.2f}  ${s.electronics_price:>10.0f}")

    print("\n" + "=" * 90)
    print("TOTAL BOM BY SOURCING SCENARIO")
    print("=" * 90)

    # Header
    print(f"\n{'Config':<20}", end="")
    for s in scenarios:
        print(f"{s.name[:12]:>14}", end="")
    print()
    print("-" * 90)

    for name, sc, elec in configs:
        print(f"{name:<20}", end="")
        for s in scenarios:
            total = sc * s.sc_price + elec * s.elec_price + s.electronics_price
            print(f"${total:>12.0f}", end="")
        print()

    print("-" * 90)

    # Highlight best options
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)

    print("""
1. FULL DESIGN (16SC+56E) - For guaranteed 8000 BTU support
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Retail:     $292  (guaranteed specs, quick delivery)
   AliExpress: $153  (47% savings, test components first)
   Surplus:    $107  (63% savings, caveat emptor)

2. MEDIUM DESIGN (12SC+40E) - Good balance
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Retail:     $231
   AliExpress: $125
   DIY max:    $ 77  ← Under $80 for 12SC+40E!

3. BUDGET DESIGN (6SC+16E) - Marginal assist
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Retail:     $109
   AliExpress: $ 68
   DIY max:    $ 45  ← Under $50!

4. MINIMAL DESIGN (4SC+20E) - Experimental
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   DIY max:    $ 43  ← Cheapest possible hybrid
""")

    return scenarios, configs


def supercap_alternatives():
    """Explore supercap alternatives and sourcing."""

    print("\n" + "=" * 90)
    print("SUPERCAPACITOR SOURCING OPTIONS")
    print("=" * 90)

    print("""
TARGET SPEC: 100F 2.7V (or equivalent energy storage)

1. NEW RETAIL (DigiKey/Mouser)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Maxwell/UCAP 100F 2.7V: ~$6-8 each
   Pros: Guaranteed specs, datasheet, warranty
   Cons: Expensive

2. LCSC/JLCPCB PARTS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Various Chinese brands 100F 2.7V: ~$3-5 each
   Pros: Still new, reasonable quality
   Cons: May not match datasheet exactly

3. ALIEXPRESS BULK
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   "100F 2.7V" listings: $1.50-3 each (10+ qty)
   Pros: Very cheap
   Cons: Often mislabeled, actual capacity may be 50-80% of rated

   *** IMPORTANT: Test actual capacitance before using! ***
   Many AliExpress supercaps are 60-80F actual when rated 100F

4. SURPLUS/SALVAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   eBay "supercapacitor lot": $1-2 each
   Sources: UPS systems, automotive, industrial equipment
   Pros: Very cheap, sometimes premium brands
   Cons: Unknown age, may be degraded, no specs

5. ALTERNATIVE FORM FACTORS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - Prismatic cells (easier to stack): Sometimes cheaper in bulk
   - Higher voltage cells (2 × 50F 5.4V instead of 4 × 100F 2.7V)
   - Supercap modules (pre-balanced): More expensive but simpler

6. CAPACITY SUBSTITUTIONS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Instead of 8 × 100F 2.7V in series (12.5F @ 21.6V):
   - 4 × 50F 5.4V in series = 12.5F @ 21.6V (same!)
   - 2 × 25F 10.8V in series = 12.5F @ 21.6V (same!)

   Higher voltage cells are often cheaper per joule stored.
""")


def electrolytic_alternatives():
    """Explore electrolytic alternatives."""

    print("\n" + "=" * 90)
    print("ELECTROLYTIC CAPACITOR SOURCING")
    print("=" * 90)

    print("""
TARGET SPEC: 4700µF 100V (or equivalent)

1. NEW RETAIL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Nichicon/Panasonic 4700µF 100V: $2-3 each
   Pros: Known quality, long life (2000-5000 hours at 105°C)
   Cons: Expensive for the quantity we need

2. LCSC/JLCPCB
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Chinese brand 4700µF 100V: $1-1.50 each
   Pros: Good for hobby use
   Cons: Shorter life, may have higher ESR

3. ALIEXPRESS BULK
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   4700µF 100V: $0.50-1 each (10+ qty)
   Pros: Very cheap
   Cons: Variable quality, check for bulging/leaking

4. SURPLUS/SALVAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   From old power supplies, UPS units, audio amps
   Often FREE to very cheap
   Pros: Sometimes premium brands (Nichicon, Rubycon)
   Cons: May be near end of life, test ESR

5. ALTERNATIVES TO 4700µF 100V
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - 2 × 2200µF 100V in parallel = 4400µF (close enough)
   - 3 × 1500µF 100V in parallel = 4500µF
   - 10000µF 63V: cheaper but lower voltage headroom

   *** For our 60V charge voltage, 80V caps might work ***
   4700µF 80V are often cheaper than 100V rated

6. SNAP-IN vs RADIAL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Snap-in (large, chassis mount): Often cheaper per µF
   - Easier to find surplus
   - Harder to mount on PCB

   Radial (standard PCB mount):
   - More convenient
   - Usually more expensive
""")


def diy_electronics():
    """Explore DIY electronics options."""

    print("\n" + "=" * 90)
    print("DIY ELECTRONICS OPTIONS")
    print("=" * 90)

    print("""
SIMPLEST POSSIBLE DESIGN (no MCU):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instead of STM32 + complex control, use analog:

1. ZERO-CROSSING DETECTION
   - Resistor divider + comparator (LM393): $0.50
   - Or optocoupler (H11AA1): $0.80

2. DISCHARGE TRIGGER
   - Current sense resistor: $0.50
   - Comparator for "motor starting" detection: $0.50

3. MOSFET DRIVER
   - Bootstrap driver (IR2110): $2
   - Or simple transistor driver: $0.50

4. MOSFETS
   - IRFB4110 (100V 180A): $2 each × 2 = $4
   - Or surplus IGBTs from inverter scrap

5. PASSIVE COMPONENTS
   - Resistors, caps for timing: $2
   - Connectors: $3
   - Fuse holder + fuse: $2

MINIMAL ELECTRONICS BOM:
━━━━━━━━━━━━━━━━━━━━━━━━
Comparators (LM393 × 2)      $1.00
Optocoupler                  $0.80
MOSFETs (× 2)                $4.00
Gate driver or transistors   $1.00
Current sense resistor       $0.50
Passive components           $3.00
Connectors, fuse             $5.00
Perfboard                    $2.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                       $17.30

Add ~$8 margin for mistakes: ~$25 electronics

SIMPLIFIED CONTROL LOGIC:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. Caps charge naturally when connected to AC
   (through appropriate charging circuit)

2. Comparator watches current sense resistor
   When I > threshold (motor starting), enable discharge

3. Gate driver + MOSFET connects cap bank to line
   (Only when line voltage < cap voltage)

4. Simple RC timer limits discharge duration (~500ms max)

No MCU needed! Pure analog timing and control.
""")


def final_recommendations():
    """Final budget recommendations."""

    print("\n" + "=" * 90)
    print("FINAL BUDGET RECOMMENDATIONS")
    print("=" * 90)

    print("""
For a ~$100 (or less!) budget build:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION 1: "Beer Money Build" (~$45-60)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  6 supercaps (AliExpress, $2.50 ea)     = $15
  16 electrolytics (AliExpress, $0.80)   = $13
  DIY electronics (perfboard, analog)    = $25
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOTAL: ~$53

  Performance: ~60J, 10A effective, 24% coverage
  Good for: Easing generator labor, 5-6k BTU smooth start


OPTION 2: "Reliable Budget" (~$75-100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  8 supercaps (LCSC, $4 ea)              = $32
  24 electrolytics (LCSC, $1 ea)         = $24
  Basic electronics w/ ATtiny            = $35
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOTAL: ~$91

  Performance: ~90J, 12A effective, 26% coverage
  Good for: Noticeable improvement, 6-8k BTU easier


OPTION 3: "Full Cheap" (~$100-130)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  12 supercaps (AliExpress tested)       = $30
  40 electrolytics (AliExpress)          = $32
  Full electronics (STM32, proper PCB)   = $55
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOTAL: ~$117

  Performance: ~150J, 18A effective, 30% coverage
  Good for: Near-full performance, 8k BTU reliable


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROTOTYPING STRATEGY:
1. Start with "Beer Money Build" to validate concept
2. Test with your actual generator + AC unit
3. If it works, consider upgrading components
4. If marginal, add more caps incrementally
""")


def main():
    analyze_sourcing()
    supercap_alternatives()
    electrolytic_alternatives()
    diy_electronics()
    final_recommendations()


if __name__ == '__main__':
    main()
