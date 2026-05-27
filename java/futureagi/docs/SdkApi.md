# SdkApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**sdkApiV1ConfigureEvaluationsCreate**](SdkApi.md#sdkApiV1ConfigureEvaluationsCreate) | **POST** /sdk/api/v1/configure-evaluations/ |  |
| [**sdkApiV1ConfigureEvaluationsCreateWithHttpInfo**](SdkApi.md#sdkApiV1ConfigureEvaluationsCreateWithHttpInfo) | **POST** /sdk/api/v1/configure-evaluations/ |  |
| [**sdkApiV1EvalCreate**](SdkApi.md#sdkApiV1EvalCreate) | **POST** /sdk/api/v1/eval/ |  |
| [**sdkApiV1EvalCreateWithHttpInfo**](SdkApi.md#sdkApiV1EvalCreateWithHttpInfo) | **POST** /sdk/api/v1/eval/ |  |
| [**sdkApiV1EvalRead**](SdkApi.md#sdkApiV1EvalRead) | **GET** /sdk/api/v1/eval/{eval_id}/ |  |
| [**sdkApiV1EvalReadWithHttpInfo**](SdkApi.md#sdkApiV1EvalReadWithHttpInfo) | **GET** /sdk/api/v1/eval/{eval_id}/ |  |
| [**sdkApiV1EvaluatePipelineCreate**](SdkApi.md#sdkApiV1EvaluatePipelineCreate) | **POST** /sdk/api/v1/evaluate-pipeline/ |  |
| [**sdkApiV1EvaluatePipelineCreateWithHttpInfo**](SdkApi.md#sdkApiV1EvaluatePipelineCreateWithHttpInfo) | **POST** /sdk/api/v1/evaluate-pipeline/ |  |
| [**sdkApiV1EvaluatePipelineList**](SdkApi.md#sdkApiV1EvaluatePipelineList) | **GET** /sdk/api/v1/evaluate-pipeline/ |  |
| [**sdkApiV1EvaluatePipelineListWithHttpInfo**](SdkApi.md#sdkApiV1EvaluatePipelineListWithHttpInfo) | **GET** /sdk/api/v1/evaluate-pipeline/ |  |
| [**sdkApiV1GetEvalsList**](SdkApi.md#sdkApiV1GetEvalsList) | **GET** /sdk/api/v1/get-evals/ |  |
| [**sdkApiV1GetEvalsListWithHttpInfo**](SdkApi.md#sdkApiV1GetEvalsListWithHttpInfo) | **GET** /sdk/api/v1/get-evals/ |  |
| [**sdkApiV1NewEvalCreate**](SdkApi.md#sdkApiV1NewEvalCreate) | **POST** /sdk/api/v1/new-eval/ |  |
| [**sdkApiV1NewEvalCreateWithHttpInfo**](SdkApi.md#sdkApiV1NewEvalCreateWithHttpInfo) | **POST** /sdk/api/v1/new-eval/ |  |
| [**sdkApiV1NewEvalList**](SdkApi.md#sdkApiV1NewEvalList) | **GET** /sdk/api/v1/new-eval/ |  |
| [**sdkApiV1NewEvalListWithHttpInfo**](SdkApi.md#sdkApiV1NewEvalListWithHttpInfo) | **GET** /sdk/api/v1/new-eval/ |  |



## sdkApiV1ConfigureEvaluationsCreate

> SDKConfigureEvaluationsResponse sdkApiV1ConfigureEvaluationsCreate(sdKConfigureEvaluationsRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKConfigureEvaluationsRequest sdKConfigureEvaluationsRequest = new SDKConfigureEvaluationsRequest(); // SDKConfigureEvaluationsRequest | 
        try {
            SDKConfigureEvaluationsResponse result = apiInstance.sdkApiV1ConfigureEvaluationsCreate(sdKConfigureEvaluationsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1ConfigureEvaluationsCreate");
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
| **sdKConfigureEvaluationsRequest** | [**SDKConfigureEvaluationsRequest**](SDKConfigureEvaluationsRequest.md)|  | |

### Return type

[**SDKConfigureEvaluationsResponse**](SDKConfigureEvaluationsResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1ConfigureEvaluationsCreateWithHttpInfo

> ApiResponse<SDKConfigureEvaluationsResponse> sdkApiV1ConfigureEvaluationsCreate sdkApiV1ConfigureEvaluationsCreateWithHttpInfo(sdKConfigureEvaluationsRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKConfigureEvaluationsRequest sdKConfigureEvaluationsRequest = new SDKConfigureEvaluationsRequest(); // SDKConfigureEvaluationsRequest | 
        try {
            ApiResponse<SDKConfigureEvaluationsResponse> response = apiInstance.sdkApiV1ConfigureEvaluationsCreateWithHttpInfo(sdKConfigureEvaluationsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1ConfigureEvaluationsCreate");
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
| **sdKConfigureEvaluationsRequest** | [**SDKConfigureEvaluationsRequest**](SDKConfigureEvaluationsRequest.md)|  | |

### Return type

ApiResponse<[**SDKConfigureEvaluationsResponse**](SDKConfigureEvaluationsResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1EvalCreate

> SDKStandaloneEvalResponse sdkApiV1EvalCreate(sdKStandaloneEvalRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKStandaloneEvalRequest sdKStandaloneEvalRequest = new SDKStandaloneEvalRequest(); // SDKStandaloneEvalRequest | 
        try {
            SDKStandaloneEvalResponse result = apiInstance.sdkApiV1EvalCreate(sdKStandaloneEvalRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvalCreate");
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
| **sdKStandaloneEvalRequest** | [**SDKStandaloneEvalRequest**](SDKStandaloneEvalRequest.md)|  | |

### Return type

[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1EvalCreateWithHttpInfo

> ApiResponse<SDKStandaloneEvalResponse> sdkApiV1EvalCreate sdkApiV1EvalCreateWithHttpInfo(sdKStandaloneEvalRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKStandaloneEvalRequest sdKStandaloneEvalRequest = new SDKStandaloneEvalRequest(); // SDKStandaloneEvalRequest | 
        try {
            ApiResponse<SDKStandaloneEvalResponse> response = apiInstance.sdkApiV1EvalCreateWithHttpInfo(sdKStandaloneEvalRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvalCreate");
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
| **sdKStandaloneEvalRequest** | [**SDKStandaloneEvalRequest**](SDKStandaloneEvalRequest.md)|  | |

### Return type

ApiResponse<[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1EvalRead

> SDKEvalTemplateResponse sdkApiV1EvalRead(evalId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        String evalId = "evalId_example"; // String | 
        try {
            SDKEvalTemplateResponse result = apiInstance.sdkApiV1EvalRead(evalId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvalRead");
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
| **evalId** | **String**|  | |

### Return type

[**SDKEvalTemplateResponse**](SDKEvalTemplateResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1EvalReadWithHttpInfo

> ApiResponse<SDKEvalTemplateResponse> sdkApiV1EvalRead sdkApiV1EvalReadWithHttpInfo(evalId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        String evalId = "evalId_example"; // String | 
        try {
            ApiResponse<SDKEvalTemplateResponse> response = apiInstance.sdkApiV1EvalReadWithHttpInfo(evalId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvalRead");
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
| **evalId** | **String**|  | |

### Return type

ApiResponse<[**SDKEvalTemplateResponse**](SDKEvalTemplateResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1EvaluatePipelineCreate

> SDKCICDEvaluationRunAcceptedResponse sdkApiV1EvaluatePipelineCreate(ciCDJob)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        CICDJob ciCDJob = new CICDJob(); // CICDJob | 
        try {
            SDKCICDEvaluationRunAcceptedResponse result = apiInstance.sdkApiV1EvaluatePipelineCreate(ciCDJob);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvaluatePipelineCreate");
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
| **ciCDJob** | [**CICDJob**](CICDJob.md)|  | |

### Return type

[**SDKCICDEvaluationRunAcceptedResponse**](SDKCICDEvaluationRunAcceptedResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1EvaluatePipelineCreateWithHttpInfo

> ApiResponse<SDKCICDEvaluationRunAcceptedResponse> sdkApiV1EvaluatePipelineCreate sdkApiV1EvaluatePipelineCreateWithHttpInfo(ciCDJob)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        CICDJob ciCDJob = new CICDJob(); // CICDJob | 
        try {
            ApiResponse<SDKCICDEvaluationRunAcceptedResponse> response = apiInstance.sdkApiV1EvaluatePipelineCreateWithHttpInfo(ciCDJob);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvaluatePipelineCreate");
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
| **ciCDJob** | [**CICDJob**](CICDJob.md)|  | |

### Return type

ApiResponse<[**SDKCICDEvaluationRunAcceptedResponse**](SDKCICDEvaluationRunAcceptedResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1EvaluatePipelineList

> SDKCICDEvaluationRunsResponse sdkApiV1EvaluatePipelineList(projectName, versions)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        String projectName = "projectName_example"; // String | 
        String versions = "versions_example"; // String | 
        try {
            SDKCICDEvaluationRunsResponse result = apiInstance.sdkApiV1EvaluatePipelineList(projectName, versions);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvaluatePipelineList");
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
| **projectName** | **String**|  | |
| **versions** | **String**|  | |

### Return type

[**SDKCICDEvaluationRunsResponse**](SDKCICDEvaluationRunsResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1EvaluatePipelineListWithHttpInfo

> ApiResponse<SDKCICDEvaluationRunsResponse> sdkApiV1EvaluatePipelineList sdkApiV1EvaluatePipelineListWithHttpInfo(projectName, versions)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        String projectName = "projectName_example"; // String | 
        String versions = "versions_example"; // String | 
        try {
            ApiResponse<SDKCICDEvaluationRunsResponse> response = apiInstance.sdkApiV1EvaluatePipelineListWithHttpInfo(projectName, versions);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1EvaluatePipelineList");
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
| **projectName** | **String**|  | |
| **versions** | **String**|  | |

### Return type

ApiResponse<[**SDKCICDEvaluationRunsResponse**](SDKCICDEvaluationRunsResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1GetEvalsList

> SDKGetEvalsResponse sdkApiV1GetEvalsList()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        try {
            SDKGetEvalsResponse result = apiInstance.sdkApiV1GetEvalsList();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1GetEvalsList");
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

[**SDKGetEvalsResponse**](SDKGetEvalsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1GetEvalsListWithHttpInfo

> ApiResponse<SDKGetEvalsResponse> sdkApiV1GetEvalsList sdkApiV1GetEvalsListWithHttpInfo()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        try {
            ApiResponse<SDKGetEvalsResponse> response = apiInstance.sdkApiV1GetEvalsListWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1GetEvalsList");
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

ApiResponse<[**SDKGetEvalsResponse**](SDKGetEvalsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1NewEvalCreate

> SDKStandaloneEvalResponse sdkApiV1NewEvalCreate(sdKStandaloneEvalV2Request)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKStandaloneEvalV2Request sdKStandaloneEvalV2Request = new SDKStandaloneEvalV2Request(); // SDKStandaloneEvalV2Request | 
        try {
            SDKStandaloneEvalResponse result = apiInstance.sdkApiV1NewEvalCreate(sdKStandaloneEvalV2Request);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1NewEvalCreate");
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
| **sdKStandaloneEvalV2Request** | [**SDKStandaloneEvalV2Request**](SDKStandaloneEvalV2Request.md)|  | |

### Return type

[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1NewEvalCreateWithHttpInfo

> ApiResponse<SDKStandaloneEvalResponse> sdkApiV1NewEvalCreate sdkApiV1NewEvalCreateWithHttpInfo(sdKStandaloneEvalV2Request)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        SDKStandaloneEvalV2Request sdKStandaloneEvalV2Request = new SDKStandaloneEvalV2Request(); // SDKStandaloneEvalV2Request | 
        try {
            ApiResponse<SDKStandaloneEvalResponse> response = apiInstance.sdkApiV1NewEvalCreateWithHttpInfo(sdKStandaloneEvalV2Request);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1NewEvalCreate");
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
| **sdKStandaloneEvalV2Request** | [**SDKStandaloneEvalV2Request**](SDKStandaloneEvalV2Request.md)|  | |

### Return type

ApiResponse<[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## sdkApiV1NewEvalList

> SDKStandaloneEvalV2Response sdkApiV1NewEvalList(evalId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        UUID evalId = UUID.randomUUID(); // UUID | 
        try {
            SDKStandaloneEvalV2Response result = apiInstance.sdkApiV1NewEvalList(evalId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1NewEvalList");
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
| **evalId** | **UUID**|  | |

### Return type

[**SDKStandaloneEvalV2Response**](SDKStandaloneEvalV2Response.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## sdkApiV1NewEvalListWithHttpInfo

> ApiResponse<SDKStandaloneEvalV2Response> sdkApiV1NewEvalList sdkApiV1NewEvalListWithHttpInfo(evalId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SdkApi;

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

        SdkApi apiInstance = new SdkApi(defaultClient);
        UUID evalId = UUID.randomUUID(); // UUID | 
        try {
            ApiResponse<SDKStandaloneEvalV2Response> response = apiInstance.sdkApiV1NewEvalListWithHttpInfo(evalId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SdkApi#sdkApiV1NewEvalList");
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
| **evalId** | **UUID**|  | |

### Return type

ApiResponse<[**SDKStandaloneEvalV2Response**](SDKStandaloneEvalV2Response.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

