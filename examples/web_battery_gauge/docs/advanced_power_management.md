# Advanced Battery Monitoring for Ultra-Low Power Applications

*Part of the picowicd Web Battery Fuel Gauge Example*

## When to Use Advanced Power Management

The simple voltage divider approach (100kΩ + 100kΩ resistors) draws ~21µA continuously. While this provides **10+ years** of battery life for most applications, optimization becomes critical in specific scenarios:

### Optimization Required When:
- **Ultra-low power systems** with total consumption <50µA
- **Long-term deployments** requiring >2 years unattended operation
- **Small batteries** (CR2032 ≤200mAh) where 21µA reduces life from 5+ years to ~1 year
- **Systems spending >90% time in deep sleep** where divider becomes dominant power drain

### Keep Simple Voltage Divider When:
- Battery capacity >1000mAh (AA/AAA size or larger)
- Project lifespan <2 years
- System already draws >100µA during operation
- Educational/prototyping applications

## Evidence-Based Advanced Design

> **⚠️ Experimental Design Notice**  
> This design is evidence-based from industry research but **untested** in this specific configuration. Provided as a starting point for advanced applications requiring battery optimization.

### FET-Switched Voltage Divider

**Theory:** Use P-FET on high side to completely disconnect voltage divider when not measuring, reducing current draw from 21µA to <1nA leakage.

```
Battery+ ─── P-FET ─── R1(100kΩ) ─── ADC Pin ─── R2(100kΩ) ─── GND
              │
         NPN Transistor
              │
         GPIO Control Pin
```

### Component Selection (Research-Based)

**P-Channel MOSFET:**
- **BS250** or **IRLML6402** (low threshold voltage)
- Key specs: Vgs(th) <-1.5V, leakage <1nA at room temperature
- Must be "logic level" compatible for 3.3V gate drive

**NPN Transistor:**
- **2N2222** or **BC547** (common, low-cost)
- Base resistor: 10kΩ from GPIO to base
- Provides voltage inversion and current gain

**Additional Components:**
- 100kΩ gate pull-up resistor (ensures P-FET stays off when GPIO floating)
- Optional: 10nF capacitor across R2 for noise filtering

### Control Logic

```python
# Enable battery measurement
def read_battery_voltage():
    battery_enable_pin.value(1)    # Turn on NPN → P-FET on
    time.sleep_ms(10)              # Allow voltage to settle
    voltage = adc.read_u16() * 3.3 / 65535 * 2  # Read and scale
    battery_enable_pin.value(0)    # Disable divider
    return voltage

# Periodic monitoring
async def battery_monitor():
    while True:
        voltage = read_battery_voltage()
        log_battery_data(voltage)
        await asyncio.sleep(600)   # Check every 10 minutes
```

### Expected Performance

**Current Draw Comparison:**
- **Simple divider**: 21µA continuous
- **FET-switched**: <1nA when disabled + measurement overhead
- **Duty cycle**: 10ms every 10 minutes = 0.0017%
- **Effective current**: ~0.0003µA average

**Battery Life Impact:**
- **CR2032 (200mAh)**: 1 year → 50+ years (limited by self-discharge)
- **AAA (1000mAh)**: 10 years → 100+ years (academic improvement)

## Implementation Considerations

### GPIO Requirements
- **1 additional digital output** for P-FET control
- Pin must be configured with pull-down when MCU in sleep mode
- Consider using pin that can wake MCU for scheduled measurements

### Timing Considerations
- **Settling time**: 10ms minimum after enabling divider
- **ADC sampling**: Take multiple readings and average for accuracy
- **Disable quickly**: Minimize on-time to reduce average current

### Temperature Effects
- **MOSFET leakage** increases exponentially with temperature
- **Resistor tolerance** affects accuracy more than power consumption
- Consider temperature compensation for precision applications

### Alternative Approaches

**Option 1: GPIO-Driven Ground**
- Use GPIO pin directly as voltage divider ground
- Simpler but limited by MCU pin drive capability
- Works only if battery voltage < MCU VCC

**Option 2: High-Value Resistors + Buffer**
- Use 1MΩ resistors (reduces to 4.2µA)
- Add low-power op-amp buffer for ADC drive
- More components but potentially more accurate

**Option 3: Measurement-Only Wake**
- Enable divider only during scheduled wake events
- Use RTC wake or external trigger
- Combines power savings with operational simplicity

## Design Validation Steps

1. **Breadboard Testing**
   - Verify P-FET switching with GPIO control
   - Measure actual leakage current with picoammeter
   - Test across temperature range if critical

2. **Long-Term Validation**
   - Monitor battery voltage over weeks/months
   - Compare against known-good multimeter readings
   - Document any drift or calibration needs

3. **System Integration**
   - Ensure proper MCU pin configuration during sleep
   - Test wake-up reliability and measurement accuracy
   - Validate total system power consumption

## Conclusion

Advanced battery monitoring adds significant complexity for relatively small gains in most applications. The FET-switched approach is theoretically sound and widely used in commercial ultra-low-power devices, but requires careful implementation and testing.

**Recommendation**: Start with simple voltage divider for prototyping, then implement advanced design only if battery life testing demonstrates actual need for optimization.

---

*This design is based on industry best practices and published research but has not been validated in this specific configuration. Use as starting point for advanced applications requiring verified ultra-low power operation.*