# TracingApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createBulkTraceAnnotation**](TracingApi.md#createBulkTraceAnnotation) | **POST** /tracer/bulk-annotation/ |  |
| [**createBulkTraceAnnotationWithHttpInfo**](TracingApi.md#createBulkTraceAnnotationWithHttpInfo) | **POST** /tracer/bulk-annotation/ |  |
| [**getErrorFeedIssue**](TracingApi.md#getErrorFeedIssue) | **GET** /tracer/feed/issues/{cluster_id}/ |  |
| [**getErrorFeedIssueWithHttpInfo**](TracingApi.md#getErrorFeedIssueWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/ |  |
| [**getErrorFeedIssueStats**](TracingApi.md#getErrorFeedIssueStats) | **GET** /tracer/feed/issues/stats/ |  |
| [**getErrorFeedIssueStatsWithHttpInfo**](TracingApi.md#getErrorFeedIssueStatsWithHttpInfo) | **GET** /tracer/feed/issues/stats/ |  |
| [**getTrace**](TracingApi.md#getTrace) | **GET** /tracer/trace/{id}/ |  |
| [**getTraceWithHttpInfo**](TracingApi.md#getTraceWithHttpInfo) | **GET** /tracer/trace/{id}/ |  |
| [**getTraceGraphMethods**](TracingApi.md#getTraceGraphMethods) | **POST** /tracer/trace/get_graph_methods/ |  |
| [**getTraceGraphMethodsWithHttpInfo**](TracingApi.md#getTraceGraphMethodsWithHttpInfo) | **POST** /tracer/trace/get_graph_methods/ |  |
| [**getTraceSession**](TracingApi.md#getTraceSession) | **GET** /tracer/trace-session/{id}/ |  |
| [**getTraceSessionWithHttpInfo**](TracingApi.md#getTraceSessionWithHttpInfo) | **GET** /tracer/trace-session/{id}/ |  |
| [**getTraceSessionGraphData**](TracingApi.md#getTraceSessionGraphData) | **POST** /tracer/trace-session/get_session_graph_data/ | Fetch time-series session metrics for the observe graph. |
| [**getTraceSessionGraphDataWithHttpInfo**](TracingApi.md#getTraceSessionGraphDataWithHttpInfo) | **POST** /tracer/trace-session/get_session_graph_data/ | Fetch time-series session metrics for the observe graph. |
| [**getVoiceCallDetail**](TracingApi.md#getVoiceCallDetail) | **GET** /tracer/trace/voice_call_detail/ | Return the heavy / detail-only fields for a single voice call. |
| [**getVoiceCallDetailWithHttpInfo**](TracingApi.md#getVoiceCallDetailWithHttpInfo) | **GET** /tracer/trace/voice_call_detail/ | Return the heavy / detail-only fields for a single voice call. |
| [**listErrorFeedIssues**](TracingApi.md#listErrorFeedIssues) | **GET** /tracer/feed/issues/ |  |
| [**listErrorFeedIssuesWithHttpInfo**](TracingApi.md#listErrorFeedIssuesWithHttpInfo) | **GET** /tracer/feed/issues/ |  |
| [**listTraceAnnotationLabels**](TracingApi.md#listTraceAnnotationLabels) | **GET** /tracer/get-annotation-labels/ |  |
| [**listTraceAnnotationLabelsWithHttpInfo**](TracingApi.md#listTraceAnnotationLabelsWithHttpInfo) | **GET** /tracer/get-annotation-labels/ |  |
| [**listTraceProjects**](TracingApi.md#listTraceProjects) | **GET** /tracer/project/list_projects/ | List projects filtered by organization ID. |
| [**listTraceProjectsWithHttpInfo**](TracingApi.md#listTraceProjectsWithHttpInfo) | **GET** /tracer/project/list_projects/ | List projects filtered by organization ID. |
| [**listTraceProperties**](TracingApi.md#listTraceProperties) | **GET** /tracer/trace/get_properties/ |  |
| [**listTracePropertiesWithHttpInfo**](TracingApi.md#listTracePropertiesWithHttpInfo) | **GET** /tracer/trace/get_properties/ |  |
| [**listTraceSessions**](TracingApi.md#listTraceSessions) | **GET** /tracer/trace-session/list_sessions/ |  |
| [**listTraceSessionsWithHttpInfo**](TracingApi.md#listTraceSessionsWithHttpInfo) | **GET** /tracer/trace-session/list_sessions/ |  |
| [**listTraceUsers**](TracingApi.md#listTraceUsers) | **GET** /tracer/users/ |  |
| [**listTraceUsersWithHttpInfo**](TracingApi.md#listTraceUsersWithHttpInfo) | **GET** /tracer/users/ |  |
| [**listTraces**](TracingApi.md#listTraces) | **GET** /tracer/trace/list_traces/ |  |
| [**listTracesWithHttpInfo**](TracingApi.md#listTracesWithHttpInfo) | **GET** /tracer/trace/list_traces/ |  |
| [**listVoiceCalls**](TracingApi.md#listVoiceCalls) | **GET** /tracer/trace/list_voice_calls/ |  |
| [**listVoiceCallsWithHttpInfo**](TracingApi.md#listVoiceCallsWithHttpInfo) | **GET** /tracer/trace/list_voice_calls/ |  |
| [**updateTraceTags**](TracingApi.md#updateTraceTags) | **PATCH** /tracer/trace/{id}/tags/ |  |
| [**updateTraceTagsWithHttpInfo**](TracingApi.md#updateTraceTagsWithHttpInfo) | **PATCH** /tracer/trace/{id}/tags/ |  |



## createBulkTraceAnnotation

> BulkAnnotationResponse createBulkTraceAnnotation(bulkAnnotationRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        BulkAnnotationRequest bulkAnnotationRequest = new BulkAnnotationRequest(); // BulkAnnotationRequest | 
        try {
            BulkAnnotationResponse result = apiInstance.createBulkTraceAnnotation(bulkAnnotationRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#createBulkTraceAnnotation");
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
| **bulkAnnotationRequest** | [**BulkAnnotationRequest**](BulkAnnotationRequest.md)|  | |

### Return type

[**BulkAnnotationResponse**](BulkAnnotationResponse.md)


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

## createBulkTraceAnnotationWithHttpInfo

> ApiResponse<BulkAnnotationResponse> createBulkTraceAnnotation createBulkTraceAnnotationWithHttpInfo(bulkAnnotationRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        BulkAnnotationRequest bulkAnnotationRequest = new BulkAnnotationRequest(); // BulkAnnotationRequest | 
        try {
            ApiResponse<BulkAnnotationResponse> response = apiInstance.createBulkTraceAnnotationWithHttpInfo(bulkAnnotationRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#createBulkTraceAnnotation");
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
| **bulkAnnotationRequest** | [**BulkAnnotationRequest**](BulkAnnotationRequest.md)|  | |

### Return type

ApiResponse<[**BulkAnnotationResponse**](BulkAnnotationResponse.md)>


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


## getErrorFeedIssue

> FeedDetailApiResponse getErrorFeedIssue(clusterId, projectId)



GET + PATCH /tracer/feed/issues/{cluster_id}/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        UUID projectId = UUID.randomUUID(); // UUID | 
        try {
            FeedDetailApiResponse result = apiInstance.getErrorFeedIssue(clusterId, projectId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getErrorFeedIssue");
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
| **clusterId** | **String**|  | |
| **projectId** | **UUID**|  | [optional] |

### Return type

[**FeedDetailApiResponse**](FeedDetailApiResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getErrorFeedIssueWithHttpInfo

> ApiResponse<FeedDetailApiResponse> getErrorFeedIssue getErrorFeedIssueWithHttpInfo(clusterId, projectId)



GET + PATCH /tracer/feed/issues/{cluster_id}/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        UUID projectId = UUID.randomUUID(); // UUID | 
        try {
            ApiResponse<FeedDetailApiResponse> response = apiInstance.getErrorFeedIssueWithHttpInfo(clusterId, projectId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getErrorFeedIssue");
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
| **clusterId** | **String**|  | |
| **projectId** | **UUID**|  | [optional] |

### Return type

ApiResponse<[**FeedDetailApiResponse**](FeedDetailApiResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getErrorFeedIssueStats

> FeedStatsApiResponse getErrorFeedIssueStats(projectId, timeRangeDays)



GET /tracer/feed/issues/stats/ — top stats bar totals.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer timeRangeDays = 56; // Integer | 
        try {
            FeedStatsApiResponse result = apiInstance.getErrorFeedIssueStats(projectId, timeRangeDays);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getErrorFeedIssueStats");
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
| **projectId** | **UUID**|  | [optional] |
| **timeRangeDays** | **Integer**|  | [optional] |

### Return type

[**FeedStatsApiResponse**](FeedStatsApiResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## getErrorFeedIssueStatsWithHttpInfo

> ApiResponse<FeedStatsApiResponse> getErrorFeedIssueStats getErrorFeedIssueStatsWithHttpInfo(projectId, timeRangeDays)



GET /tracer/feed/issues/stats/ — top stats bar totals.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer timeRangeDays = 56; // Integer | 
        try {
            ApiResponse<FeedStatsApiResponse> response = apiInstance.getErrorFeedIssueStatsWithHttpInfo(projectId, timeRangeDays);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getErrorFeedIssueStats");
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
| **projectId** | **UUID**|  | [optional] |
| **timeRangeDays** | **Integer**|  | [optional] |

### Return type

ApiResponse<[**FeedStatsApiResponse**](FeedStatsApiResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## getTrace

> Trace getTrace(id)



Retrieve a trace by its ID.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            Trace result = apiInstance.getTrace(id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTrace");
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
| **id** | **String**|  | |

### Return type

[**Trace**](Trace.md)


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

## getTraceWithHttpInfo

> ApiResponse<Trace> getTrace getTraceWithHttpInfo(id)



Retrieve a trace by its ID.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<Trace> response = apiInstance.getTraceWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTrace");
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
| **id** | **String**|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


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


## getTraceGraphMethods

> ObserveGraphDataResponse getTraceGraphMethods(observeGraphDataRequest)



Fetch data for the observe graph with optimized queries

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        ObserveGraphDataRequest observeGraphDataRequest = new ObserveGraphDataRequest(); // ObserveGraphDataRequest | 
        try {
            ObserveGraphDataResponse result = apiInstance.getTraceGraphMethods(observeGraphDataRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceGraphMethods");
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
| **observeGraphDataRequest** | [**ObserveGraphDataRequest**](ObserveGraphDataRequest.md)|  | |

### Return type

[**ObserveGraphDataResponse**](ObserveGraphDataResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## getTraceGraphMethodsWithHttpInfo

> ApiResponse<ObserveGraphDataResponse> getTraceGraphMethods getTraceGraphMethodsWithHttpInfo(observeGraphDataRequest)



Fetch data for the observe graph with optimized queries

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        ObserveGraphDataRequest observeGraphDataRequest = new ObserveGraphDataRequest(); // ObserveGraphDataRequest | 
        try {
            ApiResponse<ObserveGraphDataResponse> response = apiInstance.getTraceGraphMethodsWithHttpInfo(observeGraphDataRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceGraphMethods");
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
| **observeGraphDataRequest** | [**ObserveGraphDataRequest**](ObserveGraphDataRequest.md)|  | |

### Return type

ApiResponse<[**ObserveGraphDataResponse**](ObserveGraphDataResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## getTraceSession

> TraceSession getTraceSession(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            TraceSession result = apiInstance.getTraceSession(id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceSession");
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
| **id** | **String**|  | |

### Return type

[**TraceSession**](TraceSession.md)


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

## getTraceSessionWithHttpInfo

> ApiResponse<TraceSession> getTraceSession getTraceSessionWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<TraceSession> response = apiInstance.getTraceSessionWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceSession");
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
| **id** | **String**|  | |

### Return type

ApiResponse<[**TraceSession**](TraceSession.md)>


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


## getTraceSessionGraphData

> TraceSessionGraphDataRequest getTraceSessionGraphData(traceSessionGraphDataRequest)

Fetch time-series session metrics for the observe graph.

Supports the same metric types as the trace graph endpoint: - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,   avg_duration, avg_traces_per_session — all aggregated at session level - EVAL: eval scores averaged across sessions - ANNOTATION: annotation scores averaged across sessions  Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        TraceSessionGraphDataRequest traceSessionGraphDataRequest = new TraceSessionGraphDataRequest(); // TraceSessionGraphDataRequest | 
        try {
            TraceSessionGraphDataRequest result = apiInstance.getTraceSessionGraphData(traceSessionGraphDataRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceSessionGraphData");
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
| **traceSessionGraphDataRequest** | [**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md)|  | |

### Return type

[**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## getTraceSessionGraphDataWithHttpInfo

> ApiResponse<TraceSessionGraphDataRequest> getTraceSessionGraphData getTraceSessionGraphDataWithHttpInfo(traceSessionGraphDataRequest)

Fetch time-series session metrics for the observe graph.

Supports the same metric types as the trace graph endpoint: - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,   avg_duration, avg_traces_per_session — all aggregated at session level - EVAL: eval scores averaged across sessions - ANNOTATION: annotation scores averaged across sessions  Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        TraceSessionGraphDataRequest traceSessionGraphDataRequest = new TraceSessionGraphDataRequest(); // TraceSessionGraphDataRequest | 
        try {
            ApiResponse<TraceSessionGraphDataRequest> response = apiInstance.getTraceSessionGraphDataWithHttpInfo(traceSessionGraphDataRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getTraceSessionGraphData");
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
| **traceSessionGraphDataRequest** | [**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md)|  | |

### Return type

ApiResponse<[**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## getVoiceCallDetail

> TracerTraceList200Response getVoiceCallDetail(page, limit)

Return the heavy / detail-only fields for a single voice call.

Query params: - trace_id (required) — UUID of the voice call trace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.getVoiceCallDetail(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getVoiceCallDetail");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


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

## getVoiceCallDetailWithHttpInfo

> ApiResponse<TracerTraceList200Response> getVoiceCallDetail getVoiceCallDetailWithHttpInfo(page, limit)

Return the heavy / detail-only fields for a single voice call.

Query params: - trace_id (required) — UUID of the voice call trace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.getVoiceCallDetailWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#getVoiceCallDetail");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


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


## listErrorFeedIssues

> FeedListApiResponse listErrorFeedIssues(projectId, search, status, fixLayer, source, issueGroup, timeRangeDays, sortBy, sortDir, limit, offset)



GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        String search = "search_example"; // String | 
        String status = "escalating"; // String | 
        String fixLayer = "fixLayer_example"; // String | 
        String source = "scanner"; // String | 
        String issueGroup = "issueGroup_example"; // String | 
        Integer timeRangeDays = 56; // Integer | 
        String sortBy = "last_seen"; // String | 
        String sortDir = "asc"; // String | 
        Integer limit = 25; // Integer | 
        Integer offset = 0; // Integer | 
        try {
            FeedListApiResponse result = apiInstance.listErrorFeedIssues(projectId, search, status, fixLayer, source, issueGroup, timeRangeDays, sortBy, sortDir, limit, offset);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listErrorFeedIssues");
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
| **projectId** | **UUID**|  | [optional] |
| **search** | **String**|  | [optional] |
| **status** | **String**|  | [optional] [enum: escalating, for_review, acknowledged, resolved] |
| **fixLayer** | **String**|  | [optional] |
| **source** | **String**|  | [optional] [enum: scanner, eval] |
| **issueGroup** | **String**|  | [optional] |
| **timeRangeDays** | **Integer**|  | [optional] |
| **sortBy** | **String**|  | [optional] [default to last_seen] [enum: last_seen, first_seen, error_count, unique_traces] |
| **sortDir** | **String**|  | [optional] [default to desc] [enum: asc, desc] |
| **limit** | **Integer**|  | [optional] [default to 25] |
| **offset** | **Integer**|  | [optional] [default to 0] |

### Return type

[**FeedListApiResponse**](FeedListApiResponse.md)


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## listErrorFeedIssuesWithHttpInfo

> ApiResponse<FeedListApiResponse> listErrorFeedIssues listErrorFeedIssuesWithHttpInfo(projectId, search, status, fixLayer, source, issueGroup, timeRangeDays, sortBy, sortDir, limit, offset)



GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        String search = "search_example"; // String | 
        String status = "escalating"; // String | 
        String fixLayer = "fixLayer_example"; // String | 
        String source = "scanner"; // String | 
        String issueGroup = "issueGroup_example"; // String | 
        Integer timeRangeDays = 56; // Integer | 
        String sortBy = "last_seen"; // String | 
        String sortDir = "asc"; // String | 
        Integer limit = 25; // Integer | 
        Integer offset = 0; // Integer | 
        try {
            ApiResponse<FeedListApiResponse> response = apiInstance.listErrorFeedIssuesWithHttpInfo(projectId, search, status, fixLayer, source, issueGroup, timeRangeDays, sortBy, sortDir, limit, offset);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listErrorFeedIssues");
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
| **projectId** | **UUID**|  | [optional] |
| **search** | **String**|  | [optional] |
| **status** | **String**|  | [optional] [enum: escalating, for_review, acknowledged, resolved] |
| **fixLayer** | **String**|  | [optional] |
| **source** | **String**|  | [optional] [enum: scanner, eval] |
| **issueGroup** | **String**|  | [optional] |
| **timeRangeDays** | **Integer**|  | [optional] |
| **sortBy** | **String**|  | [optional] [default to last_seen] [enum: last_seen, first_seen, error_count, unique_traces] |
| **sortDir** | **String**|  | [optional] [default to desc] [enum: asc, desc] |
| **limit** | **Integer**|  | [optional] [default to 25] |
| **offset** | **Integer**|  | [optional] [default to 0] |

### Return type

ApiResponse<[**FeedListApiResponse**](FeedListApiResponse.md)>


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
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## listTraceAnnotationLabels

> GetAnnotationLabelsResponse listTraceAnnotationLabels(projectId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        try {
            GetAnnotationLabelsResponse result = apiInstance.listTraceAnnotationLabels(projectId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceAnnotationLabels");
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
| **projectId** | **UUID**|  | [optional] |

### Return type

[**GetAnnotationLabelsResponse**](GetAnnotationLabelsResponse.md)


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

## listTraceAnnotationLabelsWithHttpInfo

> ApiResponse<GetAnnotationLabelsResponse> listTraceAnnotationLabels listTraceAnnotationLabelsWithHttpInfo(projectId)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        try {
            ApiResponse<GetAnnotationLabelsResponse> response = apiInstance.listTraceAnnotationLabelsWithHttpInfo(projectId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceAnnotationLabels");
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
| **projectId** | **UUID**|  | [optional] |

### Return type

ApiResponse<[**GetAnnotationLabelsResponse**](GetAnnotationLabelsResponse.md)>


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


## listTraceProjects

> ListTraceProjects200Response listTraceProjects(page, limit)

List projects filtered by organization ID.

Volume counts come from ClickHouse (fast) instead of a PG JOIN on observation_spans (was 12+ seconds).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ListTraceProjects200Response result = apiInstance.listTraceProjects(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceProjects");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**ListTraceProjects200Response**](ListTraceProjects200Response.md)


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

## listTraceProjectsWithHttpInfo

> ApiResponse<ListTraceProjects200Response> listTraceProjects listTraceProjectsWithHttpInfo(page, limit)

List projects filtered by organization ID.

Volume counts come from ClickHouse (fast) instead of a PG JOIN on observation_spans (was 12+ seconds).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<ListTraceProjects200Response> response = apiInstance.listTraceProjectsWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceProjects");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**ListTraceProjects200Response**](ListTraceProjects200Response.md)>


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


## listTraceProperties

> TracerTraceList200Response listTraceProperties(page, limit)



Fetch all properties for graphing.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.listTraceProperties(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceProperties");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


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

## listTracePropertiesWithHttpInfo

> ApiResponse<TracerTraceList200Response> listTraceProperties listTracePropertiesWithHttpInfo(page, limit)



Fetch all properties for graphing.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.listTracePropertiesWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceProperties");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


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


## listTraceSessions

> TracerTraceSessionList200Response listTraceSessions(page, limit, projectId, userId, bookmarked, filters, sortParams, pageNumber, pageSize, interval)



List traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        UUID projectId = UUID.randomUUID(); // UUID | 
        String userId = "userId_example"; // String | 
        Boolean bookmarked = true; // Boolean | 
        String filters = "[]"; // String | 
        String sortParams = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        String interval = "interval_example"; // String | 
        try {
            TracerTraceSessionList200Response result = apiInstance.listTraceSessions(page, limit, projectId, userId, bookmarked, filters, sortParams, pageNumber, pageSize, interval);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceSessions");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **projectId** | **UUID**|  | [optional] |
| **userId** | **String**|  | [optional] |
| **bookmarked** | **Boolean**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |
| **interval** | **String**|  | [optional] |

### Return type

[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)


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

## listTraceSessionsWithHttpInfo

> ApiResponse<TracerTraceSessionList200Response> listTraceSessions listTraceSessionsWithHttpInfo(page, limit, projectId, userId, bookmarked, filters, sortParams, pageNumber, pageSize, interval)



List traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        UUID projectId = UUID.randomUUID(); // UUID | 
        String userId = "userId_example"; // String | 
        Boolean bookmarked = true; // Boolean | 
        String filters = "[]"; // String | 
        String sortParams = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        String interval = "interval_example"; // String | 
        try {
            ApiResponse<TracerTraceSessionList200Response> response = apiInstance.listTraceSessionsWithHttpInfo(page, limit, projectId, userId, bookmarked, filters, sortParams, pageNumber, pageSize, interval);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceSessions");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **projectId** | **UUID**|  | [optional] |
| **userId** | **String**|  | [optional] |
| **bookmarked** | **Boolean**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |
| **interval** | **String**|  | [optional] |

### Return type

ApiResponse<[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)>


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


## listTraceUsers

> UsersResponse listTraceUsers(projectId, search, pageSize, currentPageIndex, sortParams, filters)



List traces filtered by project ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        String search = "search_example"; // String | 
        Integer pageSize = 56; // Integer | 
        Integer currentPageIndex = 56; // Integer | 
        String sortParams = "[]"; // String | 
        String filters = "[]"; // String | 
        try {
            UsersResponse result = apiInstance.listTraceUsers(projectId, search, pageSize, currentPageIndex, sortParams, filters);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceUsers");
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
| **projectId** | **UUID**|  | [optional] |
| **search** | **String**|  | [optional] |
| **pageSize** | **Integer**|  | [optional] |
| **currentPageIndex** | **Integer**|  | [optional] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

[**UsersResponse**](UsersResponse.md)


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

## listTraceUsersWithHttpInfo

> ApiResponse<UsersResponse> listTraceUsers listTraceUsersWithHttpInfo(projectId, search, pageSize, currentPageIndex, sortParams, filters)



List traces filtered by project ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        String search = "search_example"; // String | 
        Integer pageSize = 56; // Integer | 
        Integer currentPageIndex = 56; // Integer | 
        String sortParams = "[]"; // String | 
        String filters = "[]"; // String | 
        try {
            ApiResponse<UsersResponse> response = apiInstance.listTraceUsersWithHttpInfo(projectId, search, pageSize, currentPageIndex, sortParams, filters);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraceUsers");
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
| **projectId** | **UUID**|  | [optional] |
| **search** | **String**|  | [optional] |
| **pageSize** | **Integer**|  | [optional] |
| **currentPageIndex** | **Integer**|  | [optional] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

ApiResponse<[**UsersResponse**](UsersResponse.md)>


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


## listTraces

> TracerTraceList200Response listTraces(projectVersionId, page, limit, traceIds, filters, sortParams, pageNumber, pageSize)



List traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String traceIds = "traceIds_example"; // String | 
        String filters = "[]"; // String | 
        String sortParams = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        try {
            TracerTraceList200Response result = apiInstance.listTraces(projectVersionId, page, limit, traceIds, filters, sortParams, pageNumber, pageSize);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraces");
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
| **projectVersionId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **traceIds** | **String**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


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

## listTracesWithHttpInfo

> ApiResponse<TracerTraceList200Response> listTraces listTracesWithHttpInfo(projectVersionId, page, limit, traceIds, filters, sortParams, pageNumber, pageSize)



List traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String traceIds = "traceIds_example"; // String | 
        String filters = "[]"; // String | 
        String sortParams = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.listTracesWithHttpInfo(projectVersionId, page, limit, traceIds, filters, sortParams, pageNumber, pageSize);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listTraces");
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
| **projectVersionId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **traceIds** | **String**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **sortParams** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


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


## listVoiceCalls

> TracerTraceList200Response listVoiceCalls(page, limit)



List voice/conversation traces for a project in an optimized way and return a response similar to the provided call object schema.  Query params: - project_id (required) - page (1-based, optional, default 1) - page_size (optional, default 30)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.listVoiceCalls(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listVoiceCalls");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


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

## listVoiceCallsWithHttpInfo

> ApiResponse<TracerTraceList200Response> listVoiceCalls listVoiceCallsWithHttpInfo(page, limit)



List voice/conversation traces for a project in an optimized way and return a response similar to the provided call object schema.  Query params: - project_id (required) - page (1-based, optional, default 1) - page_size (optional, default 30)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.listVoiceCallsWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#listVoiceCalls");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


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


## updateTraceTags

> TraceTagsUpdate updateTraceTags(id, traceTagsUpdate)



Update tags for a trace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        TraceTagsUpdate traceTagsUpdate = new TraceTagsUpdate(); // TraceTagsUpdate | 
        try {
            TraceTagsUpdate result = apiInstance.updateTraceTags(id, traceTagsUpdate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#updateTraceTags");
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
| **id** | **String**|  | |
| **traceTagsUpdate** | [**TraceTagsUpdate**](TraceTagsUpdate.md)|  | |

### Return type

[**TraceTagsUpdate**](TraceTagsUpdate.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## updateTraceTagsWithHttpInfo

> ApiResponse<TraceTagsUpdate> updateTraceTags updateTraceTagsWithHttpInfo(id, traceTagsUpdate)



Update tags for a trace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracingApi;

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

        TracingApi apiInstance = new TracingApi(defaultClient);
        String id = "id_example"; // String | 
        TraceTagsUpdate traceTagsUpdate = new TraceTagsUpdate(); // TraceTagsUpdate | 
        try {
            ApiResponse<TraceTagsUpdate> response = apiInstance.updateTraceTagsWithHttpInfo(id, traceTagsUpdate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracingApi#updateTraceTags");
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
| **id** | **String**|  | |
| **traceTagsUpdate** | [**TraceTagsUpdate**](TraceTagsUpdate.md)|  | |

### Return type

ApiResponse<[**TraceTagsUpdate**](TraceTagsUpdate.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

