# 0.15.0-dev — Block 11: Temperature-Unit Safety

- Persist the Home Assistant temperature unit (`°C` or `°F`) as the fixed
  reference for each schedule document at initial setup.
- Upgrade existing pre-release schedule documents by binding them once to the
  current Home Assistant unit.
- Safely refuse to start if the configured HA temperature unit later changes;
  users remove and re-add the integration before creating schedules in the new
  unit.
- Remove the old Celsius-only bound from the ZEAL diagnostic action, leaving
  normal climate-entity validation to Home Assistant.
