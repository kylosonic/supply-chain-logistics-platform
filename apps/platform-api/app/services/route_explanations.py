from __future__ import annotations

from typing import Any

FACTOR_LABELS = {
    'distance': 'Distance',
    'time': 'Travel time',
    'cost': 'Monetary cost',
}


def _factor_shares(totals: dict[str, float]) -> dict[str, float]:
    clean = {key: max(float(totals.get(key, 0.0)), 0.0) for key in FACTOR_LABELS}
    total = sum(clean.values())
    if total <= 0:
        return dict.fromkeys(clean, 0.0)
    return {key: round((value / total) * 100, 1) for key, value in clean.items()}


def _dominant_factor(totals: dict[str, float]) -> str:
    if max(totals.values(), default=0.0) <= 0:
        return 'none'
    return max(totals, key=lambda key: totals[key])


def _decision_reason(trace: dict[str, Any]) -> str:
    components = trace.get('factor_components') or {}
    shares = _factor_shares(components)
    chosen = trace.get('chosen_warehouse_code', 'the selected stop')
    runner_up = trace.get('runner_up_warehouse_code')
    margin = trace.get('margin')

    if max(components.values(), default=0.0) <= 0:
        reason = (
            f'All factor weights were zero at this step, so the deterministic '
            f'warehouse-code tie-break selected {chosen}.'
        )
    else:
        dominant = _dominant_factor(components)
        reason = (
            f'{FACTOR_LABELS[dominant]} contributed {shares[dominant]:.1f}% of the chosen '
            f'leg\'s weighted score.'
        )
        if runner_up is not None and margin is not None:
            reason += (
                f' {runner_up} was the runner-up, {margin:.2f} weighted points behind.'
            )
        else:
            reason += ' No runner-up stop was available at this decision.'

    excluded = int(trace.get('capacity_excluded_count') or 0)
    if excluded:
        reason += (
            f' Remaining vehicle capacity excluded {excluded} candidate '
            f'{"stop" if excluded == 1 else "stops"}.'
        )
    return reason


def _alternative_summary(
    selected: dict[str, Any],
    alternative: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not alternative or not alternative.get('stops'):
        return None

    first_stop = alternative['stops'][0]['warehouse_code']
    distance_delta = round(
        float(alternative['total_distance_km']) - float(selected['total_distance_km']), 2
    )
    duration_delta = (
        int(alternative['estimated_duration_min']) - int(selected['estimated_duration_min'])
    )
    cost_delta = round(float(alternative['total_cost']) - float(selected['total_cost']), 2)

    comparisons: list[str] = []
    if abs(distance_delta) >= 0.05:
        direction = 'farther' if distance_delta > 0 else 'shorter'
        comparisons.append(f'{abs(distance_delta):.2f} km {direction}')
    if duration_delta:
        direction = 'slower' if duration_delta > 0 else 'faster'
        comparisons.append(f'{abs(duration_delta)} min {direction}')
    if abs(cost_delta) >= 0.01:
        direction = 'more' if cost_delta > 0 else 'less'
        comparisons.append(f'${abs(cost_delta):.2f} {direction} expensive')

    if comparisons:
        summary = (
            f"Starting with {first_stop} instead produced a route that is "
            f"{' and '.join(comparisons)}."
        )
    else:
        summary = (
            f"Starting with {first_stop} instead produced the same distance, duration, and cost "
            f"under the same constraints."
        )

    return {
        'first_stop_warehouse_code': first_stop,
        'total_distance_km': float(alternative['total_distance_km']),
        'estimated_duration_min': int(alternative['estimated_duration_min']),
        'total_cost': float(alternative['total_cost']),
        'distance_delta_km': distance_delta,
        'duration_delta_min': duration_delta,
        'cost_delta': cost_delta,
        'summary': summary,
    }


def build_route_explanation(
    selected: dict[str, Any],
    alternative: dict[str, Any] | None,
    *,
    vehicle_capacity_units: int,
    max_stops: int,
) -> dict[str, Any]:
    trace = selected.get('decision_trace') or []
    totals = selected.get('factor_totals') or {
        'distance': 0.0,
        'time': 0.0,
        'cost': 0.0,
    }
    shares = _factor_shares(totals)
    dominant = _dominant_factor(totals)
    unassigned = selected.get('unassigned_deliveries') or []
    stops = selected.get('stops') or []

    constraints: list[str] = []
    # The same destination can be capacity-excluded at several decisions. The
    # optimizer reports the unique count once; summing per-decision values
    # would multiply that evidence and overstate the constraint.
    capacity_exclusions = int(selected.get('capacity_excluded_count') or 0)
    if capacity_exclusions:
        noun = 'target' if capacity_exclusions == 1 else 'targets'
        constraints.append(
            f"Vehicle capacity ({vehicle_capacity_units} units) excluded "
            f"{capacity_exclusions} distinct delivery {noun} during assignment."
        )
    remaining_capacity = max(
        int(vehicle_capacity_units) - int(selected.get('capacity_used') or 0),
        0,
    )
    capacity_blocked = [
        item
        for item in unassigned
        if int(item.get('demand_units') or 0) > remaining_capacity
    ]
    if capacity_blocked:
        noun = 'delivery' if len(capacity_blocked) == 1 else 'deliveries'
        constraints.append(
            f"Remaining vehicle capacity ({remaining_capacity} of "
            f"{vehicle_capacity_units} units) is too small for "
            f"{len(capacity_blocked)} unassigned {noun}."
        )
    if unassigned and len(stops) >= max_stops:
        constraints.append(f"The max_stops limit of {max_stops} was reached.")
    if unassigned:
        verb = 'delivery remained' if len(unassigned) == 1 else 'deliveries remained'
        constraints.append(
            f'{len(unassigned)} {verb} unassigned.'
        )

    if not trace:
        if not stops:
            summary = (
                'No delivery could be assigned to this route, so there is no stop-selection '
                'decision to explain. Review vehicle capacity, max stops, and delivery demand.'
            )
        else:
            summary = 'The run contains no decision trace from which to derive an explanation.'
    elif max(totals.values(), default=0.0) <= 0:
        summary = (
            'All route weights were zero, so no factor could dominate. Stops were assigned '
            'by the deterministic warehouse-code tie-break, subject to capacity and max stops.'
        )
    else:
        first = trace[0]
        summary = (
            f"{FACTOR_LABELS[dominant]} carried the largest share of the weighted objective "
            f"({shares[dominant]:.1f}%). The first stop was {first['chosen_warehouse_code']}"
        )
        if first.get('runner_up_warehouse_code') is not None:
            summary += (
                f", with {first['runner_up_warehouse_code']} the runner-up "
                f"{first['margin']:.2f} weighted points behind."
            )
        else:
            summary += ', and there was no runner-up at that decision.'

    decision_points = [
        {
            'sequence': int(item['sequence']),
            'chosen_warehouse_code': item['chosen_warehouse_code'],
            'chosen_weighted_cost': float(item['chosen_weighted_cost']),
            'runner_up_warehouse_code': item.get('runner_up_warehouse_code'),
            'runner_up_weighted_cost': (
                float(item['runner_up_weighted_cost'])
                if item.get('runner_up_weighted_cost') is not None
                else None
            ),
            'margin': float(item['margin']) if item.get('margin') is not None else None,
            'dominant_factor': item.get('dominant_factor', 'none'),
            'capacity_excluded_count': int(item.get('capacity_excluded_count') or 0),
            'reason': _decision_reason(item),
        }
        for item in trace
    ]

    return {
        'method': 'deterministic_weighted_greedy',
        'summary': summary,
        'dominant_factor': dominant,
        'factor_share_pct': shares,
        'constraints': constraints,
        'decision_points': decision_points,
        'runner_up': _alternative_summary(selected, alternative),
        'limitations': [
            'Derived from the same configured weights and persisted run inputs as the selected route.',
            'Explains each greedy choice; it does not prove global optimality.',
            'With a single speed and monetary cost per km, all weighted factors are proportional '
            'to leg distance; changing weights changes the objective value but not the '
            'nearest-stop ordering under these inputs.',
        ],
    }
