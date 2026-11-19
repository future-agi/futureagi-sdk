# RunTestsEvalConfigsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**simulateRunTestsEvalConfigsCreate**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsCreate) | **POST** /simulate/run-tests/{run_test_id}/eval-configs/ | Add evaluation configurations |
| [**simulateRunTestsEvalConfigsCreateWithHttpInfo**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/eval-configs/ | Add evaluation configurations |
| [**simulateRunTestsEvalConfigsDelete**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsDelete) | **DELETE** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/ | Delete evaluation configuration |
| [**simulateRunTestsEvalConfigsDeleteWithHttpInfo**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsDeleteWithHttpInfo) | **DELETE** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/ | Delete evaluation configuration |
| [**simulateRunTestsEvalConfigsUpdateCreate**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsUpdateCreate) | **POST** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/update/ | Update evaluation configuration |
| [**simulateRunTestsEvalConfigsUpdateCreateWithHttpInfo**](RunTestsEvalConfigsApi.md#simulateRunTestsEvalConfigsUpdateCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/update/ | Update evaluation configuration |
| [**simulateRunTestsRunNewEvalsCreate**](RunTestsEvalConfigsApi.md#simulateRunTestsRunNewEvalsCreate) | **POST** /simulate/run-tests/{run_test_id}/run-new-evals/ | Run new evaluations on test executions |
| [**simulateRunTestsRunNewEvalsCreateWithHttpInfo**](RunTestsEvalConfigsApi.md#simulateRunTestsRunNewEvalsCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/run-new-evals/ | Run new evaluations on test executions |



## simulateRunTestsEvalConfigsCreate

> AddEvalConfigsResponse simulateRunTestsEvalConfigsCreate(runTestId, addEvalConfigsRequest)

Add evaluation configurations

Adds evaluation configurations to a test run. Returns 201 with the created configs.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        AddEvalConfigsRequest addEvalConfigsRequest = new AddEvalConfigsRequest(); // AddEvalConfigsRequest | 
        try {
            AddEvalConfigsResponse result = apiInstance.simulateRunTestsEvalConfigsCreate(runTestId, addEvalConfigsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsCreate");
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
| **addEvalConfigsRequest** | [**AddEvalConfigsRequest**](AddEvalConfigsRequest.md)|  | |

### Return type

[**AddEvalConfigsResponse**](AddEvalConfigsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsEvalConfigsCreateWithHttpInfo

> ApiResponse<AddEvalConfigsResponse> simulateRunTestsEvalConfigsCreate simulateRunTestsEvalConfigsCreateWithHttpInfo(runTestId, addEvalConfigsRequest)

Add evaluation configurations

Adds evaluation configurations to a test run. Returns 201 with the created configs.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        AddEvalConfigsRequest addEvalConfigsRequest = new AddEvalConfigsRequest(); // AddEvalConfigsRequest | 
        try {
            ApiResponse<AddEvalConfigsResponse> response = apiInstance.simulateRunTestsEvalConfigsCreateWithHttpInfo(runTestId, addEvalConfigsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsCreate");
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
| **addEvalConfigsRequest** | [**AddEvalConfigsRequest**](AddEvalConfigsRequest.md)|  | |

### Return type

ApiResponse<[**AddEvalConfigsResponse**](AddEvalConfigsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsEvalConfigsDelete

> DeleteEvalConfigResponse simulateRunTestsEvalConfigsDelete(runTestId, evalConfigId)

Delete evaluation configuration

Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        try {
            DeleteEvalConfigResponse result = apiInstance.simulateRunTestsEvalConfigsDelete(runTestId, evalConfigId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsDelete");
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
| **evalConfigId** | **String**|  | |

### Return type

[**DeleteEvalConfigResponse**](DeleteEvalConfigResponse.md)


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

## simulateRunTestsEvalConfigsDeleteWithHttpInfo

> ApiResponse<DeleteEvalConfigResponse> simulateRunTestsEvalConfigsDelete simulateRunTestsEvalConfigsDeleteWithHttpInfo(runTestId, evalConfigId)

Delete evaluation configuration

Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        try {
            ApiResponse<DeleteEvalConfigResponse> response = apiInstance.simulateRunTestsEvalConfigsDeleteWithHttpInfo(runTestId, evalConfigId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsDelete");
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
| **evalConfigId** | **String**|  | |

### Return type

ApiResponse<[**DeleteEvalConfigResponse**](DeleteEvalConfigResponse.md)>


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


## simulateRunTestsEvalConfigsUpdateCreate

> EvalConfigUpdateResponse simulateRunTestsEvalConfigsUpdateCreate(runTestId, evalConfigId, evalConfigUpdateRequest)

Update evaluation configuration

Updates an evaluation configuration and optionally triggers a rerun. When run&#x3D;true, test_execution_id is required.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        EvalConfigUpdateRequest evalConfigUpdateRequest = new EvalConfigUpdateRequest(); // EvalConfigUpdateRequest | 
        try {
            EvalConfigUpdateResponse result = apiInstance.simulateRunTestsEvalConfigsUpdateCreate(runTestId, evalConfigId, evalConfigUpdateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsUpdateCreate");
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
| **evalConfigId** | **String**|  | |
| **evalConfigUpdateRequest** | [**EvalConfigUpdateRequest**](EvalConfigUpdateRequest.md)|  | |

### Return type

[**EvalConfigUpdateResponse**](EvalConfigUpdateResponse.md)


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsEvalConfigsUpdateCreateWithHttpInfo

> ApiResponse<EvalConfigUpdateResponse> simulateRunTestsEvalConfigsUpdateCreate simulateRunTestsEvalConfigsUpdateCreateWithHttpInfo(runTestId, evalConfigId, evalConfigUpdateRequest)

Update evaluation configuration

Updates an evaluation configuration and optionally triggers a rerun. When run&#x3D;true, test_execution_id is required.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        EvalConfigUpdateRequest evalConfigUpdateRequest = new EvalConfigUpdateRequest(); // EvalConfigUpdateRequest | 
        try {
            ApiResponse<EvalConfigUpdateResponse> response = apiInstance.simulateRunTestsEvalConfigsUpdateCreateWithHttpInfo(runTestId, evalConfigId, evalConfigUpdateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsEvalConfigsUpdateCreate");
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
| **evalConfigId** | **String**|  | |
| **evalConfigUpdateRequest** | [**EvalConfigUpdateRequest**](EvalConfigUpdateRequest.md)|  | |

### Return type

ApiResponse<[**EvalConfigUpdateResponse**](EvalConfigUpdateResponse.md)>


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsRunNewEvalsCreate

> RunNewEvalsResponse simulateRunTestsRunNewEvalsCreate(runTestId, runNewEvalsOnTestExecution)

Run new evaluations on test executions

Runs new evaluations on completed test executions. Either test_execution_ids or select_all&#x3D;true must be provided.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        RunNewEvalsOnTestExecution runNewEvalsOnTestExecution = new RunNewEvalsOnTestExecution(); // RunNewEvalsOnTestExecution | 
        try {
            RunNewEvalsResponse result = apiInstance.simulateRunTestsRunNewEvalsCreate(runTestId, runNewEvalsOnTestExecution);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsRunNewEvalsCreate");
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
| **runNewEvalsOnTestExecution** | [**RunNewEvalsOnTestExecution**](RunNewEvalsOnTestExecution.md)|  | |

### Return type

[**RunNewEvalsResponse**](RunNewEvalsResponse.md)


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsRunNewEvalsCreateWithHttpInfo

> ApiResponse<RunNewEvalsResponse> simulateRunTestsRunNewEvalsCreate simulateRunTestsRunNewEvalsCreateWithHttpInfo(runTestId, runNewEvalsOnTestExecution)

Run new evaluations on test executions

Runs new evaluations on completed test executions. Either test_execution_ids or select_all&#x3D;true must be provided.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.RunTestsEvalConfigsApi;

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

        RunTestsEvalConfigsApi apiInstance = new RunTestsEvalConfigsApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        RunNewEvalsOnTestExecution runNewEvalsOnTestExecution = new RunNewEvalsOnTestExecution(); // RunNewEvalsOnTestExecution | 
        try {
            ApiResponse<RunNewEvalsResponse> response = apiInstance.simulateRunTestsRunNewEvalsCreateWithHttpInfo(runTestId, runNewEvalsOnTestExecution);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling RunTestsEvalConfigsApi#simulateRunTestsRunNewEvalsCreate");
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
| **runNewEvalsOnTestExecution** | [**RunNewEvalsOnTestExecution**](RunNewEvalsOnTestExecution.md)|  | |

### Return type

ApiResponse<[**RunNewEvalsResponse**](RunNewEvalsResponse.md)>


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
| **401** | Unauthorized |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

