"""
Travel Provider Implementations

Providers are auto-discovered and loaded dynamically.
No need to import them here!

To add a new provider:
1. Create a new file: my_provider.py
2. Use the @ProviderRegistry.register_hotel_provider("name") or
   @ProviderRegistry.register_flight_provider("name") decorator
3. That's it! No code changes needed here.

Example providers:
- mock_provider.py: For testing (returns mock data)

Future providers (just create the file):
- booking_provider.py: Booking.com integration
- expedia_provider.py: Expedia integration
- skyscanner_provider.py: Skyscanner integration
- amadeus_provider.py: Amadeus integration
"""
