# Enterprise Search Deployment Guide

## Introduction

This guide walks you through deploying the Enterprise Search with Ollama, Qdrant, and Redis on Kubernetes. It covers the process from building the Docker images to deploying them using Helm.

## Prerequisites

- Docker
- Kubernetes cluster
- Helm 3
- kubectl

## Steps

### 1. Docker Build

First, build the Docker images for your application components. Replace `llamasearch` with each application component name (e.g., Ollama, Qdrant).

```bash
docker build -t docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest .
```

### 2. Docker Test

Test your Docker images to ensure they are working as expected. Typically you might want to check if there is no startup errors with the docker.

```bash
docker-compose up
```

### 3. Docker Push

Push the built images to your AIML Docker registry:

```bash
docker push docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest
```

### 4. Create Persistent Volume Claim (PVC)

Deploy the PVC to persistent storage to store data and models:

```bash
kubectl apply -f k8s/pvc.yaml
```

### 5. Create Config Map

Deploy the ConfigMap to provide configuration for enterprise search RAG pipeline:

```bash
kubectl apply -f k8s/config-map.yaml
```

### 6. Create Collection Config Map

Deploy the ConfigMap to create collection in the vector database using the parameters from the configuration:

```bash
kubectl apply -f k8s/create-collection-script.yaml
```

### 7. Helm Values File

Below is a table explaining the variables for each service (`app`, `ollama`, `qdrant`, and `redis`) based on the configuration snippet you've provided. Each row in the table corresponds to a variable in the configuration, detailing its key, type, default value (if applicable), and a brief description.

| Key | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| **Common to All Services** | | | |
| name | String | (varies) | The name of the service. |
| namespace | String | aiml-engineering | The Kubernetes namespace in which the service is deployed. Applicable to `ollama`, might be assumed for others if not explicitly set. |
| image.repository | String | (varies) | The Docker image repository. |
| image.tag | String | latest | The Docker image tag. |
| image.pullPolicy | String | Always | The image pull policy. |
| service.type | String | ClusterIP | The type of service to expose. |
| service.port | Integer | (varies) | The port on which the service is exposed within the cluster. |
| resources.limits.cpu | String | (varies) | The maximum amount of CPU that the service can use. |
| resources.limits.memory | String | (varies) | The maximum amount of memory that the service can use. |
| nodeName | String | (varies) | The name of the node on which the service should run. |
| **App Specific** | | | |
| app.env.CONFIG_PATH | String | `/app/config/config.yml` | The path to the configuration file within the container. |
| app.env.OLLAMA_SERVER_URL | String | `ollama-es-service.aiml-engineering.svc.cluster.local:80` | The URL for the Ollama server. |
| app.volumes.config.configMapName | String | `es-cmap` | The name of the ConfigMap containing app configuration. |
| app.volumes.data.pvcName | String | `es-pvc` | The name of the Persistent Volume Claim for app data. |
| **Ollama Specific** | | | |
| ollama.env.OLLAMA_HOST | String | `0.0.0.0` | The host IP Ollama listens on. |
| ollama.gpu.enabled | Boolean | true | Indicates if GPU integration is enabled. |
| ollama.gpu.type | String | `nvidia` | The type of GPU used (`nvidia` or `amd`). |
| ollama.gpu.number | Integer | 1 | The number of GPUs allocated. |
| ollama.models | List | `[gemma, mistral:7b-instruct, mixtral]` | The list of models to pull at container startup. |
| ollama.insecure | Boolean | true | Indicates if the service runs in insecure mode. |
| **Qdrant Specific** | | | |
| qdrant.collectionName | String | `test` | The name of the collection to use in Qdrant. |
| qdrant.vectorSize | Integer | 384 | The size of the vectors in the collection. |
| qdrant.distance | String | `Cosine` | The distance metric used by the vector search. |
| **Redis Specific** | | | |
| (No additional specific variables) | | | |

Note: The table focuses on variables explicitly mentioned in your snippet. Some services (like Redis) don't have specific variables detailed beyond the common keys shared across all services.

### 8. Helm Chart Installation

Navigate to your Helm chart directory:

```bash
cd k8s/
```

If installing for the first time, use:

```bash
helm install enterprise-search . --values values.yaml
```

For upgrading an existing deployment, use:

```bash
helm upgrade enterprise-search . --values values.yaml
```

To list the helm deployment, use:

```bash
helm list
```

To uninstall, use:

```bash
helm uninstall enterprise-search
```

### 9. Review Deployment Status

Key things to consider when monitoring and testing the deployment

1. The app deployment initially waits for the ollama server to be up and ready. For the first time, it may take
longer as it may pull the models based on the model list in the values.yaml
2. All the pods should be in running state before we can hit the endpoint.
Check the status of your deployment using `kubectl`:

```bash
kubectl get pods,svc -n aiml-engineering
```

Monitor your pods until all are in the `Running` state. You might also want to check the logs for any errors or important messages:

```bash
kubectl logs <pod-name>
```

### 10. Test the Deployment

After deploying the Enterprise Search with Ollama, Qdrant, and Redis on Kubernetes, ensure the system functions as expected by testing the deployment.

#### Steps to Test:

1. **Set Up Port Forwarding**: Forward local port 8000 to the service port of enterprise-search pod on Kubernetes to communicate with the deployed API.

   ```bash
   kubectl port-forward <pod-name> 8000:8000 -n aiml-engineering
   ```

2. **Run the Test Script**: Use `es_api_test.sh` to test a query operation. Make the script executable and run it with a query and a document path as arguments.

   ```bash
   chmod +x k8s/es_api_test.sh
   ./k8s/es_api_test.sh "Your query here" "/path/to/document.pdf"
   ```
Certainly! Presenting the API endpoint information in a table format can make it easier to read and quickly reference. Here’s a concise and structured representation of your API endpoint in a Markdown table format:

#### API Endpoint Definition using Curl

---

#### **POST** `/query/`

Submits a query along with an optional document for processing, and retrieves search results.

| Attribute      | Description                                                      |
| -------------- | ---------------------------------------------------------------- |
| **URL**        | `http://127.0.0.1:8000/query/`                                   |
| **Method**     | `POST`                                                           |
| **URL Params** | None                                                             |
| **Data Params**| `query` (String, required), `file` (File, optional, .pdf)        |
| **Headers**    | `Accept: application/json`, `Content-Type: multipart/form-data`  |

##### Request Example

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'query=What is the vision of BCG for year 2023?' \
  -F 'file=@data/test_data/bcg-2022-annual-sustainability-report-apr-2023.pdf'
```

#### Description of Data Parameters

| Parameter | Required | Type   | Description                                         |
| --------- | -------- | ------ | --------------------------------------------------- |
| `query`   | Yes      | String | The search query to be processed.                   |
| `file`    | No       | File   | A document file (.pdf) to be processed along query. |

#### Responses

| Status Code | Content Type | Description                                                      |
| ----------- | ------------ | ---------------------------------------------------------------- |
| 200 OK      | `application/json` | Returns results based on the query and document contents.       |
| 400 BAD REQUEST | `application/json` | Indicates a request format error or missing required fields.    |
| 500 INTERNAL SERVER ERROR | `application/json` | Indicates an error during processing of the query.              |

This structured format provides a quick overview and detailed descriptions of the API endpoint’s specifications, making it easy for developers to understand and integrate with the API.

### Limitations

- The deployment supports single file upload per API call.
- It does not have user state so whatever you upload stays in server with other user's files.
- It does not support a front-end (GUI)

### Troubleshooting:

- **Port Forwarding Issues**: Ensure all the pods(enterprise-search, ollama, qdrant and redis) are in the `Running` state and then forward the port of the enterprise-search pod to interact with the API.
- **Script Execution**: Verify the script's path and ensure it has execution permissions.
- **Performance**: Initial requests may take longer due to model loading times; subsequent requests should be faster.

If you encounter issues, check the logs for specific pods using `kubectl logs`, and ensure your Kubernetes cluster has enough resources to support your deployment.