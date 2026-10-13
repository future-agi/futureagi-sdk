# AnnotationQueueReviewApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**reviewAnnotationQueueItem**](AnnotationQueueReviewApi.md#reviewAnnotationQueueItem) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/review/ |  |
| [**reviewAnnotationQueueItemWithHttpInfo**](AnnotationQueueReviewApi.md#reviewAnnotationQueueItemWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/review/ |  |



## reviewAnnotationQueueItem

> QueueReviewItemResponse reviewAnnotationQueueItem(queueId, id, reviewItemRequest)



Approve, request changes, or leave reviewer feedback on an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueReviewApi;

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

        AnnotationQueueReviewApi apiInstance = new AnnotationQueueReviewApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        ReviewItemRequest reviewItemRequest = new ReviewItemRequest(); // ReviewItemRequest | 
        try {
            QueueReviewItemResponse result = apiInstance.reviewAnnotationQueueItem(queueId, id, reviewItemRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueReviewApi#reviewAnnotationQueueItem");
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
| **reviewItemRequest** | [**ReviewItemRequest**](ReviewItemRequest.md)|  | |

### Return type

[**QueueReviewItemResponse**](QueueReviewItemResponse.md)


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

## reviewAnnotationQueueItemWithHttpInfo

> ApiResponse<QueueReviewItemResponse> reviewAnnotationQueueItem reviewAnnotationQueueItemWithHttpInfo(queueId, id, reviewItemRequest)



Approve, request changes, or leave reviewer feedback on an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueReviewApi;

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

        AnnotationQueueReviewApi apiInstance = new AnnotationQueueReviewApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        ReviewItemRequest reviewItemRequest = new ReviewItemRequest(); // ReviewItemRequest | 
        try {
            ApiResponse<QueueReviewItemResponse> response = apiInstance.reviewAnnotationQueueItemWithHttpInfo(queueId, id, reviewItemRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueReviewApi#reviewAnnotationQueueItem");
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
| **reviewItemRequest** | [**ReviewItemRequest**](ReviewItemRequest.md)|  | |

### Return type

ApiResponse<[**QueueReviewItemResponse**](QueueReviewItemResponse.md)>


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

