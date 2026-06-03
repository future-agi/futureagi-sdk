# AnnotationQueueDiscussionApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createAnnotationQueueItemComment**](AnnotationQueueDiscussionApi.md#createAnnotationQueueItemComment) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ |  |
| [**createAnnotationQueueItemCommentWithHttpInfo**](AnnotationQueueDiscussionApi.md#createAnnotationQueueItemCommentWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ |  |
| [**listAnnotationQueueItemDiscussion**](AnnotationQueueDiscussionApi.md#listAnnotationQueueItemDiscussion) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ |  |
| [**listAnnotationQueueItemDiscussionWithHttpInfo**](AnnotationQueueDiscussionApi.md#listAnnotationQueueItemDiscussionWithHttpInfo) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ |  |
| [**reopenAnnotationQueueItemThread**](AnnotationQueueDiscussionApi.md#reopenAnnotationQueueItemThread) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/reopen/ |  |
| [**reopenAnnotationQueueItemThreadWithHttpInfo**](AnnotationQueueDiscussionApi.md#reopenAnnotationQueueItemThreadWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/reopen/ |  |
| [**resolveAnnotationQueueItemThread**](AnnotationQueueDiscussionApi.md#resolveAnnotationQueueItemThread) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/resolve/ |  |
| [**resolveAnnotationQueueItemThreadWithHttpInfo**](AnnotationQueueDiscussionApi.md#resolveAnnotationQueueItemThreadWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/resolve/ |  |
| [**toggleAnnotationQueueItemCommentReaction**](AnnotationQueueDiscussionApi.md#toggleAnnotationQueueItemCommentReaction) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/comments/{comment_id}/reaction/ |  |
| [**toggleAnnotationQueueItemCommentReactionWithHttpInfo**](AnnotationQueueDiscussionApi.md#toggleAnnotationQueueItemCommentReactionWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/comments/{comment_id}/reaction/ |  |



## createAnnotationQueueItemComment

> QueueDiscussionResponse createAnnotationQueueItemComment(queueId, id, discussionCommentRequest)



List or create non-blocking discussion comments for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        DiscussionCommentRequest discussionCommentRequest = new DiscussionCommentRequest(); // DiscussionCommentRequest | 
        try {
            QueueDiscussionResponse result = apiInstance.createAnnotationQueueItemComment(queueId, id, discussionCommentRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#createAnnotationQueueItemComment");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **discussionCommentRequest** | [**DiscussionCommentRequest**](DiscussionCommentRequest.md)|  | |

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)


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

## createAnnotationQueueItemCommentWithHttpInfo

> ApiResponse<QueueDiscussionResponse> createAnnotationQueueItemComment createAnnotationQueueItemCommentWithHttpInfo(queueId, id, discussionCommentRequest)



List or create non-blocking discussion comments for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        DiscussionCommentRequest discussionCommentRequest = new DiscussionCommentRequest(); // DiscussionCommentRequest | 
        try {
            ApiResponse<QueueDiscussionResponse> response = apiInstance.createAnnotationQueueItemCommentWithHttpInfo(queueId, id, discussionCommentRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#createAnnotationQueueItemComment");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **discussionCommentRequest** | [**DiscussionCommentRequest**](DiscussionCommentRequest.md)|  | |

### Return type

ApiResponse<[**QueueDiscussionResponse**](QueueDiscussionResponse.md)>


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


## listAnnotationQueueItemDiscussion

> QueueDiscussionResponse listAnnotationQueueItemDiscussion(queueId, id)



List or create non-blocking discussion comments for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        try {
            QueueDiscussionResponse result = apiInstance.listAnnotationQueueItemDiscussion(queueId, id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#listAnnotationQueueItemDiscussion");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)


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

## listAnnotationQueueItemDiscussionWithHttpInfo

> ApiResponse<QueueDiscussionResponse> listAnnotationQueueItemDiscussion listAnnotationQueueItemDiscussionWithHttpInfo(queueId, id)



List or create non-blocking discussion comments for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        try {
            ApiResponse<QueueDiscussionResponse> response = apiInstance.listAnnotationQueueItemDiscussionWithHttpInfo(queueId, id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#listAnnotationQueueItemDiscussion");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |

### Return type

ApiResponse<[**QueueDiscussionResponse**](QueueDiscussionResponse.md)>


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


## reopenAnnotationQueueItemThread

> QueueDiscussionResponse reopenAnnotationQueueItemThread(queueId, id, threadId, discussionThreadStatusRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String threadId = "threadId_example"; // String | 
        DiscussionThreadStatusRequest discussionThreadStatusRequest = new DiscussionThreadStatusRequest(); // DiscussionThreadStatusRequest | 
        try {
            QueueDiscussionResponse result = apiInstance.reopenAnnotationQueueItemThread(queueId, id, threadId, discussionThreadStatusRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#reopenAnnotationQueueItemThread");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **threadId** | **String**|  | |
| **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md)|  | |

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)


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

## reopenAnnotationQueueItemThreadWithHttpInfo

> ApiResponse<QueueDiscussionResponse> reopenAnnotationQueueItemThread reopenAnnotationQueueItemThreadWithHttpInfo(queueId, id, threadId, discussionThreadStatusRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String threadId = "threadId_example"; // String | 
        DiscussionThreadStatusRequest discussionThreadStatusRequest = new DiscussionThreadStatusRequest(); // DiscussionThreadStatusRequest | 
        try {
            ApiResponse<QueueDiscussionResponse> response = apiInstance.reopenAnnotationQueueItemThreadWithHttpInfo(queueId, id, threadId, discussionThreadStatusRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#reopenAnnotationQueueItemThread");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **threadId** | **String**|  | |
| **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md)|  | |

### Return type

ApiResponse<[**QueueDiscussionResponse**](QueueDiscussionResponse.md)>


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


## resolveAnnotationQueueItemThread

> QueueDiscussionResponse resolveAnnotationQueueItemThread(queueId, id, threadId, discussionThreadStatusRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String threadId = "threadId_example"; // String | 
        DiscussionThreadStatusRequest discussionThreadStatusRequest = new DiscussionThreadStatusRequest(); // DiscussionThreadStatusRequest | 
        try {
            QueueDiscussionResponse result = apiInstance.resolveAnnotationQueueItemThread(queueId, id, threadId, discussionThreadStatusRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#resolveAnnotationQueueItemThread");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **threadId** | **String**|  | |
| **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md)|  | |

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)


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

## resolveAnnotationQueueItemThreadWithHttpInfo

> ApiResponse<QueueDiscussionResponse> resolveAnnotationQueueItemThread resolveAnnotationQueueItemThreadWithHttpInfo(queueId, id, threadId, discussionThreadStatusRequest)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String threadId = "threadId_example"; // String | 
        DiscussionThreadStatusRequest discussionThreadStatusRequest = new DiscussionThreadStatusRequest(); // DiscussionThreadStatusRequest | 
        try {
            ApiResponse<QueueDiscussionResponse> response = apiInstance.resolveAnnotationQueueItemThreadWithHttpInfo(queueId, id, threadId, discussionThreadStatusRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#resolveAnnotationQueueItemThread");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **threadId** | **String**|  | |
| **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md)|  | |

### Return type

ApiResponse<[**QueueDiscussionResponse**](QueueDiscussionResponse.md)>


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


## toggleAnnotationQueueItemCommentReaction

> QueueDiscussionResponse toggleAnnotationQueueItemCommentReaction(queueId, id, commentId, discussionReactionRequest)



Toggle the current user&#39;s reaction on a discussion comment.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String commentId = "commentId_example"; // String | 
        DiscussionReactionRequest discussionReactionRequest = new DiscussionReactionRequest(); // DiscussionReactionRequest | 
        try {
            QueueDiscussionResponse result = apiInstance.toggleAnnotationQueueItemCommentReaction(queueId, id, commentId, discussionReactionRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#toggleAnnotationQueueItemCommentReaction");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **commentId** | **String**|  | |
| **discussionReactionRequest** | [**DiscussionReactionRequest**](DiscussionReactionRequest.md)|  | |

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)


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

## toggleAnnotationQueueItemCommentReactionWithHttpInfo

> ApiResponse<QueueDiscussionResponse> toggleAnnotationQueueItemCommentReaction toggleAnnotationQueueItemCommentReactionWithHttpInfo(queueId, id, commentId, discussionReactionRequest)



Toggle the current user&#39;s reaction on a discussion comment.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueDiscussionApi;

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

        AnnotationQueueDiscussionApi apiInstance = new AnnotationQueueDiscussionApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        String commentId = "commentId_example"; // String | 
        DiscussionReactionRequest discussionReactionRequest = new DiscussionReactionRequest(); // DiscussionReactionRequest | 
        try {
            ApiResponse<QueueDiscussionResponse> response = apiInstance.toggleAnnotationQueueItemCommentReactionWithHttpInfo(queueId, id, commentId, discussionReactionRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueDiscussionApi#toggleAnnotationQueueItemCommentReaction");
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
| **queueId** | **String**|  | |
| **id** | **UUID**| A UUID string identifying this queue item. | |
| **commentId** | **String**|  | |
| **discussionReactionRequest** | [**DiscussionReactionRequest**](DiscussionReactionRequest.md)|  | |

### Return type

ApiResponse<[**QueueDiscussionResponse**](QueueDiscussionResponse.md)>


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

