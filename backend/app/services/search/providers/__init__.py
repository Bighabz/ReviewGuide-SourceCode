"""
Search Provider Implementations

Providers are loaded on-demand based on configuration.
Only the provider specified in config/search.yaml is imported.

To add a new provider:
1. Create a new file: my_provider_provider.py (e.g., tavily_provider.py)
2. Use the @SearchProviderRegistry.register("my_provider") decorator
3. Update config/search.yaml to use it:
   search_provider:
     name: my_provider

Example:
- perplexity_provider.py → name: "perplexity"
- tavily_provider.py → name: "tavily"
- bing_provider.py → name: "bing"
"""
