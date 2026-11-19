# RunTestsEvalSummaryApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**simulateRunTestsEvalSummaryComparisonList**](RunTestsEvalSummaryApi.md#simulateRunTestsEvalSummaryComparisonList) | **GET** /simulate/run-tests/{run_test_id}/eval-summary-comparison/ | Compare evaluation summaries |
| [**simulateRunTestsEvalSummaryComparisonListWithHttpInfo**](RunTestsEvalSummaryApi.md#simulateRunTestsEvalSummaryComparisonListWithHttpInfo) | **GET** /simulate/run-tests/{run_test_id}/eval-summary-comparison/ | Compare evaluation summaries |
| [**simulateRunTestsEvalSummaryList**](RunTestsEvalSummaryApi.md#simulateRunTestsEvalSummaryList) | **GET** /simulate/run-tests/{run_test_id}/eval-summary/ | Get evaluation summary |
| [**simulateRunTestsEvalSummaryListWithHttpInfo**](RunTestsEvalSummaryApi.md#simulateRunTestsEvalSummaryListWithHttpInfo) | **GET** /simulate/run-tests/{run_test_id}/eval-summary/ | Get evaluation summary |



## simulateRunTestsEvalSummaryComparisonList

> EvalSummaryComparisonResponse simulateRunTestsEvalSummaryComparisonList(runTestId, executionIds)

Compare evaluation summaries

Compares evaluation summary statistics across multiple test executions.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalSummaryApi;

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

        RunTestsEvalSummaryApi apiInstance = new RunTestsEvalSummaryApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String executionIds = "executionIds_example"; // String | JSON-encoded array of test execution UUIDs to compare. Example: [\"uuid1\",\"uuid2\"]. Must be URL-encoded.
        try {
            EvalSummaryComparisonResponse result = apiInstance.simulateRunTestsEvalSummaryComparisonList(runTestId, executionIds);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalSummaryApi#simulateRunTestsEvalSummaryComparisonList");
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
| **runTestId** | **String**|  | |
| **executionIds** | **String**| JSON-encoded array of test execution UUIDs to compare. Example: [\&quot;uuid1\&quot;,\&quot;uuid2\&quot;]. Must be URL-encoded. | |

### Return type

[**EvalSummaryComparisonResponse**](EvalSummaryComparisonResponse.md)


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsEvalSummaryComparisonListWithHttpInfo

> ApiResponse<EvalSummaryComparisonResponse> simulateRunTestsEvalSummaryComparisonList simulateRunTestsEvalSummaryComparisonListWithHttpInfo(runTestId, executionIds)

Compare evaluation summaries

Compares evaluation summary statistics across multiple test executions.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalSummaryApi;

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

        RunTestsEvalSummaryApi apiInstance = new RunTestsEvalSummaryApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String executionIds = "executionIds_example"; // String | JSON-encoded array of test execution UUIDs to compare. Example: [\"uuid1\",\"uuid2\"]. Must be URL-encoded.
        try {
            ApiResponse<EvalSummaryComparisonResponse> response = apiInstance.simulateRunTestsEvalSummaryComparisonListWithHttpInfo(runTestId, executionIds);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalSummaryApi#simulateRunTestsEvalSummaryComparisonList");
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
| **runTestId** | **String**|  | |
| **executionIds** | **String**| JSON-encoded array of test execution UUIDs to compare. Example: [\&quot;uuid1\&quot;,\&quot;uuid2\&quot;]. Must be URL-encoded. | |

### Return type

ApiResponse<[**EvalSummaryComparisonResponse**](EvalSummaryComparisonResponse.md)>


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsEvalSummaryList

> EvalSummaryResponse simulateRunTestsEvalSummaryList(runTestId, executionId)

Get evaluation summary

Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalSummaryApi;

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

        RunTestsEvalSummaryApi apiInstance = new RunTestsEvalSummaryApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions.
        try {
            EvalSummaryResponse result = apiInstance.simulateRunTestsEvalSummaryList(runTestId, executionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalSummaryApi#simulateRunTestsEvalSummaryList");
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
| **runTestId** | **String**|  | |
| **executionId** | **UUID**| UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions. | [optional] |

### Return type

[**EvalSummaryResponse**](EvalSummaryResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsEvalSummaryListWithHttpInfo

> ApiResponse<EvalSummaryResponse> simulateRunTestsEvalSummaryList simulateRunTestsEvalSummaryListWithHttpInfo(runTestId, executionId)

Get evaluation summary

Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalSummaryApi;

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

        RunTestsEvalSummaryApi apiInstance = new RunTestsEvalSummaryApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        UUID executionId = UUID.randomUUID(); // UUID | UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions.
        try {
            ApiResponse<EvalSummaryResponse> response = apiInstance.simulateRunTestsEvalSummaryListWithHttpInfo(runTestId, executionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalSummaryApi#simulateRunTestsEvalSummaryList");
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
| **runTestId** | **String**|  | |
| **executionId** | **UUID**| UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions. | [optional] |

### Return type

ApiResponse<[**EvalSummaryResponse**](EvalSummaryResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

