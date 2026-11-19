# SimulationTestExecutionsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**cancelTestExecution**](SimulationTestExecutionsApi.md#cancelTestExecution) | **POST** /simulate/test-executions/{test_execution_id}/cancel/ |  |
| [**cancelTestExecutionWithHttpInfo**](SimulationTestExecutionsApi.md#cancelTestExecutionWithHttpInfo) | **POST** /simulate/test-executions/{test_execution_id}/cancel/ |  |
| [**getTestExecution**](SimulationTestExecutionsApi.md#getTestExecution) | **GET** /simulate/test-executions/{test_execution_id}/ |  |
| [**getTestExecutionWithHttpInfo**](SimulationTestExecutionsApi.md#getTestExecutionWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/ |  |
| [**getTestExecutionAnalytics**](SimulationTestExecutionsApi.md#getTestExecutionAnalytics) | **GET** /simulate/test-executions/{test_execution_id}/analytics/ |  |
| [**getTestExecutionAnalyticsWithHttpInfo**](SimulationTestExecutionsApi.md#getTestExecutionAnalyticsWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/analytics/ |  |
| [**getTestExecutionKpis**](SimulationTestExecutionsApi.md#getTestExecutionKpis) | **GET** /simulate/test-executions/{test_execution_id}/kpis/ |  |
| [**getTestExecutionKpisWithHttpInfo**](SimulationTestExecutionsApi.md#getTestExecutionKpisWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/kpis/ |  |
| [**getTestExecutionPerformanceSummary**](SimulationTestExecutionsApi.md#getTestExecutionPerformanceSummary) | **GET** /simulate/test-executions/{test_execution_id}/performance-summary/ |  |
| [**getTestExecutionPerformanceSummaryWithHttpInfo**](SimulationTestExecutionsApi.md#getTestExecutionPerformanceSummaryWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/performance-summary/ |  |
| [**getTestExecutionTranscripts**](SimulationTestExecutionsApi.md#getTestExecutionTranscripts) | **GET** /simulate/test-executions/{test_execution_id}/transcripts/ |  |
| [**getTestExecutionTranscriptsWithHttpInfo**](SimulationTestExecutionsApi.md#getTestExecutionTranscriptsWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/transcripts/ |  |
| [**listTestExecutions**](SimulationTestExecutionsApi.md#listTestExecutions) | **GET** /simulate/api/test-executions/ |  |
| [**listTestExecutionsWithHttpInfo**](SimulationTestExecutionsApi.md#listTestExecutionsWithHttpInfo) | **GET** /simulate/api/test-executions/ |  |



## cancelTestExecution

> CancelTestExecutionResponse cancelTestExecution(testExecutionId, body)



Cancel a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            CancelTestExecutionResponse result = apiInstance.cancelTestExecution(testExecutionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#cancelTestExecution");
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
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**CancelTestExecutionResponse**](CancelTestExecutionResponse.md)


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## cancelTestExecutionWithHttpInfo

> ApiResponse<CancelTestExecutionResponse> cancelTestExecution cancelTestExecutionWithHttpInfo(testExecutionId, body)



Cancel a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<CancelTestExecutionResponse> response = apiInstance.cancelTestExecutionWithHttpInfo(testExecutionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#cancelTestExecution");
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
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**CancelTestExecutionResponse**](CancelTestExecutionResponse.md)>


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
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTestExecution

> TestExecutionDetailResponse getTestExecution(testExecutionId, search, filters, rowGroups, groupKeys, page, limit)



Get a specific test execution with all its details and paginated call executions Query Parameters: - search: search string to filter call executions - page: page number for call executions (default: 1) - filters: JSON array of filter objects - row_groups: JSON array of column IDs to group by - group_keys: JSON array of group keys

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        String search = ""; // String | 
        String filters = "[]"; // String | 
        String rowGroups = "[]"; // String | 
        String groupKeys = "[]"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 30; // Integer | 
        try {
            TestExecutionDetailResponse result = apiInstance.getTestExecution(testExecutionId, search, filters, rowGroups, groupKeys, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecution");
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
| **testExecutionId** | **String**|  | |
| **search** | **String**|  | [optional] [default to ] |
| **filters** | **String**|  | [optional] [default to []] |
| **rowGroups** | **String**|  | [optional] [default to []] |
| **groupKeys** | **String**|  | [optional] [default to []] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 30] |

### Return type

[**TestExecutionDetailResponse**](TestExecutionDetailResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getTestExecutionWithHttpInfo

> ApiResponse<TestExecutionDetailResponse> getTestExecution getTestExecutionWithHttpInfo(testExecutionId, search, filters, rowGroups, groupKeys, page, limit)



Get a specific test execution with all its details and paginated call executions Query Parameters: - search: search string to filter call executions - page: page number for call executions (default: 1) - filters: JSON array of filter objects - row_groups: JSON array of column IDs to group by - group_keys: JSON array of group keys

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        String search = ""; // String | 
        String filters = "[]"; // String | 
        String rowGroups = "[]"; // String | 
        String groupKeys = "[]"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 30; // Integer | 
        try {
            ApiResponse<TestExecutionDetailResponse> response = apiInstance.getTestExecutionWithHttpInfo(testExecutionId, search, filters, rowGroups, groupKeys, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecution");
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
| **testExecutionId** | **String**|  | |
| **search** | **String**|  | [optional] [default to ] |
| **filters** | **String**|  | [optional] [default to []] |
| **rowGroups** | **String**|  | [optional] [default to []] |
| **groupKeys** | **String**|  | [optional] [default to []] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 30] |

### Return type

ApiResponse<[**TestExecutionDetailResponse**](TestExecutionDetailResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTestExecutionAnalytics

> TestExecutionAnalytics getTestExecutionAnalytics(testExecutionId)



Get analytics data for a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            TestExecutionAnalytics result = apiInstance.getTestExecutionAnalytics(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionAnalytics");
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
| **testExecutionId** | **String**|  | |

### Return type

[**TestExecutionAnalytics**](TestExecutionAnalytics.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getTestExecutionAnalyticsWithHttpInfo

> ApiResponse<TestExecutionAnalytics> getTestExecutionAnalytics getTestExecutionAnalyticsWithHttpInfo(testExecutionId)



Get analytics data for a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<TestExecutionAnalytics> response = apiInstance.getTestExecutionAnalyticsWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionAnalytics");
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
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**TestExecutionAnalytics**](TestExecutionAnalytics.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTestExecutionKpis

> RunTestKPIsResponse getTestExecutionKpis(testExecutionId)



Get combined KPI values for a specific run test

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            RunTestKPIsResponse result = apiInstance.getTestExecutionKpis(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionKpis");
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
| **testExecutionId** | **String**|  | |

### Return type

[**RunTestKPIsResponse**](RunTestKPIsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getTestExecutionKpisWithHttpInfo

> ApiResponse<RunTestKPIsResponse> getTestExecutionKpis getTestExecutionKpisWithHttpInfo(testExecutionId)



Get combined KPI values for a specific run test

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<RunTestKPIsResponse> response = apiInstance.getTestExecutionKpisWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionKpis");
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
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**RunTestKPIsResponse**](RunTestKPIsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTestExecutionPerformanceSummary

> PerformanceSummary getTestExecutionPerformanceSummary(testExecutionId)



Get performance summary data for a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            PerformanceSummary result = apiInstance.getTestExecutionPerformanceSummary(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionPerformanceSummary");
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
| **testExecutionId** | **String**|  | |

### Return type

[**PerformanceSummary**](PerformanceSummary.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getTestExecutionPerformanceSummaryWithHttpInfo

> ApiResponse<PerformanceSummary> getTestExecutionPerformanceSummary getTestExecutionPerformanceSummaryWithHttpInfo(testExecutionId)



Get performance summary data for a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<PerformanceSummary> response = apiInstance.getTestExecutionPerformanceSummaryWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionPerformanceSummary");
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
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**PerformanceSummary**](PerformanceSummary.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTestExecutionTranscripts

> TestExecutionTranscriptsResponse getTestExecutionTranscripts(testExecutionId)



Get all transcripts for a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            TestExecutionTranscriptsResponse result = apiInstance.getTestExecutionTranscripts(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionTranscripts");
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
| **testExecutionId** | **String**|  | |

### Return type

[**TestExecutionTranscriptsResponse**](TestExecutionTranscriptsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getTestExecutionTranscriptsWithHttpInfo

> ApiResponse<TestExecutionTranscriptsResponse> getTestExecutionTranscripts getTestExecutionTranscriptsWithHttpInfo(testExecutionId)



Get all transcripts for a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<TestExecutionTranscriptsResponse> response = apiInstance.getTestExecutionTranscriptsWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#getTestExecutionTranscripts");
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
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**TestExecutionTranscriptsResponse**](TestExecutionTranscriptsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listTestExecutions

> List<TestExecution> listTestExecutions()



Get paginated list of test executions for the user&#39;s organization Query Parameters: - search: search string to filter test executions by run test name - status: filter by execution status - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        try {
            List<TestExecution> result = apiInstance.listTestExecutions();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#listTestExecutions");
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

[**List&lt;TestExecution&gt;**](TestExecution.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listTestExecutionsWithHttpInfo

> ApiResponse<List<TestExecution>> listTestExecutions listTestExecutionsWithHttpInfo()



Get paginated list of test executions for the user&#39;s organization Query Parameters: - search: search string to filter test executions by run test name - status: filter by execution status - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationTestExecutionsApi;

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

        SimulationTestExecutionsApi apiInstance = new SimulationTestExecutionsApi(defaultClient);
        try {
            ApiResponse<List<TestExecution>> response = apiInstance.listTestExecutionsWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationTestExecutionsApi#listTestExecutions");
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

ApiResponse<[**List&lt;TestExecution&gt;**](TestExecution.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

