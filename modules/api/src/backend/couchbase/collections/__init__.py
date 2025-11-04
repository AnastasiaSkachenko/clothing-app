"""
Couchbase collections registry.

All collections are automatically registered here.
"""

# Import collections here
# Example:
# from .users import UserCollection

# Registry of all collections

from .images import ImagesCollection
COLLECTIONS = [
    # Add collection classes here
    # Example: UserCollection
    ImagesCollection,
]
