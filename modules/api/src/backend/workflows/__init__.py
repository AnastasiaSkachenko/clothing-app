"""
Temporal workflows registry.

All workflows are automatically registered here.
"""

# Import workflows here
# They will be auto-added by the add-temporal-workflow tool
from .image_processing import ImageProcessingWorkflow

# Registry of all workflows
WORKFLOWS = [
    ImageProcessingWorkflow,
]
