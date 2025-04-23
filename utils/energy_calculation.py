from typing import List, Dict, TypedDict, Optional
import math

# Type definitions
class Scenario(TypedDict):
    thresholds: List[float]
    score: float
    subcategoryId: int

class Subcategory(TypedDict):
    id: int

class Category(TypedDict):
    id: int
    subcategories: List[Subcategory]

class SubcategoryEnergy(TypedDict):
    capped: int
    uncapped: int

# Python equivalent of TierEnergies
TierEnergies = List[float]


def harmonic_mean(values: List[float]) -> float:
    """
    Calculate the harmonic mean of a list of values.
    Returns NaN if any value is less than or equal to 0.
    """
    if not all(value > 0 for value in values):
        return float('nan')

    return len(values) / sum(1 / value for value in values)


def generate_scenario_extended_thresholds(
        scenario: Scenario,
        current_tier_index: int
) -> List[float]:
    """
    Generate extended thresholds for a scenario.
    This adds a "ghost rank" threshold if we're not in the first tier
    and always adds a zero value at the start.
    """
    ghost_rank_threshold = scenario["thresholds"][0] - (scenario["thresholds"][1] - scenario["thresholds"][0])
    extended_thresholds = [0]

    if current_tier_index != 0:
        extended_thresholds.append(ghost_rank_threshold)

    extended_thresholds.extend(scenario["thresholds"])
    return extended_thresholds


def generate_extended_rank_energies(
        tiers: List[TierEnergies],
        current_tier_index: int
) -> List[float]:
    """
    Generate extended rank energies.
    This adds the highest energy from the previous tier if we're not in the first tier
    and always adds a zero value at the start.
    """
    extended_rank_energies = [0]

    if current_tier_index != 0:
        previous_tier_last_rank_energy = max(tiers[current_tier_index - 1])
        extended_rank_energies.append(previous_tier_last_rank_energy)

    extended_rank_energies.extend(tiers[current_tier_index])
    return extended_rank_energies


def find_last_index(lst: List, condition) -> int:
    """Python implementation of findLastIndex from JavaScript/TypeScript"""
    for i in range(len(lst) - 1, -1, -1):
        if condition(lst[i]):
            return i
    return -1


def uncapped_scenario_energy(
        scenario: Scenario,
        tiers: List[TierEnergies],
        current_tier_index: int
) -> float:
    """
    Calculate the uncapped energy for a scenario.
    """
    extended_thresholds = generate_scenario_extended_thresholds(scenario, current_tier_index)

    # Find the last index where threshold <= score
    scenario_extended_thresholds_index = find_last_index(
        extended_thresholds,
        lambda threshold: scenario["score"] >= threshold
    )

    extended_rank_energies = generate_extended_rank_energies(tiers, current_tier_index)
    scenario_extended_rank_energy = extended_rank_energies[scenario_extended_thresholds_index]

    score_above_threshold = scenario["score"] - extended_thresholds[scenario_extended_thresholds_index]

    # Calculate threshold differences (equivalent to the map in TypeScript)
    extended_threshold_differences = []
    for i in range(len(extended_thresholds)):
        if i == len(extended_thresholds) - 1:
            extended_threshold_differences.append(extended_thresholds[i] - extended_thresholds[i - 1])
        else:
            extended_threshold_differences.append(extended_thresholds[i + 1] - extended_thresholds[i])

    scenario_extended_threshold_difference = extended_threshold_differences[scenario_extended_thresholds_index]

    # Calculate energy differences (equivalent to the map in TypeScript)
    extended_rank_energies_differences = []
    for i in range(len(extended_rank_energies)):
        if i == len(extended_rank_energies) - 1:
            extended_rank_energies_differences.append(extended_rank_energies[i] - extended_rank_energies[i - 1])
        else:
            extended_rank_energies_differences.append(extended_rank_energies[i + 1] - extended_rank_energies[i])

    scenario_extended_rank_energy_difference = extended_rank_energies_differences[scenario_extended_thresholds_index]

    # Linearly interpolate between energy levels based on score
    return (
            scenario_extended_rank_energy +
            score_above_threshold / scenario_extended_threshold_difference *
            scenario_extended_rank_energy_difference
    )


def subcategory_energy(
        tiers: List[TierEnergies],
        current_tier_index: int,
        scenarios: List[Scenario]
) -> SubcategoryEnergy:
    """
    Calculate the energy for a subcategory based on its scenarios.
    """
    # Maximum possible energy for the current tier
    if current_tier_index == len(tiers) - 1:
        max_energy = max(tiers[current_tier_index])
    else:
        max_energy = tiers[current_tier_index + 1][0] - 1

    # Calculate energies for all scenarios in this subcategory
    scenarios_energies = [
        uncapped_scenario_energy(scenario, tiers, current_tier_index)
        for scenario in scenarios
    ]

    return {
        "capped": math.floor(min(max_energy, max(scenarios_energies)) if scenarios_energies else 0),
        "uncapped": math.floor(max(scenarios_energies) if scenarios_energies else 0)
    }


def harmonic_mean_of_subcategory_energies(
        subcategory_energies: List[SubcategoryEnergy],
        tiers: List[TierEnergies]
) -> float:
    """
    Calculate the harmonic mean of subcategory energies.
    """
    capped_values = [subcategory_energy["capped"] for subcategory_energy in subcategory_energies]
    uncapped_values = [subcategory_energy["uncapped"] for subcategory_energy in subcategory_energies]

    capped = harmonic_mean(capped_values)
    uncapped = harmonic_mean(uncapped_values)

    # If capped energy exceeds the highest tier threshold, return uncapped energy
    if capped >= max(tiers[len(tiers) - 1]):
        return 0 if math.isnan(uncapped) else math.floor(uncapped)

    return 0 if math.isnan(capped) else math.floor(capped)


def tier_energy(
        tiers: List[TierEnergies],
        current_tier_index: int,
        scenarios: List[Scenario],
        categories: List[Category]
) -> float:
    """
    Calculate the overall energy for a tier based on all categories and subcategories.
    """
    subcategory_energies = []

    for category in categories:
        for subcategory in category["subcategories"]:
            # Filter scenarios that belong to this subcategory
            subcategory_scenarios = [
                scenario for scenario in scenarios
                if scenario["subcategoryId"] == subcategory["id"]
            ]

            # Add this subcategory's energy to our list
            subcategory_energies.append(
                subcategory_energy(tiers, current_tier_index, subcategory_scenarios)
            )

    # Calculate harmonics mean across all subcategories
    return harmonic_mean_of_subcategory_energies(subcategory_energies, tiers)
