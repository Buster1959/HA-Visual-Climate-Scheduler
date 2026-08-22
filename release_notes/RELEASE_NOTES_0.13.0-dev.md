# 0.13.0-dev — Block 9: Quick Change & Temporary Overrides

- Separate Quick Change view: select rooms/zones or Whole house.
- Simple `−1` and `+1` adjustments, or an exact target temperature.
- With one selected room/zone, the exact-target field follows the selected adjustment.
- Extra spacing before Apply keeps the controls visually separate.
- Repeated `+1` / `−1` presses accumulate before applying the hold; the
  redundant adjustment text has been removed.
- The editor and Quick Change labels use Home Assistant's configured
  temperature unit (`°C` or `°F`).
- The timeline scale expands to include every entered target value, including
  values outside a typical heating range.
- Holds for 2 hours, 4 hours or each room's next scheduled change.
- Active-hold visibility and cancellation; schedules remain unchanged.
