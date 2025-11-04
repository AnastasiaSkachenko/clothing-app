# Temporal State Management Integration

This document describes how Temporal has been integrated into the clothing app for managing application state, particularly for image processing workflows.

## Overview

Temporal is now integrated to manage stateful workflows in your application, providing:
- **Reliable state management** with automatic retries and failure recovery
- **Workflow visibility** to track processing status
- **Durability** - workflows survive application restarts
- **Scalability** - distribute work across workers

## Infrastructure

### Services Added

1. **Temporal Server** (`temporal`) - Running on port 7233
2. **Temporal UI** (`temporal-ui`) - Web interface on port 8233
3. **PostgreSQL** (`postgres`) - Backend storage for Temporal

Access the Temporal UI at: http://localhost:8233

## Workflow: Image Processing

The `ImageProcessingWorkflow` manages the lifecycle of image processing with the following steps:

1. **Store Metadata** - Saves image URL and metadata to Couchbase
2. **Visual Similarity Search** - Optionally runs Lykdat API search
3. **State Tracking** - Maintains processing status throughout

### Workflow Features

- **Automatic Retries**: Failed activities retry with exponential backoff
- **State Queries**: Check workflow status at any time
- **Error Handling**: Graceful failure with error reporting
- **Cancellation**: Support for workflow cancellation signals

## API Endpoints

### Start Image Processing Workflow

```http
POST /images/process
Content-Type: application/json

{
  "url": "https://example.com/image.jpg",
  "title": "Product Image",
  "description": "Blue shirt",
  "tags": ["clothing", "shirt"]
}
```

**Response** (202 Accepted):
```json
{
  "workflow_id": "image-processing-550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Image processing workflow started successfully"
}
```

### Get Workflow Status

```http
GET /images/workflow/{workflow_id}/status
```

**Response**:
```json
{
  "workflow_id": "image-processing-550e8400-e29b-41d4-a716-446655440000",
  "state": {
    "image_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "metadata_stored": true,
    "similarity_search_completed": true,
    "error": null
  }
}
```

### Get Workflow Result

```http
GET /images/workflow/{workflow_id}/result
```

Waits for workflow completion and returns final result.

## File Structure

```
modules/api/src/backend/
├── workflows/
│   ├── __init__.py              # Workflow registry
│   └── image_processing.py       # Image processing workflow & activities
├── init/
│   └── temporal.py              # Temporal client initialization
└── conf/
    └── temporal.py              # Temporal configuration

lib/py/temporal-client/          # Temporal client library
```

## Configuration

Temporal configuration is managed through environment variables:

```bash
TEMPORAL_HOST=temporal           # Temporal server hostname
TEMPORAL_PORT=7233               # gRPC port
TEMPORAL_NAMESPACE=default       # Workflow namespace
TEMPORAL_TASK_QUEUE=main-task-queue  # Task queue name
```

## Activities

### `store_image_metadata`
Stores image metadata in Couchbase.

**Parameters**:
- `url`: Image URL
- `title`: Optional title
- `description`: Optional description
- `tags`: List of tags

**Returns**: Image ID (UUID as string)

**Retry Policy**:
- Max attempts: 3
- Initial interval: 1s
- Max interval: 10s
- Backoff coefficient: 2.0

### `run_similarity_search`
Performs visual similarity search using Lykdat API.

**Parameters**:
- `image_id`: Image identifier
- `image_url`: Image URL for search

**Returns**: Search results dictionary

**Retry Policy**:
- Max attempts: 3
- Initial interval: 2s
- Max interval: 20s
- Backoff coefficient: 2.0

## Development

### Adding New Workflows

1. Use the Polytope tool to scaffold a new workflow:
```bash
polytope run api-add-temporal-workflow --name my_workflow
```

2. Implement your workflow in `modules/api/src/backend/workflows/my_workflow.py`

3. Register it in `modules/api/src/backend/workflows/__init__.py`:
```python
from .my_workflow import MyWorkflow

WORKFLOWS = [
    ImageProcessingWorkflow,
    MyWorkflow,  # Add your workflow
]
```

4. Register activities in `modules/api/src/backend/init/temporal.py`

### Monitoring Workflows

1. **Temporal UI**: Visit http://localhost:8233
   - View all workflows
   - See execution history
   - Query workflow state
   - Inspect activity results

2. **Application Logs**: Check API container logs
```bash
polytope logs api
```

### Debugging

If workflows fail to validate:
- Check that workflow methods use proper Temporal decorators (@workflow.defn, @workflow.run)
- Ensure activities are decorated with @activity.defn  
- Verify parameter types are JSON-serializable
- Review logs for validation errors

## Benefits of Temporal State Management

1. **Reliability**: Workflows automatically recover from failures
2. **Visibility**: Track processing status in real-time
3. **Scalability**: Add more workers to handle increased load
4. **Maintainability**: Workflow code is separate from business logic
5. **Testability**: Workflows can be tested in isolation
6. **Versioning**: Support multiple workflow versions simultaneously

## Next Steps

1. **Implement Couchbase persistence** in `store_image_metadata` activity
2. **Add more workflows** for other stateful operations
3. **Set up monitoring** with Temporal metrics
4. **Configure production settings** (authentication, encryption, etc.)
5. **Scale workers** based on workload demands

## Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal UI](http://localhost:8233)
- [Workflow Best Practices](https://docs.temporal.io/dev-guide/python/foundations)
