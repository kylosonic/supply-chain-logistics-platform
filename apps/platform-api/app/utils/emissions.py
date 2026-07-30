"""Carbon emissions calculation using EPA ton-mile factors."""

# EPA standard emission factor: kg CO2 per ton-mile for heavy-duty trucks
_EPA_FACTOR_KG_CO2_PER_TON_MILE = 0.161

# Typical gross vehicle weight by class (in tons)
_WEIGHT_CLASS_TONS: dict[str, float] = {
    'heavy_duty': 40.0,
    'medium_duty': 14.0,
    'light_duty': 6.0,
}


def calculate_trip_emissions(distance_miles: float, vehicle_weight_class: str) -> float:
    """Calculate trip CO2 emissions using the EPA ton-mile factor.

    Args:
        distance_miles: Total trip distance in miles.
        vehicle_weight_class: One of 'heavy_duty', 'medium_duty', or 'light_duty'.

    Returns:
        CO2 emissions in kilograms, rounded to two decimal places.

    Raises:
        ValueError: If the weight class is not recognised.
    """
    weight_class_lower = vehicle_weight_class.strip().lower()
    weight_tons = _WEIGHT_CLASS_TONS.get(weight_class_lower)
    if weight_tons is None:
        valid = ', '.join(sorted(_WEIGHT_CLASS_TONS.keys()))
        raise ValueError(
            f"Unknown vehicle_weight_class '{vehicle_weight_class}'. "
            f"Valid options: {valid}"
        )

    emissions = distance_miles * weight_tons * _EPA_FACTOR_KG_CO2_PER_TON_MILE
    return round(emissions, 2)
