# P59 OS 12587603 — Calibration Address Map

> Extracted from LegacyNsfw 4,796-entry CSV — key entries for tuning

## AIRFLOW (45 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KA_EGR_AIR_FLOW` | 0x008110 | Grams Per Second | EGR air flow through the EGR valve. |
| `KE_EGR_AIR_FLOW_FILT_COEF` | 0x0081D6 | NONE 0-1 | The calculated EGRflow for Dyna-Air will be filtered using this coefficient. |
| `KE_EGR_DUTY_CYCLE_DYNAAIR` | 0x0081D8 | Percent | The commanded EGR duty cycle must be at least this value to enable calculation of EGR air mass. |
| `KE_VE_TEMPERATURE` | 0x0081DA | sqrt deg K | $000043BF |
| `KV_VOLUMETRIC_EFFICIENCY_BARO_CO` | 0x0081DC | NONE 0-2 | $000043C2 |
| `KA_VOLUMETRIC_EFFICIENCY_CRANK` | 0x0081F0 | Percent | Volumetric efficiency at cranking speeds. |
| `K_MAIN_VOLUMETRIC_EFFICIENCY` | 0x008442 | gm*K/kPa | The volumetric efficiency term used for modeling the air per cylinder for Dyna-Air calculations. |
| `KV_GAMMA_INIT_COOLANT_BREAKPOINT` | 0x00873A | Deg C | Breakpoints for selection coolant zone for initializing Filtered_VE_Correction_Factor. |
| `KA_GAMMA_INIT_TABLE` | 0x00873E | NONE 0-2 | Initialize Filtered_VE_Correction_Factor to this value. |
| `K_CYLINDER_VOLUME` | 0x00875C | Liter | Volume of each cylinder in the engine. |
| `KE_BACKUP_AIR_FLOW_FILTER_COEF` | 0x00875E | NONE 0-1 | Use this to filter air flow sensor reading to generate air flow 'prediction' in response to MAP OR T |
| `KE_HI_SPEED_DYNA_AIR_THRESH` | 0x008760 | RPM | Engine speed above which a filtered value OF Sensed_Air_Per_Cylinder is used instead of the Dyna-Air |
| `KE_HI_SPEED_DYNA_AIR_HYSTERESIS` | 0x008762 | RPM | Amount by which engine speed must drop below KE_Hi_Speed_Dyna_Air_Thresh before the Dyna_Air predict |
| `KE_USE_CHARGE_TEMPERATURE` | 0x008764 | Boolean | $000043CB |
| `K_DYNA_AIR_COEFFICIENT` | 0x008766 | Various | Array of corrective factors used to adjust the predicted volume of air that will get into the cylind |
| `K_INITIAL_OPERATING_ZONE` | 0x0088CE | Op. Zone # | Initial engine operating zone. |
| `K_WIDE_OPEN_THROTTLE_LO` | 0x0088D0 | Percent | Minumum throttle percentage that is still considered wide open throttle. |
| `K_IDLE_VEHICLE_SPEED_HI` | 0x0088D2 | MPH | Maximum vehicle speed that is still considered idle conditions. |
| `K_IDLE_THROTTLE_HI` | 0x0088D4 | Percent | Maximum throttle percentage that is still considered idle conditions. |
| `K_ENGINE_SPEED_UPPER_BOUND` | 0x0088D6 | RPM | RPM boundaries between engine speed zones in the operating zones grid. |
| `KE_ENGINE_SPEED_HYSTERESIS` | 0x0088DC | RPM | RPM boundary hysteresis for changing engine speed zones. |
| `K_MANIFOLD_PRESSURE_UPPER_BOUND` | 0x0088DE | kPa | Pressure boundaries between manifold pressure zones in the operating zones grid. |
| `KE_MANIFOLD_PRESSURE_HYSTERESIS` | 0x0088F6 | kPa | Pressure boundary hysteresis for changing manifold pressure zones. |
| `K_MAXFLOW_SAFETY_FACTOR` | 0x0088F8 | NONE 0-2 | A safety factor multiplied by the calculated maximum air flow limit used on the air flow variables u |
| `K_DEEP_DECEL_MAP_THRESHOLD` | 0x0088FA | kPa | MAP threshold below which the engine is considered to be in deep deceleration. |
| `K_MODEL_OF_AIR_FILTER_COEF` | 0x0088FC | NONE 0-1 | Filter coefficient for the Model_Of_Air_Per_Cylinder term. |
| `K_STEADY_STATE_RPM_THRESHOLD` | 0x0088FE | kPa | Steady state enable/disable threshold.  Used to determine if high MAP or low MAP conditions will be  |
| `K_STEADY_STATE_MAP_THRESHOLD` | 0x008900 | kPa | Steady state enable/disable threshold.  Used to determine if high MAP or low MAP conditions will be  |
| `K_STEADY_STATE_LOW_MAP_DELTA` | 0x008902 | kPa | If low MAP conditions, delta MAP must equal this to enter steady state. |
| `K_STEADY_STATE_HIGH_MAP_DELTA` | 0x008904 | kPa | Delta MAP criteria for enable/disable of steady state if high MAP conditions. |
| ... | | 15 more entries | |

## BAROMETER (11 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_BARO_DEFAULT_MAP_FAILED` | 0x00893C | kPa | Default barometric pressure used if MAP sensor fails. |
| `KE_BARO_TPS_LIMIT` | 0x00893E | Percent | Minimum throttle position to allow a part throttle barometer update. |
| `KE_BARO_TPS_DELTA_LIMIT` | 0x008940 | Percent | Minimum change in throttle position during last 100 mS to allow a part throttle barometer update. |
| `KE_BARO_MAP_DELTA_LIMIT` | 0x008942 | kPa | Maximum change in manifold pressure during last 100 mS to allow a part throttle barometer update. |
| `KE_BARO_STABILITY_TIME` | 0x008944 | Seconds | Minimum time MAP and throttle must be stable to allow a part throttle barometer update. |
| `KE_MIN_RPM_FOR_BARO_UPDATE` | 0x008946 | RPM | Minimum RPM at which to allow a barometric pressure update. |
| `KE_MAX_RPM_FOR_BARO_UPDATE` | 0x008948 | RPM | Maximum RPM at which to allow a barometric pressure update. |
| `KE_MAX_BARO_OFFSET_FOR_UPDATE` | 0x00894A | kPa | Maximum calculated barometric pressure offset to allow baro update. |
| `KE_BARO_FILTER_COEFFICIENT` | 0x00894C | Coefficient | Barometer value update rate lag filter time constant. |
| `KV_BARO_OFFSET_FACTOR` | 0x00894E | Factor | Scaling factor used to correct the barometer offset value for altitude changes. |
| `KA_BARO_OFFSET` | 0x008960 | kPA | Sea level pressure offset to be added to the part throttle manifold pressure to correct the barometr |

## CONVERTER (30 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_COT_INC_TEMPERATURE_FILTER_CO` | 0x008B22 | Multiplier 0-1 | Filter used to predict current catalytic converter bed temperature when the predicted converter temp |
| `KV_COT_DEC_TEMPERATURE_FILTER_CO` | 0x008B4C | Multiplier 0-1 | Filter used to predict current catalytic converter bed temperature when the predicted converter temp |
| `KV_COT_DFCO_TEMPERATURE_OFFSET` | 0x008B76 | Degrees_C | $000044D8 |
| `KV_COT_EQ_RATIO_TEMP_OFFSET` | 0x008B88 | Degrees_C | $000044DA |
| `KV_COT_FFS_MULTIPLIER` | 0x008BAA | Scaler 1 | Multiplier to compensate the stabilized temperature for any fuel composition effects on exhaust temp |
| `KV_COT_INITIAL_TEMP_SOAK_MULT` | 0x008BB4 | Scaler_2 | soak timer modifier for Converter temperature prediction |
| `KV_COT_RETARDED_SPARK_OFFSET` | 0x008BC2 | Degrees_C | $000044DC |
| `KV_COT_VEH_SPEED_TEMP_OFFSET` | 0x008BD8 | Degrees_C | A prediction of the difference in stabilized catalytic converterbed temperature relative to the spee |
| `KE_COT_TEMPERATURE_COOL_THRESHOL` | 0x008BEA | Degrees_C | $000044DE |
| `KE_COT_TEMPERATURE_INITIAL` | 0x008BEC | Degrees_C_S | If the coolant temperature is larger than this calibration, thenthe converter temperature is initial |
| `KA_COT_TEMPERATURE_STOICH_STABLE` | 0x008BEE | Degrees_C | A prediction of the stabilized catalytic converter bed .temperature based on air-fuel ratio. |
| `KE_COT_THROTTLE_OPENED` | 0x008E64 | Percent | Throttle position >= this allows immediate update OF catalytic converter temperature. |
| `KE_COT_THROTTLE_CLOSED` | 0x008E66 | Percent | Throttle position <= this causes airflow to determine timing of catalytic converter temperature upda |
| `KE_COT_AIRFLOW_DELTA` | 0x008E68 | gm/S | Airflow dropping >= this IN one seconds causes delay OF catalytic converter temperature update. |
| `KE_COT_TEMPERATURE_DELAY_TIME` | 0x008E6A | Seconds | Overrun causes delay of this length in catalytic converter temperature update. |
| `KE_COT_EQ_RATIO_DEC_FILTER_LIMIT` | 0x008E6C | Equiv_Ratio | $000044DF |
| `KE_COT_DEC_TEMP_FILTER_RICH_RATE` | 0x008E6E | NONE 0-4 | $000044E0 |
| `KE_COT_HOT_DETERMINATION_ENABLE` | 0x008E70 | BOOLEAN | COT hot determination is activated IFF this is TRUE. |
| `KE_COT_HOT_TIME_THRESHOLD` | 0x008E72 | Seconds | If the catalytic converter temperature is above KE_COT_Temperature_High for this time, then the conv |
| `KE_COT_1PERCENT_TIME_THRESHOLD` | 0x008E74 | Seconds | $000044E1 |
| `KE_COT_1PERCENT_CYCLE_TIME` | 0x008E76 | Seconds_L | $000044E2 |
| `KE_COT_TEMPERATURE_LOW` | 0x008E7A | Degrees_C_S | The lowest catalytic converter temperature protection threshold. |
| `KE_COT_TEMPERATURE_MEDIUM` | 0x008E7C | Degrees_C_S | The second catalytic converter temperature protection threshold. |
| `KE_COT_TEMPERATURE_HIGH` | 0x008E7E | Degrees_C_S | The third catalytic converter temperature protection threshold. |
| `KE_COT_TEMPERATURE_EXTREME` | 0x008E80 | Degrees_C_S | The Highest catalytic converter temperature protection threshold. |
| `KE_COT_MIN_EQ_ALLOWED` | 0x008E82 | Equiv_Ratio_Type | Minimum amount of fueling that COT will try to deliver. Have this minimum help to get back to closed |
| `KE_COT_MAX_EQ_ALLOWED` | 0x008E84 | Equiv_Ratio_Type | Maximum amount of authority the COT EQ offset can have. |
| `KV_COT_BARO_MULTIPLIER` | 0x008E86 | Mult_0_to_2 | $000044E4 |
| `KV_COT_INC_COEF_TEMP_DELTA_MULT` | 0x008E90 | Mult_0_to_1 | Multiplier on the COT increasing filter coeff based on delta between COT stabilized and 1 second old |
| `KV_COT_EQ_RATIO_OFFSET` | 0x008E9C | Equiv_Ratio_Type | ???. |

## COOLANT (3 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_INITIAL_COOLANT_DEFAULT` | 0x0164CE | Degrees C | Initial coolant default, used if IAT failed on powerup. |
| `KE_WARM_ENGINE_DEFAULT_COOLANT_M` | 0x0164D0 | Degrees C | Maximum value allowed for default coolant temperature. |
| `KV_DEFAULT_COOLANT` | 0x0164D2 | Degrees C | This is added to what the ambient air temperature was at powerup to determine what the default coola |

## DG_FUEL_TRIM (9 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_FTRM_EXCESS_PURGE_PRESENT_LIM` | 0x016A2E | Unitless | Limits the number of purge tests per trip by limiting the number of tests that have indicated an exc |
| `KE_FTRM_LEAN_TEST_FAIL_LIMIT` | 0x016A2F | Unitless | Determines how long the system can be lean before a lean failure is reported to the Diagnostic Execu |
| `KE_FTRM_NORMAL_PURGE_PRESENT_LIM` | 0x016A30 | Unitless | Limits the number of purge tests per trip by limiting the number of tests that have indicated normal |
| `KE_FTRM_PURGE_TEST_REQUEST_LIM` | 0x016A31 | Unitless | Limits the number of purge tests per trip by limiting the number of purge test requests. |
| `KE_FTRM_RICH_TEST_FAIL_LIMIT` | 0x016A32 | Unitless | Determines how long the system can be rich before a rich failure is reported to the Diagnostic Execu |
| `KE_FTRM_SHORT_TERM_SAMPLE_COUNT` | 0x016A33 | Unitless | Determines how many samples will be collected and used in the short term fuel trim average calculati |
| `KE_FTRM_SHORT_TERM_TRIM_LEAN` | 0x016A34 | Unitless | Determines at what point the short term fuel trim average is considered to be lean. |
| `KE_FTRM_SHORT_TERM_TRIM_RICH` | 0x016A35 | Unitless | Determines at what point the short term fuel trim average is considered to be rich. |
| `KE_FTRM_WAIT_TIME_MAX` | 0x016A36 | Seconds | Maximum time the diagnostic will wait before executing after excess purge has been detected. |

## DG_IDLE (17 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_IAC_INTRUSIVE_TEST_OPTION` | 0x016A7E | BOOLEAN | This calibration option determines whether or not the valvetest should be allowed to execute. |
| `KE_IAC_RPM_DELTA_LIMIT` | 0x016A80 | RPM | RPM delta threshold to disable the valve test. |
| `KE_IAC_TPS_DELTA_LIMIT` | 0x016A82 | Percent | TPS delta threshold to disable the valve test. |
| `KE_IAC_VALVE_TEST_AIRFLOW_MAX` | 0x016A84 | Grams/Sec | Upper threshold airflow value to disable the valve test. |
| `KE_IAC_VALVE_TEST_AIRFLOW_MIN` | 0x016A86 | Grams/Sec | Lower threshold airflow value to disable the valve test. |
| `KE_IAC_VALVE_TEST_VEH_SPEED_MAX` | 0x016A88 | MPH | Upper threshold vehicle speed value to disable the valve test. |
| `KE_IAC_VALVE_TEST_VEH_SPEED_MIN` | 0x016A8A | MPH | Lower threshold vehicle speed value to disable the valve test. |
| `KE_IAC_AIRFLOW_RESPONSE_THRESH` | 0x016A8C | Grams/Sec | This calibration determines how much airflow decrease must occur in order to consider the valve func |
| `KE_IAC_VALVE_TEST_TIME_LIMIT` | 0x016A8E | Seconds | This calibration limits how long the valve test will execute. |
| `KE_IAC_REPORT_IDLE_RESULTS` | 0x016A8F | BOOLEAN | $000041E1 |
| `KV_IAC_RPM_ERROR_HIGH_THRESHOLD` | 0x016A90 | RPM | Minimum RPM error used to determine if the OBD_Idle_RPM_Error is too high. |
| `KE_IAC_RPM_HIGH_TIMER_LIMIT` | 0x016AB2 | Seconds | Minimum amount of time used to indicate that there is a high idle RPM problem. |
| `KV_IAC_RPM_ERROR_LOW_THRESHOLD` | 0x016AB4 | RPM | Maximum RPM error used to determine if the OBD_Idle_RPM_Error is too low. |
| `KE_IAC_RPM_LOW_TIMER_LIMIT` | 0x016AD6 | Seconds | Minimum amount of time used to indicate that there is a low idle RPM error problem. |
| `KE_IAC_FILTERED_RPM_ERROR_MAX` | 0x016AD8 | RPM | Maximum value for the allowable filtered RPM error. |
| `KE_IAC_TEST_PASS_TIME` | 0x016ADA | Seconds | Minimum time duration for the RPM to be within its allowable filtered RPM error to report that the I |
| `KE_IAC_RPM_ERROR_FILTER_COEFF` | 0x016ADC | Coef | This is the coefficient for the first order lag filter of the error. |

## DG_MF_ENGINE_CYCLE (1 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_MISF_ABNORMAL_SPEED_OPTION` | 0x016CF4 | Unitless | Indicates when to analyze the abnormal speed data. |

## DI_FUEL_TRIM (46 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_FTRM_LONG_TERM_IDLE_COEFF` | 0x01762A | NONE 0-2 | Coefficient applied to each 'Idle' Long Term Target used FOR this diagnostic. |
| `KA_FTRM_LONG_TERM_OFF_IDLE_COEFF` | 0x01762C | NONE 0-2 | Coefficient applied to each 'Off-Idle' Long Term Target used FOR this diagnostic. |
| `KE_FTRM_NUMBER_OF_OFF_IDLE_CELLS` | 0x01764C | Cells | Number of 'Off Idle' cells used in this diagnostic. |
| `KV_FTRM_OFF_IDLE_CELLS_TO_AVG` | 0x01764E | Region | Indicates for which Adaptive Regions to use the Long Term Target for this diagnostic. |
| `KE_FTRM_ENABLE_PLM_MODIFIER` | 0x01765E | 0_to_1 | Used as a modifier to the PLM multiplier for FTRM diagnostics. |
| `KE_FTRM_NUMBER_OF_IDLE_CELLS` | 0x017660 | Cells | Number of Idle Cells the system is calibrated to use FOR this diagnostic. |
| `KV_FTRM_IDLE_CELLS_TO_AVG` | 0x017662 | Region | Indicates for which adaptive regions the Long Term Target should be used for this diagnostic. |
| `KE_FTRM_DEFAULT_IDLE_CELL` | 0x01766A | Region | Initialize idle fuel trim data to that indicated in this region. |
| `KE_FTRM_DIAG_INHIBITING_FAULTS` | 0x01766C | Boolean | If TRUE is specified for the indexed fault group, then any active fault within that group will inhib |
| `KE_FTRM_COOLANT_TEMP_LOW` | 0x017670 | Degrees_C | Coolant temperature must be > this to enable diagnostic. |
| `KE_FTRM_COOLANT_TEMP_HIGH` | 0x017672 | Degrees_C | Coolant temperature must be < this to enable diagnostic. |
| `KE_FTRM_MAT_LOW` | 0x017674 | Degrees_C | Manifold air temperature must be > this to enable diagnostic. |
| `KE_FTRM_MAT_HIGH` | 0x017676 | Degrees_C | Manifold air temperature must be < this to enable diagnostic. |
| `KE_FTRM_MAP_LOW` | 0x017678 | kPa | Manifold absolute pressure must be > this to enable diagnostic. |
| `KE_FTRM_MAP_HIGH` | 0x01767A | kPa | Manifold absolute pressure must be < this to enable diagnostic. |
| `KE_FTRM_ENGINE_AIR_FLOW_LOW` | 0x01767C | gm/s | Engine air flow must be > this to enable diagnostic. |
| `KE_FTRM_ENGINE_AIR_FLOW_HIGH` | 0x01767E | gm/s | Engine air flow must be < this to enable diagnostic. |
| `KE_FTRM_PURGE_TEST_TMR_OFFSET_DC` | 0x017680 | Percent | $000042B1 |
| `KE_FTRM_RPM_LOW` | 0x017682 | RPM | Engine speed must be > this to enable diagnostic. |
| `KE_FTRM_RPM_HIGH` | 0x017684 | RPM | Engine speed must be < this to enable diagnostic. |
| `KE_FTRM_VEHICLE_SPEED_HIGH` | 0x017686 | MPH | Vehicle speed must be < this to enable diagnostic. |
| `KE_FTRM_TPS_HIGH` | 0x017688 | Percent | Throttle position (opening) must be < this to enable diagnostic. |
| `KE_FTRM_BAROMETER_LOW` | 0x01768A | kPa | Barometric pressure must be > this to enable diagnostic. |
| `KE_FTRM_FUEL_LEVEL_MIN` | 0x01768C | Percent | $000042B2 |
| `KE_FTRM_FUEL_LEVEL_LOW_TIME` | 0x01768E | Seconds | $000042B3 |
| `KE_FTRM_PURGE_RPM_MIN` | 0x017690 | RPM | Engine Speed must be > this to run the Excess Purge Test. |
| `KE_FTRM_ENG_AIRFLOW_LOW` | 0x017692 | gm/S | Engine Airflow must be > this to run the Excess Purge Test. |
| `KE_FTRM_ENG_AIRFLOW_HIGH` | 0x017694 | gm/S | Engine Airflow < this to run the Excess Purge Test. |
| `KV_FTRM_INDEX_OPER_TIME` | 0x017696 | Seconds | This much time must be spent in the current  adaptive index region before the Excess Purge Test can  |
| `KV_FTRM_PR_INDEX_OPER_TIME` | 0x0176B6 | Seconds | This much time must be spent in the current adaptive index region before the Excess Purge Test can r |
| ... | | 16 more entries | |

## DI_IDLE (9 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_IAC_BAROMETRIC_PRESSURE_MIN` | 0x017BE4 | kPa | Minimum barometric pressure threshold to enable the IAC diagnostic. |
| `KE_IAC_COOL_TEMP_MIN` | 0x017BE6 | Degrees_C | Minimum coolant temperature threshold to enable the IAC diagnostic. |
| `KE_IAC_ENGINE_RUN_TIME_MIN` | 0x017BE8 | Seconds | Minimum engine run time to enable the IAC diagnostic. |
| `KE_IAC_IGNITION_VOLTAGE_MAX` | 0x017BEA | Volts | Maximum ignition system voltage threshold to enable the IAC diagnostic. |
| `KE_IAC_IGNITION_VOLTAGE_MIN` | 0x017BEC | Volts | Minimum ignition system voltage threshold to enable the IAC diagnostic. |
| `KE_IAC_INTAKE_AIR_TEMP_MIN` | 0x017BEE | Degrees_C | Minimum intake air temperature threshold to enable the IAC diagnostic. |
| `KE_IAC_IDLE_THROTTLE_POS_MAX` | 0x017BF0 | Percent | Maximum throttle position threshold to allow idle conditions. |
| `KE_IAC_IDLE_VEHICLE_SPEED_MAX` | 0x017BF2 | MPH | Maximum vehicle speed threshold to allow idle conditions. |
| `KE_IAC_DIAG_STABLE_WINDOW_TIME` | 0x017BF4 | Seconds | Time for which the appropriate conditions must be stable before Idle Conditions Present flag can be  |

## ETC_ENGINE_AIR (26 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_ENG_ACCELERATION_THRESHOLD` | 0x00A750 | Engine_Accel_Type_Vs_RPM_Table | Lookup for engine accel threshold above which lead governing isenabled as a function of engine speed |
| `KV_ENGINE_SPEED_GOV_INT_GAIN` | 0x00A77A | RPM_S_Vs_EngSpd_Int_Gain | Integral gain value for the PID engine speed governor indexed withEngine Speed Error. |
| `KV_ENG_SPEED_GOV_DERIVATIVE_GAIN` | 0x00A7A4 | RPM_S_Vs_EngSpd_Deriv_Gain | Derivative gain value for the PID engine speed governor indexed with Engine_Speed_Error. |
| `KV_ENGINE_SPEED_GOV_PROP_GAIN` | 0x00A7CE | RPM_S_Vs_EngSpd_Prop_Gain | Proportional gain value for the PID engine speed governor indexed with Engine_Speed_Error. |
| `KV_VEH_SPEED_GOV_INT_GAIN` | 0x00A7F8 | Percent_Vs_VehSpd_Int_Gain | Integral gain value for the PID vehicle speed governor indexed withDesired_Throttle_Position. |
| `KV_VEH_SPEED_GOV_PROP_GAIN` | 0x00A7FE | MPH_S_Vs_VehSpd_Prop_Gain | Proportional gain value for the PID vehicle speed governor indexedwith Vehicle speed error. |
| `KV_VEH_ACCELERATION_THRESHOLD` | 0x00A80E | MPH_Per_300ms_S_Vs_MPH_Table | Vehicle accel threshold above which lead governing is enabled asa function of Vehicle_Acceleration_E |
| `KV_ENG_SPEED_GOV_AREA_INITIAL` | 0x00A82E | Gear_Vs_Percent_Table | Initial value used for throttle area if less than Desired_Throttle_Position. |
| `KV_TRANS_STAB_GOV_AREA_INITIAL` | 0x00A842 | Gear_Vs_Percent_Table | Initial value used for throttle area if less than Desired_Throttle_Position and ETC Trans stablizati |
| `KV_ENG_SPD_GOV_PID_DELAY_CNT` | 0x00A856 | Gear_Vs_Count_Table | Specifies the number of control loops that the PID terms will be initialized upon activation of the  |
| `KE_ENG_SPD_GOV_EXIT_HYSTERESIS` | 0x00A860 | RPM | Exit Engine speed gov when speed drops this amout below Engine_ Speed_Max_Limit and RPM_Gov is not t |
| `KE_ENGINE_SPD_GOV_AREA_MIN` | 0x00A862 | Percent | Lower clamp for engine speed governor speed area |
| `KE_VEH_SPEED_GOV_AREA_INITIAL` | 0x00A864 | Percent | Initial value used in lead mode if current throttle area is less than this calibration. |
| `KE_VEH_SPEED_DERIVATIVE_GAIN` | 0x00A866 | Vehicle_Spd_Gain_Type | The gain coefficient in the Vehicle speed gov derivative term |
| `KE_VEH_SPD_GOV_EXIT_HYSTERESIS` | 0x00A868 | MPH | Exit vehicle speed gov when speed drops this amout below Vehicle_ Speed_Max_Limit and MPH_Gov is not |
| `KE_VEHICLE_SPD_GOV_AREA_MIN` | 0x00A86A | Percent | Lower clamp for governor speed area |
| `KE_ACCEL_LOW_MPH_THRESHOLD` | 0x00A86C | MPH | Programmed acceleration low vehicle speed. |
| `KE_ACCEL_HIGH_MPH_THRESHOLD` | 0x00A86E | MPH | Programmed acceleration High vehicle speed. |
| `KE_LOW_SPEED_ACCEL_RATE` | 0x00A870 | MPH_Per_Second_S | Programmed acceleration low vehicle speed acceleration rate. |
| `KE_MEDIUM_SPEED_ACCEL_RATE` | 0x00A872 | MPH_Per_Second_S | Programmed acceleration Medium vehicle speed acceleration rate. |
| `KE_HIGH_SPEED_ACCEL_RATE` | 0x00A874 | MPH_Per_Second_S | Programmed acceleration High vehicle speed acceleration rate. |
| `KE_ACCEL_GOVERNOR_PROPORTIONAL_G` | 0x00A876 | Percent_S | Programmed acceleration proportional gain term. |
| `KE_ACCEL_GOVERNOR_INTEGRAL_GAIN` | 0x00A878 | Vehicle_Accel_Int_Gain_Type | Programmed acceleration integral gain term. |
| `KE_LOW_SPEED_MAX_AREA` | 0x00A87A | Percent | Clamp for max throttle commanded when vehicle speed is too low |
| `KE_VEHICLE_SPEED_FILT_COEF` | 0x00A87C | Coefficient | Coefficient used to filter vehicle speed for core ETC algorithm |
| `KE_ENGINE_SPEED_GOV_ENABLED` | 0x00A87E | BOOLEAN | Used to prevent engine speed governor from executing. |

## FUEL (1 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_TWO_BANK_FUEL_CONTROL` | 0x00A87F | BOOLEAN | Used to determine if two bank fuel control is to be used or not. |

## FUELCALIBRATIONS (1 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `HEADER` | 0x01E1B0 | Cal_ID_Record | Use this cal to identify the Fuel Systems calibration |

## FUEL_COMPOSITION (11 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_FLEX_FUEL_EQUIPPED` | 0x00B7AC | TRUE/FALSE | Indicates that vehicle is flex fuel capable. |
| `KE_FFS_COMP_CHANGE_THRESH` | 0x00B7AE | Percent | Minimum fuel composition change to initiate an update of the filtered fuel composition. |
| `KE_FFS_COMP_DELAY_VOLUME` | 0x00B7B0 | Liters | Volume of fuel to be consumed by the engine before a new fuel composition reaches the injector rail. |
| `KE_FFS_COMP_TRANSITION_VOLUME` | 0x00B7B2 | Liters | Volume of fuel consumed by the engine during which the transition occurs from the old fuel compositi |
| `KE_FFS_COMPOSITION_DEFAULT` | 0x00B7B4 | Percent | Value to be used when fuel composition can not otherwise be determined. |
| `KE_FFS_0PCT_ALCOHOL_FREQUENCY` | 0x00B7B6 | Hertz | Frequency of the FFS PWM input corresponding to 0% alcohol. |
| `KE_FFS_COMPOSITION_SLOPE` | 0x00B7B8 | Scaler_16_S | Proportional constant for determining fuel composition from the frequency of the FFS PWM input. |
| `KE_FFS_MIN_TEMPERATURE` | 0x00B7BA | Degrees_C | Minimum temperature value measured by the Flex Fuel Sensor. |
| `KE_FFS_MAX_TEMPERATURE` | 0x00B7BC | Degrees_C | Maximum temperature value measured by the Flex Fuel Sensor. |
| `KE_FFS_MIN_TEMP_LOW_TIME` | 0x00B7BE | Milliseconds | Low time of FFS input PWM corresponding to the minimum temperature value measured by the Flex Fuel S |
| `KE_FFS_TEMPERATURE_SLOPE` | 0x00B7C0 | Multiplier_-+_1000 | Proportional constant for determining fuel temperature from the low time of the Flex Fuel Sensor PWM |

## FUEL_CRANK (18 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_FUEL_BARO_GAIN` | 0x00B7C2 | NONE 0-2 | Gain applied to account for air density charges with barometric pressure. |
| `KV_FUEL_PRESSURE_DELAY` | 0x00B7CC | Seconds | Amount of time to delay after powerup before allowing key on prime pulse to be delivered. |
| `KV_OCTIFIRE2_SOAKTIMER_MODIFIER` | 0x00B7EC | NONE 0_2 | A modifier to Second_Octifire_Prime based on soaktimerif enabled. |
| `KV_PRIME_PULSE_MASS` | 0x00B826 | Grams | This is the mass of fuel to be injected on the first simultaneous, nonsynchronous (Prime) injection. |
| `KV_FIRST_PULSE_MASS` | 0x00B846 | Grams | This is the mass of fuel to be injected on the first simultaneous, synchronous (octifire) injection. |
| `KV_SECOND_PULSE_MASS` | 0x00B866 | Grams | $0000456C |
| `KV_FIRST_OCTIFIRE_REF_COUNT` | 0x00B886 | SHORTCARD | $0000456D |
| `KV_SECOND_OCTIFIRE_REF_OFFSET` | 0x00B896 | SHORTCARD | $0000456E |
| `KV_PRIME_MIN_RUN_TIME` | 0x00B8A6 | Seconds | This is the minimum engine run time required to allow a prime pulse to issued. |
| `KE_PRIME_FUEL_ENG_SPEED_DISABLE` | 0x00B8C6 | Engine Speed | $00004571 |
| `KE_USE_FUEL_PUMP_DEVELOPMENT_SW` | 0x00B8C8 | BOOLEAN | If TRUE look at Pin J1-52 to check if FP dev switch is open, if so don't deliver prime pulse. |
| `KE_SOAKTIMER_ENG_RUNTIME_LIMIT` | 0x00B8CA | Seconds | $00004572 |
| `KE_SOAKTIMER_COOLANT_LIMIT` | 0x00B8CE | Degrees_C | $00004573 |
| `KE_KEY_ON_PRIME_REENABLE_TIME` | 0x00B8D0 | Seconds | Key-on Prime is delivered if the previous key-on primedelivered was at least this time ago which is  |
| `KV_KEY_ON_SOAKTIMER_MODIFIER` | 0x00B8D4 | NONE 0_2 | A modifier to Key_On_Prime based on soaktimer if enabled. |
| `KV_OCTIFIRE1_SOAKTIMER_MODIFIER` | 0x00B90E | NONE 0_2 | A modifier to First_Octifire_Prime based on soaktimerif enabled. |
| `KA_FFS_COMPOSITION_GAIN` | 0x00B948 | Mult 0 to 4 | Gain applied to account for changes due to fuel alcohol composition |
| `KE_CRANK_SEQUENTIAL_COOLANT_ENAB` | 0x00BA06 | Degrees_C | Enable sequential fueling during crank when coolant temperature is less than this calibration. |

## FUEL_CU (54 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_CLUTCH_DFCO_SPK_EXIT_RATE` | 0x00BA08 | Degrees | Determines ramp rate of spark advance during exit of aclutch-based DFCO event. |
| `KE_DFCO_SPK_CONTINUE_REF_COUNT` | 0x00BA0A | Counts | Number of low res. reference pulse counts to hold continue spark after DFCO exit. |
| `KE_DFCO_SPK_CONTINUE_TPS_HIGH` | 0x00BA0C | Percent | Throttle position high limit for usage of DFCO continue spark. |
| `KE_DFCO_SPK_CONTINUE_TPS_LOW` | 0x00BA0E | Percent | Throttle position Low limit for usage of DFCO continue spark. |
| `KE_DFCO_SPK_DISABLED_HOLD_REF` | 0x00BA10 | Counts | $00004510 |
| `KE_DFCO_SPK_INTERRUPTED_RAMP` | 0x00BA11 | BOOLEAN | $00004512 |
| `KV_DFCO_SPK_CONTINUE_SPARK_HIGH` | 0x00BA12 | Degrees | If throttle position is above the high threshold, then this cal. is used for DFCO continue spark. |
| `KV_DFCO_SPK_CONTINUE_SPARK_LOW` | 0x00BA3C | Degrees | If throttle position is below the low threshold, then this cal. is used for DFCO continue spark. |
| `KV_DFCO_SPK_EXIT_RAMP_RATE` | 0x00BA66 | Degrees | This calibration establishes the rate in which Net Spark Advance will increase during DFCO exit. |
| `KV_DFCO_SPK_HOLD_SPARK` | 0x00BA88 | Degrees | Net Spark advance during DFCO after the ramp is completed. |
| `KV_DFCO_SPK_ENTRY_RAMP_RATE` | 0x00BAB2 | Multiplier_0_to_1 | This calibration establishes the rate in which Net Spark Advance will decrease during DFCO. |
| `KE_STALL_ENGINE_SPEED` | 0x00BADC | RPM | Min engine speed in which fuel cutoff is still allowed.  Lowerspeeds than this may result in a stall |
| `KE_ENGINE_OVERSPEED_TIME` | 0x00BADE | Seconds | The time that engine speed must exceed the calibratible threshold before fuel is shut off. |
| `KE_PN_ENGINE_OVERSPEED_HIGH` | 0x00BAE0 | RPM | This is the Engine Speed above which fuel is shutoff if the transmission is in park or neutral. |
| `KE_PN_ENGINE_OVERSPEED_LOW` | 0x00BAE2 | RPM | Engine Speed must fall below this limit before allowing fuel to be turned back on if the transmissio |
| `KE_ENG_OVERSPEED_VSS_FAIL_HIGH` | 0x00BAE4 | RPM | Eng speed above which fuel is shutoff if a VSS failure existsUsed for chassis protection on med duty |
| `KE_ENG_OVERSPEED_VSS_FAIL_LOW` | 0x00BAE6 | RPM | Eng speed must fall below before fuel is turned on if a VSS failureexists.  Used for chassis protect |
| `KV_ENGINE_OVERSPEED_HIGH` | 0x00BAE8 | RPM | $00004513 |
| `KV_ENGINE_OVERSPEED_LOW` | 0x00BAFC | RPM | This is the calibration that the engine speed must fall below before allowing fuel to be turned back |
| `KE_LOW_RPM_FUEL_CUTOFF_HIGH` | 0x00BB10 | RPM | Turn fuel on above this RPM if fuel is currently turned off due to low RPM. |
| `KE_LOW_RPM_FUEL_CUTOFF_LOW` | 0x00BB12 | RPM | Turn fuel off below this RPM if fuel is the engine speed has been above KE_Low_RPM_Fuel_Cutoff_High. |
| `KV_COLD_ENGINE_PROTECTION_TIME` | 0x00BB14 | Seconds | Amount of time that cold engine protection should be enabled |
| `KE_CLUTCH_DFCO_ENTRY_DELAY` | 0x00BB34 | Seconds | Clutch-based DFCO enabling conditions must exist continuously for this long to enable clutch-based D |
| `KE_CLUTCH_DFCO_EXIT_TPS_INCREASE` | 0x00BB36 | Percent | Exit clutch-based DFCO if throttle position increases by more than this amount over a 25 mS interval |
| `KE_CLUTCH_DFCO_HOLD_TIME` | 0x00BB38 | Seconds | The duration of a clutch-based DFCO event. |
| `KE_CLUTCH_THROTTLE_DECREASE` | 0x00BB3A | Percent | $00004515 |
| `KE_CLUTCH_DFCO_REENABLE_DELAY` | 0x00BB3C | Seconds | Minimum amount of time between clutch-based DFCO events. |
| `KE_CLUTCH_THROTTLE_WINDOW` | 0x00BB3E | Seconds | Window of time either before or after the clutch pedal is depressed when a throttle decrease indicat |
| `KE_DFCO_REENTRY_DELAY` | 0x00BB40 | Seconds | Amount of time to disable DFCO from becoming active after exiting DFCO. |
| `KE_CLUTCH_DFCO_COOLANT_TEMP` | 0x00BB42 | Degrees_C | Minimum coolant temperature to enable clutch-based DFCO. |
| ... | | 24 more entries | |

## FUEL_DY (26 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_MAKEUP_FUEL_ENABLED` | 0x00BC3C | TRUE | FALSE | Flag used to enable/disable the calculation and delivery of makeup fuel. |
| `KA_K2_PRIOR_STOMP_COMP_REDUCTION` | 0x00BC3E | NONE 0_1 | $0000453D |
| `KV_K4_STOMP_COMP_DELTA_LIMIT` | 0x00BCFC | Grams | Minimum delta fuel limit to add stomp compensation. |
| `KV_K5_STOMP_COMP_DELTA_LOW_LIMIT` | 0x00BD06 | Grams | Delta mass threshold to disable throttle stomp compensation on tip outs. |
| `KA_IMPACT_FACTOR_20KPA_MAP` | 0x00BD10 | Mult_0_to_1 | Describes the fraction of the injected pulse that will impact the port wall at 20kPa MAP. |
| `KA_IMPACT_FACTOR_100KPA_MAP` | 0x00BDCE | Mult_0_to_1 | Describes the fraction of the injected pulse that will impact the port wall at 100kPa MAP. |
| `KA_BOIL_TIME_CONST_20KPA_MAP` | 0x00BE8C | Seconds | Describes the time it takes for 63% of liquid fuel on port wall to vaporize at 20kPa MAP. |
| `KA_BOIL_TIME_CONST_100KPA_MAP` | 0x00BF4A | Seconds | Describes the time it takes for 63% of liquid fuel on port wall to vaporize at 100kPa MAP. |
| `KE_DFCO_STOMP_COMP_TPS_MIN` | 0x00C008 | Percent | Throttle position below which stomp comp will not be applied when exiting DFCO. |
| `KE_FUEL_IGNORE_WALL_WETTING_RPM` | 0x00C00A | RPM | $0000453E |
| `KE_FUEL_IGNORE_WALL_WETTING_TPS` | 0x00C00C | Percent | $0000453F |
| `KE_MIN_PULSE_WIDTH` | 0x00C00E | Seconds | $00004540 |
| `KA_K1_INITIAL_STOMP_COMP_TIME_FA` | 0x00C010 | NONE 0_8 | $00004542 |
| `KA_K3_STOMP_COMP_TIME_DECAY` | 0x00C0CE | NONE 0_1 | The stomp compensation factor is decayed by this multiplier once per second. |
| `KV_K1_SOAKTIMER_MODIFIER` | 0x00C18C | NONE 0_2 | A modifier to Stomp_Comp_Time_Decay_Factor based on.soaktimer if enabled. |
| `KE_WALL_MASS_FACTOR` | 0x00C1C6 | NONE 0_2 | Multiplier used to guarantee stability of the Wall  Wetting model. |
| `KV_IMPACT_FACTOR_MODIFIER` | 0x00C1C8 | NONE 0_1 | Factor, based on air flow, which reduces KA_Boiling_Time_Constant. |
| `KA_IMPACT_FACTOR_BLEND_FRACTION` | 0x00C20A | Scaler_16_S | Normalized fraction describing the impact factor surface relative to the 20kPa and 100kPa MAP extrem |
| `KA_BOIL_TIME_CONST_BLND_FRACTION` | 0x00C360 | Scaler_16_S | Normalized fraction describing the boiling time constant surface relative to the 20kPa and 100kPa MA |
| `KV_INITIAL_WW_DELAY_REFS` | 0x00C4B6 | SHORTCARD | Number of reference pulses to delay, after PCM state equal run, before enabling Wall Wetting. |
| `KE_STARTUP_MAKEUP_DELAY` | 0x00C4C6 | CARDINAL | Number of reference pulses to delay after engine is running before calculating makeup fuel. |
| `KV_MAKEUP_FUEL_CHANNEL` | 0x00C4C8 | CYL NUM | Selects the cylinder to receive makeup fuel based on the current cylinder. |
| `KV_MAKEUP_CYLINDER_INDEX` | 0x00C4D2 | CYL NUM | Selects the cylinder index for which to calculate makeup fuel based on the cylinder to receive makeu |
| `KA_IMPACT_FACTOR_MODIFIER_2` | 0x00C4DC | Scaler 0-1 | Impact Factor modifier vs Delta Mass and Coolant Temp. |
| `KA_BOILING_TIME_MODIFIER_2` | 0x00C630 | Scaler 0-1 | Impact Factor modifier vs Delta Mass and Coolant Temp. |
| `KV_BOILING_TIME_MODIFIER` | 0x00C784 | NONE 0_1 | Factor, based on air flow, which reduces KA_Boiling_Time_Constant. |

## FUEL_ECONOMY (2 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_FUEL_ECONOMY_SCALER` | 0x00C7C6 | NONE 0_2 | Scaler used to adjust liters of fuel for fuel economy calculations. |
| `KE_INSTANTANEOUS_FILTER_COEFF` | 0x00C7C8 | NONE 0-1 | Coefficient for filtering instantaneous fuel |

## FUEL_EQ (94 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_GREEN_ENGINE_AIRFUEL_RATIO` | 0x00C7CA | Airfuel Ratio | Commanded Airfuel Ratio during Green Engine Crank. |
| `KE_CLEAR_FLOOD_THROTTLE_ENTER` | 0x00C7D0 | Percent | Threshold which throttle position must initially cross for no crank or prime fuel to be delivered. |
| `KE_CLEAR_FLOOD_THROTTLE_EXIT` | 0x00C7D2 | Percent | Threshold which throttle position must remain above for no crank or prime fuel to be delivered. |
| `KV_STOICHIOMETRIC_FUEL_AIR` | 0x00C7D4 | Mult_0_to_1 | Defines the ratio mass of fuel to mass of air for stoichiometric, based on alcohol content of fuel. |
| `KV_OPEN_LP_EQ_RATIO_BLEND_FACTOR` | 0x00C7F6 | Mult_0_to_1 | $0000433D |
| `KV_PARK_DRIVE_DELAY_TIME` | 0x00C800 | Seconds | Amount of time after PRNDL shifts into drive before adding park to drive enrichment. |
| `KV_ENGINE_PROTECTION_EQUIVALENCE` | 0x00C820 | Equiv_Ratio_Type | Equivalence ratio based on engine speed if engine protection is enabled. |
| `KE_NORMAL_CRANK_EVENT_LIMIT` | 0x00C84A | 1-32 | Absolute ref count defining the end of the normal crank portion of KA_Crank_Equivalence_Ratio. |
| `KE_EXTENDED_CRANK_EVENT_LIMIT` | 0x00C84B | 1-32 | $0000433E |
| `KE_HOT_ENRICHMENT_COOLANT_ENTRY_` | 0x00C84C | Degrees_C | Coolant temperature above which the hot enrichment state can become active. |
| `KE_HOT_ENRICHMENT_COOLANT_EXIT_T` | 0x00C84E | Degrees_C | Coolant temperature below which the hot enrichment state will become inactive, used due to hysteresi |
| `KE_HOT_ENRICHMENT_THROTTLE_ENTRY` | 0x00C850 | Percent | Throttle position above which the hot enrichment state can become active. |
| `KE_HOT_ENRICHMENT_THROTTLE_EXIT_` | 0x00C852 | Percent | Throttle position below which the hot enrichment state will become inactive, used due to hysteresis. |
| `KE_HOT_ENRICHMENT_MAP_ENTRY_THRE` | 0x00C854 | kPa | Manifold pressure above which the hot enrichment state can become active. |
| `KE_HOT_ENRICHMENT_MAP_EXIT_THRES` | 0x00C856 | kPa | Manifold pressure below which the hot enrichment state will become inactive, used due to hysteresis. |
| `KE_HOT_ENRICHMENT_VEH_SPEED_ENTR` | 0x00C858 | MPH | Vehicle speed above which the hot enrichment state can become active. |
| `KE_HOT_ENRICHMENT_VEH_SPEED_EXIT` | 0x00C85A | MPH | Vehicle speed below which the hot enrichment state will become inactive, used due to hysteresis. |
| `KE_HOT_ENRICHMENT_EQUIVALENCE_OF` | 0x00C85C | Degrees_C | Coolant temperature threshold in which enrichmentwill be applied. |
| `KE_HOT_ENRICHMENT_EQUIVALENCE_MU` | 0x00C85E | Mult_0_to_2 | Percentage of enrichment as a function of coolant temperature. |
| `KE_MAXIMUM_ENRICHMENT_EQUIVALENC` | 0x00C860 | Equiv_Ratio_Type | Maximum allowable enrichment equivalence ratio. |
| `KE_POWER_ENRICHMENT_HOT_TEMP` | 0x00C862 | Degrees_C | Coolant temperature threshold above which a different enable criteria for PE is used. |
| `KE_POWER_ENRICHMENT_THROTTLE_HYS` | 0x00C864 | Percent | Hysteresis to the base throttle threshold to prevent noise from turning PE on and off. |
| `KE_POWER_ENRICHMENT_COT_HYSTERES` | 0x00C866 | Percent | Hysteresis to the base throttle threshold to prevent noise from turning PE on and off, while in COT. |
| `KE_POWER_ENRICHMENT_MAP_THRESHOL` | 0x00C868 | kPa | Base MAP threshold to enable PE. |
| `KE_POWER_ENRICHMENT_MAP_HYSTERES` | 0x00C86A | kPa | Hysteresis to the base MAP threshold to prevent noise from turning PE on and off. |
| `KV_POWER_ENRICHMENT_HOT_THRESHOL` | 0x00C86C | Percent | Defines the base enable throttle position for power  enrichment when coolant temperature is above a  |
| `KV_POWER_ENRICHMENT_COLD_THRESHO` | 0x00C892 | Percent | Defines the base enable throttle position for power  enrichment when coolant temperature is below a  |
| `KV_POWER_ENRICHMENT_RPM_EQUIVALE` | 0x00C8B8 | Equiv_Ratio_Type | Defines the base equivalence ratio for power enrichment based on RPM. |
| `KV_POWER_ENRICHMENT_COOLANT_EQUI` | 0x00C8DE | Equiv_Ratio_Type | Used to modify the base equivalence ratio for power enrichment based on coolant. |
| `KV_POWER_ENRICHMENT_IAT_EQUIV` | 0x00C904 | Equiv_Ratio_Type | Used to modify the base equivalence ratio for power enrichment based on IAT. For Holden application. |
| ... | | 64 more entries | |

## FUEL_IO (26 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_BOUNDARY_OFFSET` | 0x00E276 | Lores_Periods | $000043DB |
| `KE_ENG_PROTECTION_NORMAL_END_OF_` | 0x00E278 | Lores_Periods | Normal pulse end of injection location if engine protection is enabled, in number of lores periods a |
| `KE_ENG_PROTECTION_TRIM_END_OF_IN` | 0x00E27A | Lores_Periods | Trim pulse end of injection location if engine protection is enabled, in number of lores periods aft |
| `KV_NORMAL_END_OF_INJECTION_COOLA` | 0x00E27C |  | $000043DC |
| `KV_TRIM_END_OF_INJECTION_COOLANT` | 0x00E29C |  | Defines the trim pulse end of injection location, based on coolant temperature, in number of lores p |
| `KE_MINIMUM_INJECTOR_OFF_TIME` | 0x00E2BC | Milliseconds | Minimum amount of time that an injector must remain off before turning on again. |
| `KV_INJECTOR_OFFSET_ADJUSTMENT` | 0x00E2BE | Milliseconds | This is the injector offset used to account for injector dynamics due vacuum effects on the trapped  |
| `KA_INJECTOR_OFFSET` | 0x00E2E0 | Milliseconds | $000043DD |
| `KA_FIRST_CYL_TO_GET_SEQUENTIAL` | 0x00E698 | Cyl_Number | $000043DE |
| `KV_BANK_FOR_CYLINDER` | 0x00E6B8 | Bank1|Bank2 | This calibration associates each cylinder with a bank of the engine. |
| `KA_UPDATE_FUEL_CHANNELS` | 0x00E6C0 | TRUE|FALSE | Determines whether to update Fuel Pulse Width for the injector based on the current cylinder. |
| `KE_AIRBAG_ENG_SHUTDOWN_VEH_SPEED` | 0x00E700 | MPH | Threshold below which the vehicle is considered to stationary |
| `KE_AIRBAG_ENG_SHUTDOWN_TIMER` | 0x00E702 | Seconds | Timer above which the vehicle is considered to have been longenough to allow the state of the airbag |
| `KE_DESOOT_COOLANT_THRESH` | 0x00E704 | Degrees_C | Coolant must be at least this temperature to enable Desoot mode. |
| `KE_DESOOT_COOLANT_THRESH_HYSTERE` | 0x00E706 | Degrees_C | Hysteresis required of coolant temperature to disable Desoot mode. |
| `KE_DESOOT_MAP_THRESH` | 0x00E708 | kPa | MAP must be at least this calibration to enable Desoot mode. |
| `KE_DESOOT_MAP_THRESH_HYSTERESIS` | 0x00E70A | kPa | Hysteresis required of MAP to disable Desoot mode. |
| `KE_DESOOT_LO_MAP_EXIT_THRESH` | 0x00E70C | kPa | If MAP falls below this calibration, disable Desoot mode immediately. |
| `KE_DESOOT_DELAY_TIME` | 0x00E70E | Seconds | Conditions must exist for this amount of time for the Desoot mode to activate. |
| `KE_USE_CRANK_EOIT` | 0x00E70F | BOOLEAN | Prevent Desoot mode from affecting the end of injection targets |
| `KE_DESOOT_EOIT` | 0x00E710 | Lores_Periods | EOIT to use when Desoot mode has been activated |
| `KV_END_OF_INJECTION_CRANK_TARGET` | 0x00E712 | Low res Period | $000043E0 |
| `KV_INJECTOR_TRIM_FACTOR` | 0x00E732 | Scaler_0_to_2 | Allows for scaling of the final injector pulse width for demonstration purposes. |
| `KA_DESOOT_UPDATE_FUEL_CHANNELS` | 0x00E742 | BOOLEAN | Determines whether to update Fuel Pulse Width for the injector based on the current cylinder when De |
| `KV_FIRST_FUEL_DELAY` | 0x00E782 | SHORTCARD | Number of Ref pulses after sync that must occur before sequentialfuel delivery to allow prime fuel t |
| `KE_MINIMUM_TRIM_PULSE_WIDTH` | 0x00E786 |  |  |

## FUEL_LO (31 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_CANISTER_LIMIT` | 0x00E788 | Percent | Used to determine if canister purge is active or inactive. |
| `KE_RPM_HYSTERESIS` | 0x00E78A | RPM | Provides more stability when transitioning from one cell to another. |
| `KE_MAP_HYSTERESIS` | 0x00E78C | kPa | Provides more stability when transitioning from one cell to another. |
| `KE_LONG_TERM_IDLE_THROTTLE_THRES` | 0x00E78E | Percent | Throttle threshold used to determine idle condition. |
| `KE_LONG_TERM_IDLE_VEH_SPEED_THRE` | 0x00E790 | MPH | Vehicle speed threshold used to determine idle condition. |
| `KV_RPM_BOUNDARY` | 0x00E792 | RPM | Boundary for cells based on engine speed. |
| `KV_MAP_BOUNDARY` | 0x00E798 | kPa | Boundary for cells based on manifold pressure. |
| `KE_BLENDING_SELECTED` | 0x00E79E | TRUE|FALSE | Allow blending if target is below the current long term correction. |
| `KE_BLENDING_TIMER` | 0x00E7A0 | Seconds | Time between long term memory blends. |
| `KE_LONG_TERM_DELTA` | 0x00E7A4 | NONE 0-2 | If cell value changes more than this, reset integrator to 1.0. |
| `KV_PLM_REDUCTION_FACTOR` | 0x00E7A6 | NONE 0-1 | Factor to reduce PLM by before applying to pulse width. |
| `KE_ADAPTIVE_LOW_COOLANT_LIMIT` | 0x00E7E8 | Degrees_C | Minimum coolant temperature to allow long term cell update. |
| `KE_ADAPTIVE_HIGH_COOLANT_LIMIT` | 0x00E7EA | Degrees_C | Maximum coolant temperature to allow long term cell update. |
| `KE_LONG_TERM_CORRECTION_ENABLED` | 0x00E7EC | TRUE|FALSE | Indicates long term cell update is enabled. |
| `KE_UPDATE_THRESHOLD` | 0x00E7EE | NONE 0-2 | Amount the integrator must be above or below 1.0 for an update to occur. |
| `KE_UPDATE_DELTA` | 0x00E7F0 | NONE 0-2 | Value of the long term update amount. |
| `KE_LONG_TERM_MINIMUM` | 0x00E7F2 | NONE 0-2 | Minimum long term correction. |
| `KE_LONG_TERM_IDLE_MAXIMUM` | 0x00E7F4 | NONE 0-2 | Maximum long term correction for idle purge cells. |
| `KE_LONG_TERM_IDLE_MINIMUM` | 0x00E7F6 | NONE 0-2 | Minimum long term correction for idle purge cells. |
| `KE_LONG_TERM_MAXIMUM` | 0x00E7F8 | NONE 0-2 | Maximum long term correction. |
| `KE_LONG_TERM_UPDATE_RATE` | 0x00E7FA | Seconds | Time required for update condition to exist to allow Long Term Adaptive update. |
| `KE_PLM_INCREASE_DELTA` | 0x00E7FC | NONE 0-2 | Value to increase PLM by when learning up. |
| `KE_PLM_REDUCTION_DELTA` | 0x00E7FE | NONE 0-2 | Value to reduce PLM by when learning down. |
| `KE_ADAPTIVE_NON_PURGE_MAX_KAM_LI` | 0x00E800 | NONE 0-2 | Max BLM which can be learned in KAM for non-CCP cells |
| `KE_ADAPTIVE_PURGE_MAX_KAM_LIMIT` | 0x00E802 | NONE 0-2 | Max BLM which can be learned in KAM for CCP cells |
| `KV_ADAPTIVE_MIN_KAM_LIMIT` | 0x00E804 | NONE 0-2 | Minimum block learn modifier which can be learned in KAM. |
| `KV_PLM_UPDATE_OFFSET` | 0x00E80A | NONE 0-2 | If the BLM for the cell falls more than this offset below the BLM in KAM for the cell, the PLM is de |
| `KE_NON_CCP_KAM_LOW_COOLANT_LIMIT` | 0x00E832 | Degrees_C | Lower limit of coolant window to tranfer non-CCP BLM values to KAM. |
| `KE_NON_CCP_KAM_HIGH_COOLANT_LIMI` | 0x00E834 | Degrees_C | Upper limit of coolant window to tranfer non-CCP BLM values to KAM. |
| `KV_PLM_MINIMUM` | 0x00E836 | NONE 0-2 | Minimum PLM correction. |
| ... | | 1 more entries | |

## FUEL_O2 (29 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_POST_DERIVATIVE_TERM_FILTER` | 0x00E844 | NONE 0-1 | Time coefficient for first order lag filter. |
| `KE_POST_PROPORTIONAL_IDLE_FACTOR` | 0x00E846 | Scaler 2 | Modifier to proportional offset in idle condition to reduce the aggressiveness of proportional term. |
| `KE_LONG_TERM_IDLETHROTTLE_THRESH` | 0x00E848 | Percent | Throttle threshold used to determine idle condition. |
| `KE_LONG_TERM_IDLE_VEH_SPD_THRESH` | 0x00E84A | SHORTCARD | Vehicle speed threshold used to determine idle condition. |
| `KE_POST_OXYGEN_LEAN_READY` | 0x00E84C | Millivolts | Lower voltage threshold to determine when the oxygen sensor is ready. |
| `KE_POST_OXYGEN_RICH_READY` | 0x00E84E | Millivolts | Upper voltage threshold to determine when the oxygen sensor is ready. |
| `KE_POST_OXYGEN_READY_COUNTER` | 0x00E850 | Counts | Count number of samples outside the control limits to determine when the sensor hsa become ready. |
| `KE_BANK_EXHAUST` | 0x00E851 | Value | Configuration of the exhaust system for the specific application. |
| `KE_POST_OXYGEN_INTEGRAL_COOLANT` | 0x00E852 | Degrees_C | Threshold for coolant temperature to enable Integral Part of Post Oxygen Fuel Trim. |
| `KV_POST_OXYGEN_BANK1_INTEGRATOR` | 0x00E854 | NONE 0-2 | Closed loop integrator enable criteria for post oxygen control. |
| `KV_POST_OXYGEN_BANK2_INTEGRATOR` | 0x00E85E | NONE 0-2 | Closed loop integrator enable criteria for post oxygen control. |
| `KE_POST_O2_DECEL_UPPER_LIMIT` | 0x00E868 | NONE 0-64 | Post O2 mode is DECEL if closed loop mode is greater than 0 and less than or equal to this calibrati |
| `KE_POST_O2_CRUISE_UPPER_LIMIT` | 0x00E86A | NONE 0-64 | $0000456A |
| `KE_POST_O2_LIGHT_ACCEL_UPPER_LIM` | 0x00E86C | NONE 0-64 | $0000456B |
| `KE_POST_TIME_CONSTANT` | 0x00E86E | NONE 0-1 | Time coefficient for first order lag filter. |
| `KV_POST_OXYGEN_INT_OFFSET_MAX` | 0x00E870 | Millivolts | Limit maximum value of Post_Oxygen_Integral_Offset. |
| `KV_POST_OXYGEN_INT_OFFSET_MIN` | 0x00E87A | Millivolts | Limit minimum value of Post_Oxygen_Integral_Offset. |
| `KV_BANK1_POST_LEAN_THRESHOLD` | 0x00E884 | Millivolts | Post Oxygen lower threshold. |
| `KV_BANK2_POST_LEAN_THRESHOLD` | 0x00E88E | Millivolts | Post Oxygen lower threshold. |
| `KV_BANK1_POST_RICH_THRESHOLD` | 0x00E898 | Millivolts | Post Oxygen upper threshold. |
| `KV_BANK2_POST_RICH_THRESHOLD` | 0x00E8A2 | Millivolts | Post Oxygen upper threshold. |
| `KE_POST_OXYGEN_INTEGRATE` | 0x00E8AC | Millivolts | Integration value for post Oxygen transitions. |
| `KV_POST_OXYGEN_INTEGRAL_DELAY` | 0x00E8AE | Seconds | Delay time between execution of the post oxygen integral correction. |
| `KV_POST_DERIV_DISABLE_TIME` | 0x00E8B8 | Seconds | Disable derivative offsets after starts for this amount of time. |
| `KV_POST_DERIV_RAMP_IN_TIME` | 0x00E8CC | Seconds | Once enabled, ramp the derivative offsets to desired values by this time. |
| `KV_POST_OXYGEN_DERIVATIVE_OFFSET` | 0x00E8E0 | Millivolts | Apply this additive offset as derivative term based on filtered PO2 signal. |
| `KV_POST_O2_PROPORTIONAL_OFFSET` | 0x00E90A | Millivolts | Apply this additive offset as proportional term based on filtered PO2 signal. |
| `KV_POST_PROP_DISABLE_TIME` | 0x00E944 | Seconds | Disable proportional offsets after starts for this amount of time. |
| `KV_POST_PROP_RAMP_IN_TIME` | 0x00E958 | Seconds | Once enabled, ramp the proportional offsets to desired values by this time. |

## FUEL_PL (8 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KV_INJECTOR_SLOPE` | 0x00E96C | Grams/Sec | Defines the slope of the injector versus on time. |
| `KV_FLOW_RATE_PUMP_CORRECTION` | 0x00E98E | Mult0to8 | Correction to injector flow rate based on fuel pump voltage, Ignition voltage. |
| `KE_SHORT_PULSE_LIMIT` | 0x00E9C6 | Milliseconds | Pulses shorter than this will be increased by an amount KV_Short_pulse_Adjustment. |
| `KV_SHORT_PULSE_ADJUSTMENT` | 0x00E9C8 | Milliseconds | $00004575 |
| `KV_MINIMUM_PULSE_WIDTH` | 0x00EA4E | Milliseconds | This is the minimum pulse width allowed. |
| `KV_DEFAULT_PULSE_WIDTH` | 0x00EA78 | Milliseconds | This is the default pulse width used when the pulse is less than the minimum. |
| `KE_USE_INJ_SLOPE_MODIFIER` | 0x00EAA2 | BOOLEAN | Determines if the Injector Slope will be modified for fuel flow. |
| `KV_INJ_SLOPE_FUEL_FLOW_MOD` | 0x00EAA4 | Unitless | The correction to injector flow based on fuel flow rate. |

## FUEL_PUMP (1 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_FUEL_PUMP_PRIME_TIMER` | 0x01FDB4 | Seconds | $00004199 |

## FUEL_SH (43 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_CL_IDLE_THROTTLE_POSITION` | 0x00EABC | Percent | Throttle position must be less than this calibration for Cl_Idle to be TRUE. |
| `KE_CL_IDLE_THROTTLE_HYSTERESIS` | 0x00EABE | Percent | Throttle position hysteresis for CL_Idle determination. |
| `KE_CL_IDLE_VEHICLE_SPEED` | 0x00EAC0 | MPH | Vehicle Speed must be less than this for CL_Idle to be TRUE. |
| `KE_CL_IDLE_VEHICLE_SPEED_HYSTERE` | 0x00EAC2 | MPH | Vehicle Speed hysteresis for CL_Idle determination. |
| `KE_CL_LOW_RPM_RESET_COOLANT_TEMP` | 0x00EAC4 | Degrees_C | Coolant must be warmer than this to enable or trigger 'Low RPM Closed Loop Reset'. |
| `KE_CL_LOW_RPM_RESET_ENABLE_OFFSE` | 0x00EAC6 | RPM | Engine speed must exceed 'desired idle speed' BY more than this to enable 'Low RPM Closed Loop Reset |
| `KE_CL_LOW_RPM_RESET_INTEGRAL_TER` | 0x00EAC8 | NONE 0-2 | $000044F8 |
| `KE_CL_LOW_RPM_RESET_TRIGGER_OFFS` | 0x00EACA | RPM | $000044F9 |
| `KV_CL_MODE` | 0x00EACC | NONE 0-64 | $000044FB |
| `KV_INTEGRAL_DELAY_BASE_LEAN` | 0x00EB6E | Seconds | Base factor applied to the Integral_Delay_Base when both Slow and Fast O2 status are LEAN. |
| `KV_INTEGRAL_DELAY_BASE_RICH` | 0x00EB80 | Seconds | Base factor applied to the Integral_Delay_Base when both Slow and Fast O2 status are RICH. |
| `KV_INTEGRAL_DELAY_GAIN_LEAN` | 0x00EB92 | NONE 0-2 | Gain factor applied to the Integral_Delay_Base when both Slow and Fast O2 status are LEAN. |
| `KV_INTEGRAL_DELAY_GAIN_RICH` | 0x00EBAC | NONE 0-2 | Gain factor applied to the Integral_Delay_Base when both Slow and Fast O2 status are RICH. |
| `KE_INTEGRAL_TERM_ADJUSTMENT_IDLE` | 0x00EBC6 | NONE 0-2 | Magnitude of adjustments to integral term under idle conditions. |
| `KE_INTEGRAL_TERM_MINIMUM` | 0x00EBC8 | NONE 0-2 | The minimum integrator factor value allowed in closed loopmode. |
| `KE_INTEGRAL_TERM_MINIMUM_AF_CL` | 0x00EBCA | NONE 0-2 | The minimum integrator factor value allowed in Air FuelClosed Loop mode. |
| `KE_INTEGRAL_TERM_MAXIMUM` | 0x00EBCC | NONE 0-2 | The maximum allowed integrator value. |
| `KV_INTEGRAL_TERM_ADJUSTMENT_LEAN` | 0x00EBCE | NONE 0-2 | $000044FC |
| `KV_INTEGRAL_TERM_ADJUSTMENT_RICH` | 0x00EBE0 | NONE 0-2 | $000044FD |
| `KE_O2_AFTER_START_THRESHOLD_OFF` | 0x00EBF2 | Millivolts | Offset added to O2 Rich Lean threshold. For Holden Vehicle only. |
| `KE_O2_COLD_TEMPERATURE` | 0x00EBF4 | Degrees_C | $000044FE |
| `KE_O2_COLD_TIME` | 0x00EBF6 | Seconds | The offset is added to the Rich Lean threshold as long as Engine run time is less this. Used for Hol |
| `KV_O2_RICH_LEAN_THRESHOLD` | 0x00EBF8 | MilliVolts | Oxygen sensor voltage level for rich/lean decision |
| `KV_O2_OFF_RICH_LEAN_THRESHOLD` | 0x00EC1C | MilliVolts | $000044FF |
| `KE_PROPORTIONAL_TERM_IDLE_ENABLE` | 0x00EC40 | TRUE_FALSE | Use specially formed idle proportional term at idle. |
| `KV_PROPORTIONAL_TERM_IDLE_BASE` | 0x00EC42 | NONE 0-2 | Proportional term base for each bank under idle conditions |
| `KV_PROPORTIONAL_TERM_IDLE_GAIN` | 0x00EC54 | NONE 0-2 | Gain factor applied to proportional term base for each bank under idle conditions |
| `KV_PROP_TERM_NORMAL_BASE_LEAN` | 0x00EC6E | NONE 0-2 | Base size of proportional term under normal (non-idle) conditions when Fast O2 Status is LEAN. |
| `KV_PROP_TERM_NORMAL_BASE_RICH` | 0x00EC80 | NONE 0-2 | Base size of proportional term under normal (non-idle) conditions when Fast O2 Status is RICH. |
| `KV_PROP_TERM_NORMAL_GAIN_LEAN` | 0x00EC92 | NONE 0-2 | Gain factor applied to proportional term under normal (non-idle) conditions when Fast O2 Status is L |
| ... | | 13 more entries | |

## FUEL_ST (12 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_OXYGEN_LOWER_READY_VOLTAGE` | 0x00ED0A | Millivolts | Lower voltage threshold in which the oxygen sensor voltage must fall below before indicating oxygen  |
| `KE_OXYGEN_UPPER_READY_VOLTAGE` | 0x00ED0C | Millivolts | Upper voltage threshold in which the oxygen sensor voltage must go above before indicating oxygen se |
| `KE_OXYGEN_NOT_READY_TIME` | 0x00ED0E | Seconds | $0000451F |
| `KE_COLD_CLOSED_LOOP_TEMPERATURE` | 0x00ED10 | Degrees_C | Startup coolant temperature below which the cold wait timer, KE_Cold_Wait_Time, is used. |
| `KE_HOT_CLOSED_LOOP_TEMPERATURE` | 0x00ED12 | Degrees_C | Startup coolant temperature above which the hot wait timer, KE_Hot_Wait_Time, is used. |
| `KE_COLD_WAIT_TIME` | 0x00ED14 | Seconds | Engine run time before closed loop is allowed when startup coolant is below KE_Cold_Closed_Loop_Temp |
| `KE_WARM_WAIT_TIME` | 0x00ED16 | Seconds | $00004520 |
| `KE_HOT_WAIT_TIME` | 0x00ED18 | Seconds | Engine run time before closed loop is allowed when startup coolant is above KE_Hot_Closed_Loop_Tempe |
| `KV_CLOSED_LOOP_COOLANT_TEMPERATU` | 0x00ED1A | Degrees_C | Defines the coolant temperature above which closed loop fuel is allowed. |
| `KE_USE_AIRFUEL_CLOSED_LOOP_STATE` | 0x00ED40 | TRUE | FALSE | $00004521 |
| `KE_O2_READY_COUNTER_THRESHOLD` | 0x00ED41 | Counter | Number of O2 reads that must fall outside not ready window for the O2 sensor to be ready. |
| `KE_OPEN_LOOP_FOR_MISFIRE` | 0x00ED42 | TRUE | FALSE | If this calibration is set TRUE, any Misfire faults will force Afterstart mode and reset LTM Fuel Ce |

## IAC_AIRFLOW (96 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_IDLE_AREA_SCALAR` | 0x00ED44 | Percent_Per_mm_Squared | Conversion factor to convert to percent WOT from an effective throttle area in millimeters squared. |
| `KE_THROTTLE_CRACKER_DISABLE_THRE` | 0x00ED46 | MPH | Vehicle speed must be <= to this calibration to disable the extended throttle cracker function. |
| `KE_THROTTLE_CRACKER_ENABLE_THRES` | 0x00ED48 | MPH | Vehicle speed must be >= to this calibration to enable the extended throttle cracker function. |
| `KE_AC_OFFSET_FILTER_CONSTANT` | 0x00ED4A | Filt_Coeff | Filter coefficient for first order lag filter. |
| `KE_CHOKE_FLOW_TIME` | 0x00ED4C | Seconds | Calibration used before engine is running to generate desired effective area based on choke flow pre |
| `KE_COOLING_FAN_CORRECTION` | 0x00ED4E | GPS | Default value of airflow required to compensate for the parasitic load from a single cooling fan. |
| `KE_COOLING_FANS_CORRECTION` | 0x00ED50 | GPS | Default value of airflow required to compensate for the parasitic load from multiple cooling fans. |
| `KE_DFCO_ENTRANCE_HOLD_TIME` | 0x00ED52 | Seconds | The amount of time to hold decel fuel cutoff airflow before decaying it away. |
| `KE_DFCO_ENTRY_RAMP_RATE` | 0x00ED54 | GPS | This calibration increases or decreases the decel fuel cutoff air value when decel fuel cutoff is en |
| `KE_DFCO_EXIT_RAMP_RATE` | 0x00ED56 | GPS | This calibration increases or decreases the decel fuel cutoff air value when decel fuel cutoff is ex |
| `KE_DRIVE_CORRECTION_HIGH` | 0x00ED58 | GPS | Upper limit allowed for adaptively learned correction to the airflow for the engine when the transmi |
| `KE_DRIVE_CORRECTION_LOW` | 0x00ED5A | GPS | Lower limit allowed for adaptively learned correction to the airflow for the engine when the transmi |
| `KE_DRIVE_FILTER_CONSTANT` | 0x00ED5C | Filt_Coeff | Filter coefficient for first order lag filter for filtering Learned_Airflow_Drive.  Activation rate: |
| `KE_FAN_INHIBIT_REGULATOR_TIME` | 0x00ED5E | Seconds | The constant speed regulator will be inhibited for this period of time when the Fan1 or Fan2 load ha |
| `KE_HIGH_TO_LOW_PRESSURE_TIME` | 0x00ED60 | Seconds | $0000452C |
| `KE_IDLE_TO_OFFIDLE_TIME` | 0x00ED62 | Seconds | Calibration to enable reset of Breakaway_Friction_Airflow if the engine running time equals this val |
| `KE_LEARNED_AC_AIRFLOW_OFFSET_DR` | 0x00ED64 | GPS | Default value of AC_Airflow_Learned_Offset_DR. |
| `KE_LEARNED_AC_AIRFLOW_OFFSET_PN` | 0x00ED66 | GPS | Default value of AC_Airflow_Learned_Offset_PN. |
| `KE_AC_OFFSET_LOW_DR` | 0x00ED68 | GPS | Lower limit allowed for adaptively learned correctionto the AC airflow offset while in a drive gear  |
| `KE_AC_OFFSET_HIGH_DR` | 0x00ED6A | GPS | Upper limit allowed for adaptively learned correctionto the AC airflow offset while in a drive gear  |
| `KE_AC_OFFSET_LOW_PN` | 0x00ED6C | GPS | Lower limit allowed for adaptively learned correctionto the AC airflow offset while in park or neutr |
| `KE_AC_OFFSET_HIGH_PN` | 0x00ED6E | GPS | Upper limit allowed for adaptively learned correctionto the AC airflow offset while in park or neutr |
| `KE_LEARNED_AIRFLOW_DRIVE` | 0x00ED70 | GPS | Default value of Learned_Airflow_Drive. |
| `KE_LEARNED_AIRFLOW_PARK_NEUTRAL` | 0x00ED72 | GPS | Default value of Learned_Airflow_Park_Neutral. |
| `KE_LOW_TO_HIGH_PRESSURE_TIME` | 0x00ED74 | Seconds | $0000452E |
| `KE_MAP_AD_FAIL_THRESHOLD` | 0x00ED76 | A/D Counts | Calibration used to determine the closed throttle  maximum AD MAP. |
| `KE_MAP_FOR_IAC_RESET` | 0x00ED78 | kPa | Calibration used to control IAC motor park position since MAP goes to baro on engine shut down. |
| `KE_MAX_DESIRED_IDLE_EFF_AREA` | 0x00ED7A | Millimeters_Squared | $00004530 |
| `KE_PARK_NEUTRAL_CORRECTION_HIGH` | 0x00ED7C | GPS | Upper limit allowed for adaptively learned correction to the airflow for the engine when the transmi |
| `KE_PARK_NEUTRAL_CORRECTION_LOW` | 0x00ED7E | GPS | Lower limit allowed for adaptively learned correction to the airflow for the engine when the transmi |
| ... | | 66 more entries | |

## SPARK_ADVANCE (107 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KA_CAT_LIGHTOFF_SPARK_RETARD` | 0x010176 | Degrees_POSITIVE | The amount of spark retard to apply to lightoff the catalytic converter. |
| `KA_MBT_SPARK` | 0x010638 | Degrees | Spark Advance for mean best timing. |
| `KA_MAIN_OT_HIGH_OCTANE` | 0x010890 | Degrees | This calibration determines base spark 'good fuel' contribution to spark advance. |
| `KA_MAIN_OT_LOW_OCTANE` | 0x010E3A | Degrees | This calibration determines base spark 'bad fuel' contribution to spark advance. |
| `KV_FFS_SPARK_BLEND_FACTOR` | 0x0113E4 | Mult_0_to_1 | Interpolation fraction used to determine the portion of the FFS_Spark to use. |
| `KV_LAUNCH_SPARK_RAMP_OUT_MULT` | 0x0113EE | 0 to 1 | Multiplier applied to the Launch Spark value every ref pulse ince the hold duration has expired. |
| `KV_LIMIT_MAX_RETARD` | 0x011414 | Degrees | Maximum spark retard limit allowed. |
| `KE_AIR_PER_CYLINDER_BLEND_RATIO` | 0x01143E | Scaler_2_S | Describes the index and ratio for interpolation between two adjacent air per cylinder values. |
| `KE_HVS_RUN_MODE_ENABLE_RPM` | 0x011440 | RPM | Engine speed threshold above which the EST will switch to low resnormal mode for non 24X application |
| `KE_HVS_RUN_MODE_DISABLE_RPM` | 0x011442 | RPM | Engine speed threshold below which the EST will switch to low rescrank mode for non 24X applications |
| `KV_HVS_SWITCH_MODES_REF_COUNT` | 0x011444 | Scaler_0_to_16 | $000044C3 |
| `KA_LAUNCH_SPARK` | 0x011454 | Degrees | This calibration is a spark advance or retard based on Coolant Temperature and Engine Run Time. |
| `KE_LAUNCH_SPARK_MAXCLTSOAKENABLE` | 0x01155E | Degrees C | Maximum Coolant Temperature for Soak Time multiplier to be applied to Launch Spark. |
| `KE_LAUNCH_SPARK_MINRUNSOAKENABLE` | 0x011560 | Seconds | Minimum Previous Engine Run Time for Soak Time multiplier to be applied to Launch Spark. |
| `KE_LAUNCH_SPARKRPMMULTCOOLENABLE` | 0x011564 | Degrees C | Minimum Coolant Temperature for enable of the Engine Speed Multiplier to Launch Spark. |
| `KE_LIGHTOFF_AND_LAUNCHRAMPINTIME` | 0x011566 | Seconds | Used to calculate a ramp in multiplier based upon engine run time. |
| `KE_LAUNCH_SPARKRPMRUNTIME` | 0x011568 | Seconds | Minimum Engine Run Time for application of the RPMmultiplier. |
| `KV_LAUNCH_SPARK_RPM_MULTIPLIER` | 0x01156A | 0 to 2 | $000044C5 |
| `KV_LAUNCH_SPARK_SOAK_MULT` | 0x011594 | 0 to 2 | This calibration is a multiplier applied to Launch Spark in short soak time conditions. |
| `KV_LAUNCH_SPARK_DELTA_CYLAIRMASS` | 0x01159C | Grams | This calibration is an enabler to Launch Spark when an increasing change in cylinder air mass is abo |
| `KV_LAUNCH_SPARK_DELTA_CYLAIRMULT` | 0x0115C6 | 0 to 1 | This calibration is a multiplier for the cylinder air mass threshold. |
| `KV_LAUNCH_SPARK_DELT_CA_TPS_MULT` | 0x0115EC | 0 to 2 | This calibration is a multiplier to be applied to the cyli- nder air threshold. |
| `KV_LAUNCH_SPARK_DURATION` | 0x011602 | Pulses | This calibration is the number of low resolution reference pulses. |
| `KA_EQ_RATIO_SPARK` | 0x011616 | Degrees | Equivalence ratio contribution to spark. |
| `KA_EGR_SPARK` | 0x0118B6 | Degrees | EGR contribution to spark. |
| `KA_IAT_SPARK` | 0x011BA8 | Degrees | This calibration determines the main induction air temperature spark. |
| `KA_RDSC_DAMPING_GAIN_CT` | 0x01206A | Deg/RPM | CLOSED Throttle gain to use in the calculation of RDSC active damping. |
| `KA_RDSC_DAMPING_GAIN_OT` | 0x012092 | Deg/RPM | OPEN Throttle gain to use in the calculation of RDSC active damping. |
| `KA_RDSC_PHASE_DELAY_TIME_CT` | 0x0120BA | mSec | CLOSED Throttle delay of the actual deliveryof active damping spark. |
| `KA_RDSC_PHASE_DELAY_TIME_OT` | 0x0120E2 | mSec | OPEN Throttle delay of the actual deliveryof active damping spark. |
| ... | | 77 more entries | |

## SPARK_KNOCK (85 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_NUMBER_OF_SENSORS` | 0x01460A | Number | This is the number of ESC sensors used to determine if ESC sensors should be multiplexed in diagnost |
| `KE_DELTA_TPS_ABSOLUTE_MAD_DIS` | 0x01460C | Percent | If TPS changes more than this in 200 ms MAD learning will be disabled |
| `KE_DELTA_RPM_ABSOLUTE_MAD_DIS` | 0x01460E | RPM | If RPM changes more than this in 200 ms MAD learning will be disabled |
| `KE_DELTA_MAP_ABSOLUTE_MAD_DIS` | 0x014610 | RPM | If 12p5_ms_Filtered_MAP has changed more than this MAD learning will be disabled |
| `KE_MAP_12P5_MS_FILT_COEFFICIENT` | 0x014612 | Coef. | Filter coefficient for 12.5 ms MAP readings |
| `KE_ADAPTIVE_BPF_GAIN_ADJ_RATE` | 0x014613 | Counts | This controls the number of 200 ms loops betweenadaptive BPF gain calculations |
| `KE_INITIAL_ADAPTIVE_BPF_GAIN` | 0x014614 | Gain_dB | This is the initial value for the BPF Gain. |
| `KE_MIN_ADAPTIVE_BPF_GAIN` | 0x014615 | Gain_dB | This is the minimum value for the BPF Gain. |
| `KE_MAX_ADAPTIVE_BPF_GAIN` | 0x014616 | Gain_dB | This is the maximum value for the BPF Gain. |
| `KE_DIAG_IRIC_DB_GAIN` | 0x014617 | Gain_dB | This is the value for the BPF Gain in diagnostic mode. |
| `KE_RPM_KNOCK_LOW` | 0x014618 | RPM | RPM value below this level will not enable Delta RPM detection logic. |
| `KE_RPM_KNOCK_HIGH` | 0x01461A | RPM | RPM value above this level will not enable Delta RPM detection logic. |
| `KE_RPM_KNOCK_DELTA` | 0x01461C | RPM | An RPM increase greater than this over a 25 msec time period will enable the Delta RPM detection log |
| `KE_RPM_KNOCK_TIME` | 0x01461E | Second | Duration of time to modify knock thresholds due to an engine speed increase. |
| `KA_OCTANE_INIT_MODIFIER` | 0x014620 | Scaler -1 to 1 | Octane adaptive scaler is modified by this calibrated amount every powerup when KE_Octane_Scaler_Mod |
| `KE_ADAPT_BPF_HIGH_AVG_NOISE_THRE` | 0x0148F2 | Volts | If the average noise is greater than this value the adaptive gain will be decreased. |
| `KE_ADAPT_BPF_LOW_AVG_NOISE_THRES` | 0x0148F4 | Volts | If the average noise is less than this value the adaptive gain will be increased. |
| `KE_KNOCK_DETECTOR_MAD_INIT` | 0x0148F6 | Millivolts | Initialization value for Knock_Detector_MAD value invoked during powerup. |
| `KE_KNOCK_DETECTOR_MAD_MAX` | 0x0148FA | Millivolts | Maximum allowable knock detector mean absolute deviation (MAD) for any sensor. |
| `KE_KNOCK_DETECTOR_MAD_MIN` | 0x0148FE | Millivolts | Minimum allowable knock detector mean absolute deviation (MAD) for any sensor. |
| `KE_KNOCK_MAD_MAP_THRESH` | 0x014902 | kPa | Above this manifold pressure, threshold Knock_Detector_MAD can be updated. |
| `KE_KNOCK_MAD_RPM_THRESH` | 0x014904 | RPM | Above this engine speed, threshold Knock_Detector_MAD can be updated. |
| `KE_MAD_COEFFICIENT_SAMPLES` | 0x014906 | Counts | Determines the number of samples used in computing Knock_Detector_MAD. |
| `KE_IR_AVERAGE_NOISE_INITIAL` | 0x014908 | Volts | If KE_IR_Avg_Noise_Modify_Init is TRUE then all IR average noise levels will be set to this calibrat |
| `KE_IR_AVG_NOISE_MODIFY_INIT` | 0x01490A | Boolean | When set to TRUE, all IR average noise levels will be set to a calibration upon initialization. |
| `KE_OCTANE_SCALER_DIAG_DEFAULT` | 0x01490C | Multiplier_0_To_1 | This is the octane scaler value if a knock sensor group fault is active. |
| `KE_OCTANE_SCALER_MODIFY_ON_INIT` | 0x01490E | Boolean | When set to TRUE the octane adaptive scaler will be modified on every powerup. |
| `KE_SPEED_CHANGE_HIGH_COUNTER_A` | 0x01490F | Counts | When this calibration is exceeded, the slow sample number will be used for determining the average n |
| `KV_KNOCK_FAST_ATTACK_COOL_GAIN` | 0x014910 | Scaler | An attack rate coolant gain table that allows the detector to be disabled below an engine temperatur |
| `KV_KNOCK_FAST_ATTACK_BARO_GAIN` | 0x014936 | Scaler | An attack rate baro gain table that adjusts the detector's sensitivity for changes in altitude. |
| ... | | 55 more entries | |

## VEH_SPEED (19 entries)

| Label | Address | Units | Description |
|-------|---------|-------|-------------|
| `KE_PULSES_PER_MILE` | 0x01FECC | Pulses/Mile | Vehicle speed sensor scaling factor. |
| `KE_USE_EEPROM_VSS_CALS` | 0x01FECE | BOOLEAN | Determines whether to use the EEPROM based VSS cals or the Cal ROM VSS cals. |
| `KE_PRIMARY_OUTPUT_PPM` | 0x01FED0 | Pulses/Mile | Determines the PPM for the vehicle speed primary output. |
| `KE_SECONDARY_OUTPUT_PPM` | 0x01FED2 | Pulses/Mile | Determines the PPM for the vehicle speed secondary output. |
| `KE_VEH_SPEED_TIME` | 0x01FED4 | Seconds | If no vehicle speed pulses for this period of time, the vehicle is considered to be stationary. |
| `KE_VEHICLE_SPEED_LIMIT` | 0x01FED6 | MPH | limit below which the ETC governor attempts to keep the vehicle speed |
| `KE_VSS_APPLICATION_TYPE` | 0x01FED8 | CPD_Output_Selection_Type | $00004330 |
| `KE_RTD_FAULT_ETC_GOV_MAX_SPEED` | 0x01FEDA | MPH | $00004332 |
| `KE_FINAL_DRIVE_RATIO` | 0x01FEDC | Multiplier_0_to_16 | Axle gear ratio for calibration application |
| `KE_MAX_POSITIVE_MPH_CHANGE` | 0x01FEDE | MPH / Sec | The vehicle speed will not increase at a rate greater than this. |
| `KE_RTD_FAULT_MAX_SPEED` | 0x01FEE0 | MPH | Maximum vehicle speed when an RTD fault is sent to the PCM by the RTD system. |
| `KE_VEHICLE_OVERSPEED_TIME` | 0x01FEE2 | Seconds | For a non ETC vehicle, time that vehicle speed must be over the max. limit before cutting off fuel. |
| `KE_VEHICLE_OVERSPEED` | 0x01FEE4 | MPH | $00004334 |
| `KE_VEHICLE_OVERSPEED_TIME_ETC` | 0x01FEE6 | Seconds | For an ETC vehicle, time that vehicle speed must be over the max. limit before cutting off fuel. |
| `KE_VEHICLE_OVERSPEED_ETC` | 0x01FEE8 | MPH | $00004335 |
| `KE_VEHICLE_OVERSPEED_HYSTERESIS` | 0x01FEEA | MPH | Hysteresis applied to vehicle speed at which fuel cutoff occurs. |
| `KE_C2_VEH_SPEED_DEFAULT_ENABLED` | 0x01FEEC | BOOLEAN | Enable setting vehicle speed to a valid class 2 wheel speedwhen a fault in the vehicle speed group i |
| `KE_VEH_SPEED_FILTER` | 0x01FEEE | Seconds | Vehicle speed filter coefficient used in the first order lag filter applied to the raw vehicle speed |
| `KE_LOW_AXLE_SPEED_ADJUST` | 0x01FEF0 | Multiplier_0_to_2 | Vehicle speed multiplier when Dual_Axle is Low. Note: Range from (0.1228 .. < 2.0)! |
