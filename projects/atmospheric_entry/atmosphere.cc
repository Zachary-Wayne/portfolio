/****
* Authors: Zachary Wayne
* License: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
*/

#include "atmosphere.h"

/**
 * Calculates the atmospheric properties at a given altitude based on planetary parameters.
 *
 * @param altitude        Altitude of the point in meters.
 * @param gravity         Gravitational acceleration of the planet in m/s^2.
 * @param planet_radius   Radius of the planet in meters.
 * @param composition     Composition of the atmosphere as a vector of ChemicalComposition structs.
 * @return                `AtmoProperties`
 *
 * @note
 * This function computes atmospheric pressure and temperature at the specified altitude.
 * Atmospheric pressure (P) is determined using the formula:
 * P = ρ * g * R * T / (M * R^2), where:
 * P = pressure, ρ = air density, g = gravitational acceleration,
 * R = gas constant, T = absolute temperature, M = molar mass of air.
 *
 * The absolute temperature (T) is calculated by:
 * T = 288.15 - (altitude / H), where:
 * T = temperature in Kelvin, altitude = altitude of the point,
 * H = scale height of the atmosphere.
 *
 * Scale height (H) of the atmosphere is calculated as:
 * H = (R * M) / (g * 1000), where:
 * R = gas constant, M = molar mass of the air at that altitude.
 */
AtmoProperties calculateAtmosphericProperties(float altitude, float gravity, float planet_radius, const std::vector<ChemicalComposition>& chemical_composition) {
    const float gas_constant = 8.314;
    float scale_height = (gas_constant * averageMolecularWeight(chemical_composition)) / (gravity * 1000);
    float temperature = 288.15 - (altitude / scale_height); // Hardcoded to 288.15 K (15°C) surface temperature
    std::vector<ChemicalComposition> normalized_composition;
    glm::vec3 total_flame_colour(0.0f); // TODO: Doesn't work quite right
    for (const auto& element : chemical_composition) {
        float concentration = element.percentage * exp(-altitude / scale_height) * element.atmo_element.molar_mass / averageMolecularWeight(chemical_composition);
        normalized_composition.push_back(ChemicalComposition{ element.atmo_element, concentration});
        total_flame_colour += element.atmo_element.flame_colour * concentration;
    }
    normalizePercentages(normalized_composition);
    glm::vec4 final_flame_colour = glm::vec4(total_flame_colour / 100.0f, 1.0f); // TODO: Doesn't work quite right
    float pressure = gravity * (planet_radius / (planet_radius + altitude));
    return AtmoProperties{pressure, temperature, normalized_composition, final_flame_colour};
}

// Calculate the average molecular weight of the atmosphere
float averageMolecularWeight(const std::vector<ChemicalComposition>& atmosphere_composition) {
    float total_molecular_weight = 0.0f;
    for (const auto& element : atmosphere_composition) {
        total_molecular_weight += element.percentage * element.atmo_element.molar_mass / 100.0f;
    }
    return total_molecular_weight;
}

// Function to normalize percentages to ensure they add up to 100
void normalizePercentages(std::vector<ChemicalComposition>& chemical_composition) {
    float total_percentage = 0.0f;
    for (const auto& composition : chemical_composition) {
        total_percentage += composition.percentage;
    }
    float normalization_factor = 100.0f / total_percentage;
    for (auto& composition : chemical_composition) {
        composition.percentage *= normalization_factor;
    }
}
