/**
 * Geo-location utilities
 * Note: Country detection is now handled by the backend via IP address
 * This file is kept for potential future client-side detection needs
 */

/**
 * Clear cached country code (useful for testing or manual override)
 */
export function clearCountryCache(): void {
  localStorage.removeItem('user_country_code');
}
