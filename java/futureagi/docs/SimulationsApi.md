# SimulationsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getSimulationAnalytics**](SimulationsApi.md#getSimulationAnalytics) | **GET** /sdk/api/v1/simulation/analytics/ | GET /simulation/analytics/ |
| [**getSimulationAnalyticsWithHttpInfo**](SimulationsApi.md#getSimulationAnalyticsWithHttpInfo) | **GET** /sdk/api/v1/simulation/analytics/ | GET /simulation/analytics/ |
| [**listSimulationMetrics**](SimulationsApi.md#listSimulationMetrics) | **GET** /sdk/api/v1/simulation/metrics/ | GET /simulation/metrics/ |
| [**listSimulationMetricsWithHttpInfo**](SimulationsApi.md#listSimulationMetricsWithHttpInfo) | **GET** /sdk/api/v1/simulation/metrics/ | GET /simulation/metrics/ |
| [**listSimulationRuns**](SimulationsApi.md#listSimulationRuns) | **GET** /sdk/api/v1/simulation/runs/ | GET /simulation/runs/ |
| [**listSimulationRunsWithHttpInfo**](SimulationsApi.md#listSimulationRunsWithHttpInfo) | **GET** /sdk/api/v1/simulation/runs/ | GET /simulation/runs/ |



## getSimulationAnalytics

> SDKSimulationAnalyticsResponse getSimulationAnalytics(runTestName, executionId, evalName, summary)

GET /simulation/analytics/

Aggregated analytics view: eval scores (radar chart data), critical issues, FMA suggestions. Corresponds to the Analytics tab in the UI.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        String evalName = "evalName_example"; // String | 
        Boolean summary = true; // Boolean | 
        try {
            SDKSimulationAnalyticsResponse result = apiInstance.getSimulationAnalytics(runTestName, executionId, evalName, summary);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#getSimulationAnalytics");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **evalName** | **String**|  | [optional] |
| **summary** | **Boolean**|  | [optional] [default to true] |

### Return type

[**SDKSimulationAnalyticsResponse**](SDKSimulationAnalyticsResponse.md)


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getSimulationAnalyticsWithHttpInfo

> ApiResponse<SDKSimulationAnalyticsResponse> getSimulationAnalytics getSimulationAnalyticsWithHttpInfo(runTestName, executionId, evalName, summary)

GET /simulation/analytics/

Aggregated analytics view: eval scores (radar chart data), critical issues, FMA suggestions. Corresponds to the Analytics tab in the UI.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        String evalName = "evalName_example"; // String | 
        Boolean summary = true; // Boolean | 
        try {
            ApiResponse<SDKSimulationAnalyticsResponse> response = apiInstance.getSimulationAnalyticsWithHttpInfo(runTestName, executionId, evalName, summary);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#getSimulationAnalytics");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **evalName** | **String**|  | [optional] |
| **summary** | **Boolean**|  | [optional] [default to true] |

### Return type

ApiResponse<[**SDKSimulationAnalyticsResponse**](SDKSimulationAnalyticsResponse.md)>


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listSimulationMetrics

> SDKSimulationMetricsResponse listSimulationMetrics(runTestName, executionId, callExecutionId)

GET /simulation/metrics/

Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        UUID callExecutionId = UUID.randomUUID(); // UUID | 
        try {
            SDKSimulationMetricsResponse result = apiInstance.listSimulationMetrics(runTestName, executionId, callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#listSimulationMetrics");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **callExecutionId** | **UUID**|  | [optional] |

### Return type

[**SDKSimulationMetricsResponse**](SDKSimulationMetricsResponse.md)


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listSimulationMetricsWithHttpInfo

> ApiResponse<SDKSimulationMetricsResponse> listSimulationMetrics listSimulationMetricsWithHttpInfo(runTestName, executionId, callExecutionId)

GET /simulation/metrics/

Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        UUID callExecutionId = UUID.randomUUID(); // UUID | 
        try {
            ApiResponse<SDKSimulationMetricsResponse> response = apiInstance.listSimulationMetricsWithHttpInfo(runTestName, executionId, callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#listSimulationMetrics");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **callExecutionId** | **UUID**|  | [optional] |

### Return type

ApiResponse<[**SDKSimulationMetricsResponse**](SDKSimulationMetricsResponse.md)>


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listSimulationRuns

> SDKSimulationRunsResponse listSimulationRuns(runTestName, executionId, callExecutionId, evalName, summary)

GET /simulation/runs/

Run-level records with eval scores, scenario metadata, call details.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        UUID callExecutionId = UUID.randomUUID(); // UUID | 
        String evalName = "evalName_example"; // String | 
        Boolean summary = false; // Boolean | 
        try {
            SDKSimulationRunsResponse result = apiInstance.listSimulationRuns(runTestName, executionId, callExecutionId, evalName, summary);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#listSimulationRuns");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **callExecutionId** | **UUID**|  | [optional] |
| **evalName** | **String**|  | [optional] |
| **summary** | **Boolean**|  | [optional] [default to false] |

### Return type

[**SDKSimulationRunsResponse**](SDKSimulationRunsResponse.md)


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listSimulationRunsWithHttpInfo

> ApiResponse<SDKSimulationRunsResponse> listSimulationRuns listSimulationRunsWithHttpInfo(runTestName, executionId, callExecutionId, evalName, summary)

GET /simulation/runs/

Run-level records with eval scores, scenario metadata, call details.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationsApi;

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

        SimulationsApi apiInstance = new SimulationsApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | 
        UUID callExecutionId = UUID.randomUUID(); // UUID | 
        String evalName = "evalName_example"; // String | 
        Boolean summary = false; // Boolean | 
        try {
            ApiResponse<SDKSimulationRunsResponse> response = apiInstance.listSimulationRunsWithHttpInfo(runTestName, executionId, callExecutionId, evalName, summary);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationsApi#listSimulationRuns");
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
| **runTestName** | **String**|  | [optional] |
| **executionId** | **UUID**|  | [optional] |
| **callExecutionId** | **UUID**|  | [optional] |
| **evalName** | **String**|  | [optional] |
| **summary** | **Boolean**|  | [optional] [default to false] |

### Return type

ApiResponse<[**SDKSimulationRunsResponse**](SDKSimulationRunsResponse.md)>


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

