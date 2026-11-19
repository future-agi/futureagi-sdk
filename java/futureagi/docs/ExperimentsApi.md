# ExperimentsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**compareExperiments**](ExperimentsApi.md#compareExperiments) | **POST** /model-hub/experiments/v2/{experiment_id}/compare-experiments/ |  |
| [**compareExperimentsWithHttpInfo**](ExperimentsApi.md#compareExperimentsWithHttpInfo) | **POST** /model-hub/experiments/v2/{experiment_id}/compare-experiments/ |  |
| [**createExperiment**](ExperimentsApi.md#createExperiment) | **POST** /model-hub/experiments/v2/ |  |
| [**createExperimentWithHttpInfo**](ExperimentsApi.md#createExperimentWithHttpInfo) | **POST** /model-hub/experiments/v2/ |  |
| [**deleteExperiments**](ExperimentsApi.md#deleteExperiments) | **DELETE** /model-hub/experiments/v2/delete/ |  |
| [**deleteExperimentsWithHttpInfo**](ExperimentsApi.md#deleteExperimentsWithHttpInfo) | **DELETE** /model-hub/experiments/v2/delete/ |  |
| [**downloadExperiment**](ExperimentsApi.md#downloadExperiment) | **GET** /model-hub/experiments/v2/{experiment_id}/download/ |  |
| [**downloadExperimentWithHttpInfo**](ExperimentsApi.md#downloadExperimentWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/download/ |  |
| [**getExperiment**](ExperimentsApi.md#getExperiment) | **GET** /model-hub/experiments/v2/{experiment_id}/ |  |
| [**getExperimentWithHttpInfo**](ExperimentsApi.md#getExperimentWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/ |  |
| [**getExperimentJsonSchema**](ExperimentsApi.md#getExperimentJsonSchema) | **GET** /model-hub/experiments/v2/{experiment_id}/json-schema/ |  |
| [**getExperimentJsonSchemaWithHttpInfo**](ExperimentsApi.md#getExperimentJsonSchemaWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/json-schema/ |  |
| [**getExperimentRow**](ExperimentsApi.md#getExperimentRow) | **GET** /model-hub/experiments/v2/{experiment_id}/rows/{row_id}/ |  |
| [**getExperimentRowWithHttpInfo**](ExperimentsApi.md#getExperimentRowWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/rows/{row_id}/ |  |
| [**getExperimentStats**](ExperimentsApi.md#getExperimentStats) | **GET** /model-hub/experiments/v2/{experiment_id}/stats/ |  |
| [**getExperimentStatsWithHttpInfo**](ExperimentsApi.md#getExperimentStatsWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/stats/ |  |
| [**listExperimentComparisons**](ExperimentsApi.md#listExperimentComparisons) | **GET** /model-hub/experiments/v2/{experiment_id}/comparisons/ |  |
| [**listExperimentComparisonsWithHttpInfo**](ExperimentsApi.md#listExperimentComparisonsWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/comparisons/ |  |
| [**listExperimentRows**](ExperimentsApi.md#listExperimentRows) | **GET** /model-hub/experiments/v2/{experiment_id}/rows/ |  |
| [**listExperimentRowsWithHttpInfo**](ExperimentsApi.md#listExperimentRowsWithHttpInfo) | **GET** /model-hub/experiments/v2/{experiment_id}/rows/ |  |
| [**listExperiments**](ExperimentsApi.md#listExperiments) | **GET** /model-hub/experiments/v2/list/ |  |
| [**listExperimentsWithHttpInfo**](ExperimentsApi.md#listExperimentsWithHttpInfo) | **GET** /model-hub/experiments/v2/list/ |  |
| [**rerunExperiment**](ExperimentsApi.md#rerunExperiment) | **POST** /model-hub/experiments/v2/re-run/ | V2 re-run: org-scoped, uses V2 Temporal workflow. |
| [**rerunExperimentWithHttpInfo**](ExperimentsApi.md#rerunExperimentWithHttpInfo) | **POST** /model-hub/experiments/v2/re-run/ | V2 re-run: org-scoped, uses V2 Temporal workflow. |
| [**stopExperiment**](ExperimentsApi.md#stopExperiment) | **POST** /model-hub/experiments/v2/{experiment_id}/stop/ | Stop a running V2 experiment. |
| [**stopExperimentWithHttpInfo**](ExperimentsApi.md#stopExperimentWithHttpInfo) | **POST** /model-hub/experiments/v2/{experiment_id}/stop/ | Stop a running V2 experiment. |
| [**updateExperiment**](ExperimentsApi.md#updateExperiment) | **PUT** /model-hub/experiments/v2/{experiment_id}/ | Update a V2 experiment with diff-based selective re-run. |
| [**updateExperimentWithHttpInfo**](ExperimentsApi.md#updateExperimentWithHttpInfo) | **PUT** /model-hub/experiments/v2/{experiment_id}/ | Update a V2 experiment with diff-based selective re-run. |



## compareExperiments

> ExperimentDatasetComparisonResponse compareExperiments(experimentId, experimentComparisonWeightsRequest)



V2 compare view: reads from experiment_datasets FK + snapshot_dataset.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        ExperimentComparisonWeightsRequest experimentComparisonWeightsRequest = new ExperimentComparisonWeightsRequest(); // ExperimentComparisonWeightsRequest | 
        try {
            ExperimentDatasetComparisonResponse result = apiInstance.compareExperiments(experimentId, experimentComparisonWeightsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#compareExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **experimentComparisonWeightsRequest** | [**ExperimentComparisonWeightsRequest**](ExperimentComparisonWeightsRequest.md)|  | |

### Return type

[**ExperimentDatasetComparisonResponse**](ExperimentDatasetComparisonResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## compareExperimentsWithHttpInfo

> ApiResponse<ExperimentDatasetComparisonResponse> compareExperiments compareExperimentsWithHttpInfo(experimentId, experimentComparisonWeightsRequest)



V2 compare view: reads from experiment_datasets FK + snapshot_dataset.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        ExperimentComparisonWeightsRequest experimentComparisonWeightsRequest = new ExperimentComparisonWeightsRequest(); // ExperimentComparisonWeightsRequest | 
        try {
            ApiResponse<ExperimentDatasetComparisonResponse> response = apiInstance.compareExperimentsWithHttpInfo(experimentId, experimentComparisonWeightsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#compareExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **experimentComparisonWeightsRequest** | [**ExperimentComparisonWeightsRequest**](ExperimentComparisonWeightsRequest.md)|  | |

### Return type

ApiResponse<[**ExperimentDatasetComparisonResponse**](ExperimentDatasetComparisonResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## createExperiment

> ExperimentStringResultResponse createExperiment(experimentCreateV2)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        ExperimentCreateV2 experimentCreateV2 = new ExperimentCreateV2(); // ExperimentCreateV2 | 
        try {
            ExperimentStringResultResponse result = apiInstance.createExperiment(experimentCreateV2);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#createExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentCreateV2** | [**ExperimentCreateV2**](ExperimentCreateV2.md)|  | |

### Return type

[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## createExperimentWithHttpInfo

> ApiResponse<ExperimentStringResultResponse> createExperiment createExperimentWithHttpInfo(experimentCreateV2)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        ExperimentCreateV2 experimentCreateV2 = new ExperimentCreateV2(); // ExperimentCreateV2 | 
        try {
            ApiResponse<ExperimentStringResultResponse> response = apiInstance.createExperimentWithHttpInfo(experimentCreateV2);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#createExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentCreateV2** | [**ExperimentCreateV2**](ExperimentCreateV2.md)|  | |

### Return type

ApiResponse<[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## deleteExperiments

> void deleteExperiments()



V2 delete: org-scoped, cancels workflows, cleans up columns &amp; EDTs.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        try {
            apiInstance.deleteExperiments();
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#deleteExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type


null (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **0** | Default error response |  -  |

## deleteExperimentsWithHttpInfo

> ApiResponse<Void> deleteExperiments deleteExperimentsWithHttpInfo()



V2 delete: org-scoped, cancels workflows, cleans up columns &amp; EDTs.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        try {
            ApiResponse<Void> response = apiInstance.deleteExperimentsWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#deleteExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type


ApiResponse<Void>

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **0** | Default error response |  -  |


## downloadExperiment

> File downloadExperiment(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            File result = apiInstance.downloadExperiment(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#downloadExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**File**](File.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## downloadExperimentWithHttpInfo

> ApiResponse<File> downloadExperiment downloadExperimentWithHttpInfo(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<File> response = apiInstance.downloadExperimentWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#downloadExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**File**](File.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getExperiment

> ExperimentV2DetailResponse getExperiment(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ExperimentV2DetailResponse result = apiInstance.getExperiment(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getExperimentWithHttpInfo

> ApiResponse<ExperimentV2DetailResponse> getExperiment getExperimentWithHttpInfo(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<ExperimentV2DetailResponse> response = apiInstance.getExperimentWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getExperimentJsonSchema

> ExperimentJsonSchemaResponse getExperimentJsonSchema(experimentId)



Get JSON schemas and images metadata for columns in an experiment&#39;s snapshot dataset. Delegates to the shared get_json_column_schemas() function.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ExperimentJsonSchemaResponse result = apiInstance.getExperimentJsonSchema(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentJsonSchema");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**ExperimentJsonSchemaResponse**](ExperimentJsonSchemaResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getExperimentJsonSchemaWithHttpInfo

> ApiResponse<ExperimentJsonSchemaResponse> getExperimentJsonSchema getExperimentJsonSchemaWithHttpInfo(experimentId)



Get JSON schemas and images metadata for columns in an experiment&#39;s snapshot dataset. Delegates to the shared get_json_column_schemas() function.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<ExperimentJsonSchemaResponse> response = apiInstance.getExperimentJsonSchemaWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentJsonSchema");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentJsonSchemaResponse**](ExperimentJsonSchemaResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getExperimentRow

> ExperimentTableRowsResponse getExperimentRow(experimentId, rowId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        String rowId = "rowId_example"; // String | 
        try {
            ExperimentTableRowsResponse result = apiInstance.getExperimentRow(experimentId, rowId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentRow");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **rowId** | **String**|  | |

### Return type

[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getExperimentRowWithHttpInfo

> ApiResponse<ExperimentTableRowsResponse> getExperimentRow getExperimentRowWithHttpInfo(experimentId, rowId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        String rowId = "rowId_example"; // String | 
        try {
            ApiResponse<ExperimentTableRowsResponse> response = apiInstance.getExperimentRowWithHttpInfo(experimentId, rowId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentRow");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **rowId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getExperimentStats

> ExperimentStatsResponse getExperimentStats(experimentId)



Stats view for V2 experiments that read from snapshot_dataset.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ExperimentStatsResponse result = apiInstance.getExperimentStats(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentStats");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**ExperimentStatsResponse**](ExperimentStatsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getExperimentStatsWithHttpInfo

> ApiResponse<ExperimentStatsResponse> getExperimentStats getExperimentStatsWithHttpInfo(experimentId)



Stats view for V2 experiments that read from snapshot_dataset.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<ExperimentStatsResponse> response = apiInstance.getExperimentStatsWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#getExperimentStats");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentStatsResponse**](ExperimentStatsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listExperimentComparisons

> ExperimentComparisonDetailsResponse listExperimentComparisons(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ExperimentComparisonDetailsResponse result = apiInstance.listExperimentComparisons(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperimentComparisons");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**ExperimentComparisonDetailsResponse**](ExperimentComparisonDetailsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listExperimentComparisonsWithHttpInfo

> ApiResponse<ExperimentComparisonDetailsResponse> listExperimentComparisons listExperimentComparisonsWithHttpInfo(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<ExperimentComparisonDetailsResponse> response = apiInstance.listExperimentComparisonsWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperimentComparisons");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentComparisonDetailsResponse**](ExperimentComparisonDetailsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listExperimentRows

> ExperimentTableRowsResponse listExperimentRows(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ExperimentTableRowsResponse result = apiInstance.listExperimentRows(experimentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperimentRows");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listExperimentRowsWithHttpInfo

> ApiResponse<ExperimentTableRowsResponse> listExperimentRows listExperimentRowsWithHttpInfo(experimentId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        try {
            ApiResponse<ExperimentTableRowsResponse> response = apiInstance.listExperimentRowsWithHttpInfo(experimentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperimentRows");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |

### Return type

ApiResponse<[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listExperiments

> ListExperiments200Response listExperiments(createdAt, status, datasetId, search, ordering, page, limit)



V2 experiment list with filtering, search, and pagination.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String createdAt = "createdAt_example"; // String | 
        String status = "status_example"; // String | 
        String datasetId = "datasetId_example"; // String | 
        String search = "search_example"; // String | A search term.
        String ordering = "ordering_example"; // String | Which field to use when ordering the results.
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ListExperiments200Response result = apiInstance.listExperiments(createdAt, status, datasetId, search, ordering, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **createdAt** | **String**|  | [optional] |
| **status** | **String**|  | [optional] |
| **datasetId** | **String**|  | [optional] |
| **search** | **String**| A search term. | [optional] |
| **ordering** | **String**| Which field to use when ordering the results. | [optional] |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**ListExperiments200Response**](ListExperiments200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## listExperimentsWithHttpInfo

> ApiResponse<ListExperiments200Response> listExperiments listExperimentsWithHttpInfo(createdAt, status, datasetId, search, ordering, page, limit)



V2 experiment list with filtering, search, and pagination.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String createdAt = "createdAt_example"; // String | 
        String status = "status_example"; // String | 
        String datasetId = "datasetId_example"; // String | 
        String search = "search_example"; // String | A search term.
        String ordering = "ordering_example"; // String | Which field to use when ordering the results.
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<ListExperiments200Response> response = apiInstance.listExperimentsWithHttpInfo(createdAt, status, datasetId, search, ordering, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#listExperiments");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **createdAt** | **String**|  | [optional] |
| **status** | **String**|  | [optional] |
| **datasetId** | **String**|  | [optional] |
| **search** | **String**| A search term. | [optional] |
| **ordering** | **String**| Which field to use when ordering the results. | [optional] |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**ListExperiments200Response**](ListExperiments200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## rerunExperiment

> ExperimentStringResultResponse rerunExperiment(experimentRerunRequest)

V2 re-run: org-scoped, uses V2 Temporal workflow.

No manual workflow cancel needed — Temporal&#39;s TERMINATE_IF_RUNNING ID reuse policy automatically cancels any running workflow with the same ID. Cell reset is handled by the workflow itself (cleanup + setup activities).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        ExperimentRerunRequest experimentRerunRequest = new ExperimentRerunRequest(); // ExperimentRerunRequest | 
        try {
            ExperimentStringResultResponse result = apiInstance.rerunExperiment(experimentRerunRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#rerunExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentRerunRequest** | [**ExperimentRerunRequest**](ExperimentRerunRequest.md)|  | |

### Return type

[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## rerunExperimentWithHttpInfo

> ApiResponse<ExperimentStringResultResponse> rerunExperiment rerunExperimentWithHttpInfo(experimentRerunRequest)

V2 re-run: org-scoped, uses V2 Temporal workflow.

No manual workflow cancel needed — Temporal&#39;s TERMINATE_IF_RUNNING ID reuse policy automatically cancels any running workflow with the same ID. Cell reset is handled by the workflow itself (cleanup + setup activities).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        ExperimentRerunRequest experimentRerunRequest = new ExperimentRerunRequest(); // ExperimentRerunRequest | 
        try {
            ApiResponse<ExperimentStringResultResponse> response = apiInstance.rerunExperimentWithHttpInfo(experimentRerunRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#rerunExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentRerunRequest** | [**ExperimentRerunRequest**](ExperimentRerunRequest.md)|  | |

### Return type

ApiResponse<[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## stopExperiment

> ExperimentStopResponse stopExperiment(experimentId, body)

Stop a running V2 experiment.

Cancels all Temporal workflows (main + reruns). DB cleanup (marking RUNNING cells as ERROR, columns/EDTs as FAILED, experiment as CANCELLED) is handled by each workflow&#39;s CancelledError handler via the stop_experiment_cleanup_activity.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        Object body = null; // Object | 
        try {
            ExperimentStopResponse result = apiInstance.stopExperiment(experimentId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#stopExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**ExperimentStopResponse**](ExperimentStopResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## stopExperimentWithHttpInfo

> ApiResponse<ExperimentStopResponse> stopExperiment stopExperimentWithHttpInfo(experimentId, body)

Stop a running V2 experiment.

Cancels all Temporal workflows (main + reruns). DB cleanup (marking RUNNING cells as ERROR, columns/EDTs as FAILED, experiment as CANCELLED) is handled by each workflow&#39;s CancelledError handler via the stop_experiment_cleanup_activity.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<ExperimentStopResponse> response = apiInstance.stopExperimentWithHttpInfo(experimentId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#stopExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**ExperimentStopResponse**](ExperimentStopResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## updateExperiment

> ExperimentV2DetailResponse updateExperiment(experimentId, experimentUpdateV2)

Update a V2 experiment with diff-based selective re-run.

Editable fields: column_id, prompt_config, user_eval_metrics. Re-run triggers (determined by fingerprint diffs, not field presence): - prompt_config has new/modified entries → re-run those configs + ALL dependent evals - user_eval_metrics has new/modified entries → re-run only those evals - column_id changed → delete old base eval columns, re-run base evals - If FE sends unchanged data, diffs return empty → no re-run

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        ExperimentUpdateV2 experimentUpdateV2 = new ExperimentUpdateV2(); // ExperimentUpdateV2 | 
        try {
            ExperimentV2DetailResponse result = apiInstance.updateExperiment(experimentId, experimentUpdateV2);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#updateExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **experimentUpdateV2** | [**ExperimentUpdateV2**](ExperimentUpdateV2.md)|  | |

### Return type

[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## updateExperimentWithHttpInfo

> ApiResponse<ExperimentV2DetailResponse> updateExperiment updateExperimentWithHttpInfo(experimentId, experimentUpdateV2)

Update a V2 experiment with diff-based selective re-run.

Editable fields: column_id, prompt_config, user_eval_metrics. Re-run triggers (determined by fingerprint diffs, not field presence): - prompt_config has new/modified entries → re-run those configs + ALL dependent evals - user_eval_metrics has new/modified entries → re-run only those evals - column_id changed → delete old base eval columns, re-run base evals - If FE sends unchanged data, diffs return empty → no re-run

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ExperimentsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        ExperimentsApi apiInstance = new ExperimentsApi(defaultClient);
        String experimentId = "experimentId_example"; // String | 
        ExperimentUpdateV2 experimentUpdateV2 = new ExperimentUpdateV2(); // ExperimentUpdateV2 | 
        try {
            ApiResponse<ExperimentV2DetailResponse> response = apiInstance.updateExperimentWithHttpInfo(experimentId, experimentUpdateV2);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ExperimentsApi#updateExperiment");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **experimentId** | **String**|  | |
| **experimentUpdateV2** | [**ExperimentUpdateV2**](ExperimentUpdateV2.md)|  | |

### Return type

ApiResponse<[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **409** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

