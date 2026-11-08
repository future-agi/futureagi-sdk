# AnnotationQueueItemsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**addAnnotationQueueItems**](AnnotationQueueItemsApi.md#addAnnotationQueueItems) | **POST** /model-hub/annotation-queues/{queue_id}/items/add-items/ |  |
| [**addAnnotationQueueItemsWithHttpInfo**](AnnotationQueueItemsApi.md#addAnnotationQueueItemsWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/add-items/ |  |
| [**assignAnnotationQueueItems**](AnnotationQueueItemsApi.md#assignAnnotationQueueItems) | **POST** /model-hub/annotation-queues/{queue_id}/items/assign/ |  |
| [**assignAnnotationQueueItemsWithHttpInfo**](AnnotationQueueItemsApi.md#assignAnnotationQueueItemsWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/assign/ |  |
| [**completeAnnotationQueueItem**](AnnotationQueueItemsApi.md#completeAnnotationQueueItem) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/complete/ |  |
| [**completeAnnotationQueueItemWithHttpInfo**](AnnotationQueueItemsApi.md#completeAnnotationQueueItemWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/complete/ |  |
| [**getAnnotationQueueItemDetail**](AnnotationQueueItemsApi.md#getAnnotationQueueItemDetail) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/annotate-detail/ |  |
| [**getAnnotationQueueItemDetailWithHttpInfo**](AnnotationQueueItemsApi.md#getAnnotationQueueItemDetailWithHttpInfo) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/annotate-detail/ |  |
| [**getNextAnnotationQueueItem**](AnnotationQueueItemsApi.md#getNextAnnotationQueueItem) | **GET** /model-hub/annotation-queues/{queue_id}/items/next-item/ | Get the next or previous item in the queue. |
| [**getNextAnnotationQueueItemWithHttpInfo**](AnnotationQueueItemsApi.md#getNextAnnotationQueueItemWithHttpInfo) | **GET** /model-hub/annotation-queues/{queue_id}/items/next-item/ | Get the next or previous item in the queue. |
| [**importAnnotationQueueItemAnnotations**](AnnotationQueueItemsApi.md#importAnnotationQueueItemAnnotations) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/import/ |  |
| [**importAnnotationQueueItemAnnotationsWithHttpInfo**](AnnotationQueueItemsApi.md#importAnnotationQueueItemAnnotationsWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/import/ |  |
| [**listAnnotationQueueItemAnnotations**](AnnotationQueueItemsApi.md#listAnnotationQueueItemAnnotations) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/ |  |
| [**listAnnotationQueueItemAnnotationsWithHttpInfo**](AnnotationQueueItemsApi.md#listAnnotationQueueItemAnnotationsWithHttpInfo) | **GET** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/ |  |
| [**listAnnotationQueueItems**](AnnotationQueueItemsApi.md#listAnnotationQueueItems) | **GET** /model-hub/annotation-queues/{queue_id}/items/ |  |
| [**listAnnotationQueueItemsWithHttpInfo**](AnnotationQueueItemsApi.md#listAnnotationQueueItemsWithHttpInfo) | **GET** /model-hub/annotation-queues/{queue_id}/items/ |  |
| [**releaseAnnotationQueueItem**](AnnotationQueueItemsApi.md#releaseAnnotationQueueItem) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/release/ |  |
| [**releaseAnnotationQueueItemWithHttpInfo**](AnnotationQueueItemsApi.md#releaseAnnotationQueueItemWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/release/ |  |
| [**removeAnnotationQueueItems**](AnnotationQueueItemsApi.md#removeAnnotationQueueItems) | **POST** /model-hub/annotation-queues/{queue_id}/items/bulk-remove/ |  |
| [**removeAnnotationQueueItemsWithHttpInfo**](AnnotationQueueItemsApi.md#removeAnnotationQueueItemsWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/bulk-remove/ |  |
| [**skipAnnotationQueueItem**](AnnotationQueueItemsApi.md#skipAnnotationQueueItem) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/skip/ |  |
| [**skipAnnotationQueueItemWithHttpInfo**](AnnotationQueueItemsApi.md#skipAnnotationQueueItemWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/skip/ |  |
| [**submitAnnotationQueueItemAnnotations**](AnnotationQueueItemsApi.md#submitAnnotationQueueItemAnnotations) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/submit/ |  |
| [**submitAnnotationQueueItemAnnotationsWithHttpInfo**](AnnotationQueueItemsApi.md#submitAnnotationQueueItemAnnotationsWithHttpInfo) | **POST** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/submit/ |  |



## addAnnotationQueueItems

> QueueAddItemsResponse addAnnotationQueueItems(queueId, addItems)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        AddItems addItems = new AddItems(); // AddItems | 
        try {
            QueueAddItemsResponse result = apiInstance.addAnnotationQueueItems(queueId, addItems);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#addAnnotationQueueItems");
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
| **addItems** | [**AddItems**](AddItems.md)|  | |

### Return type

[**QueueAddItemsResponse**](QueueAddItemsResponse.md)


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
| **0** | Default error response |  -  |

## addAnnotationQueueItemsWithHttpInfo

> ApiResponse<QueueAddItemsResponse> addAnnotationQueueItems addAnnotationQueueItemsWithHttpInfo(queueId, addItems)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        AddItems addItems = new AddItems(); // AddItems | 
        try {
            ApiResponse<QueueAddItemsResponse> response = apiInstance.addAnnotationQueueItemsWithHttpInfo(queueId, addItems);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#addAnnotationQueueItems");
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
| **addItems** | [**AddItems**](AddItems.md)|  | |

### Return type

ApiResponse<[**QueueAddItemsResponse**](QueueAddItemsResponse.md)>


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
| **0** | Default error response |  -  |


## assignAnnotationQueueItems

> QueueAssignItemsResponse assignAnnotationQueueItems(queueId, assignItems)



Assign items to one or more annotators.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        AssignItems assignItems = new AssignItems(); // AssignItems | 
        try {
            QueueAssignItemsResponse result = apiInstance.assignAnnotationQueueItems(queueId, assignItems);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#assignAnnotationQueueItems");
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
| **assignItems** | [**AssignItems**](AssignItems.md)|  | |

### Return type

[**QueueAssignItemsResponse**](QueueAssignItemsResponse.md)


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

## assignAnnotationQueueItemsWithHttpInfo

> ApiResponse<QueueAssignItemsResponse> assignAnnotationQueueItems assignAnnotationQueueItemsWithHttpInfo(queueId, assignItems)



Assign items to one or more annotators.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        AssignItems assignItems = new AssignItems(); // AssignItems | 
        try {
            ApiResponse<QueueAssignItemsResponse> response = apiInstance.assignAnnotationQueueItemsWithHttpInfo(queueId, assignItems);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#assignAnnotationQueueItems");
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
| **assignItems** | [**AssignItems**](AssignItems.md)|  | |

### Return type

ApiResponse<[**QueueAssignItemsResponse**](QueueAssignItemsResponse.md)>


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


## completeAnnotationQueueItem

> QueueNavigationResponse completeAnnotationQueueItem(queueId, id, queueItemNavigationRequest)



Mark item as completed and return next pending item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        QueueItemNavigationRequest queueItemNavigationRequest = new QueueItemNavigationRequest(); // QueueItemNavigationRequest | 
        try {
            QueueNavigationResponse result = apiInstance.completeAnnotationQueueItem(queueId, id, queueItemNavigationRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#completeAnnotationQueueItem");
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
| **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md)|  | |

### Return type

[**QueueNavigationResponse**](QueueNavigationResponse.md)


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

## completeAnnotationQueueItemWithHttpInfo

> ApiResponse<QueueNavigationResponse> completeAnnotationQueueItem completeAnnotationQueueItemWithHttpInfo(queueId, id, queueItemNavigationRequest)



Mark item as completed and return next pending item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        QueueItemNavigationRequest queueItemNavigationRequest = new QueueItemNavigationRequest(); // QueueItemNavigationRequest | 
        try {
            ApiResponse<QueueNavigationResponse> response = apiInstance.completeAnnotationQueueItemWithHttpInfo(queueId, id, queueItemNavigationRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#completeAnnotationQueueItem");
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
| **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md)|  | |

### Return type

ApiResponse<[**QueueNavigationResponse**](QueueNavigationResponse.md)>


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


## getAnnotationQueueItemDetail

> QueueAnnotateDetailResponse getAnnotationQueueItemDetail(queueId, id, annotatorId, includeCompleted, viewMode, reviewStatus, excludeReviewStatus, includeAllAnnotations, reserve)



Get full annotation workspace data for an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        UUID annotatorId = UUID.randomUUID(); // UUID | 
        Boolean includeCompleted = true; // Boolean | 
        String viewMode = "viewMode_example"; // String | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String excludeReviewStatus = "excludeReviewStatus_example"; // String | 
        Boolean includeAllAnnotations = true; // Boolean | 
        Boolean reserve = true; // Boolean | 
        try {
            QueueAnnotateDetailResponse result = apiInstance.getAnnotationQueueItemDetail(queueId, id, annotatorId, includeCompleted, viewMode, reviewStatus, excludeReviewStatus, includeAllAnnotations, reserve);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#getAnnotationQueueItemDetail");
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
| **annotatorId** | **UUID**|  | [optional] |
| **includeCompleted** | **Boolean**|  | [optional] |
| **viewMode** | **String**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **excludeReviewStatus** | **String**|  | [optional] |
| **includeAllAnnotations** | **Boolean**|  | [optional] |
| **reserve** | **Boolean**|  | [optional] |

### Return type

[**QueueAnnotateDetailResponse**](QueueAnnotateDetailResponse.md)


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

## getAnnotationQueueItemDetailWithHttpInfo

> ApiResponse<QueueAnnotateDetailResponse> getAnnotationQueueItemDetail getAnnotationQueueItemDetailWithHttpInfo(queueId, id, annotatorId, includeCompleted, viewMode, reviewStatus, excludeReviewStatus, includeAllAnnotations, reserve)



Get full annotation workspace data for an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        UUID annotatorId = UUID.randomUUID(); // UUID | 
        Boolean includeCompleted = true; // Boolean | 
        String viewMode = "viewMode_example"; // String | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String excludeReviewStatus = "excludeReviewStatus_example"; // String | 
        Boolean includeAllAnnotations = true; // Boolean | 
        Boolean reserve = true; // Boolean | 
        try {
            ApiResponse<QueueAnnotateDetailResponse> response = apiInstance.getAnnotationQueueItemDetailWithHttpInfo(queueId, id, annotatorId, includeCompleted, viewMode, reviewStatus, excludeReviewStatus, includeAllAnnotations, reserve);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#getAnnotationQueueItemDetail");
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
| **annotatorId** | **UUID**|  | [optional] |
| **includeCompleted** | **Boolean**|  | [optional] |
| **viewMode** | **String**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **excludeReviewStatus** | **String**|  | [optional] |
| **includeAllAnnotations** | **Boolean**|  | [optional] |
| **reserve** | **Boolean**|  | [optional] |

### Return type

ApiResponse<[**QueueAnnotateDetailResponse**](QueueAnnotateDetailResponse.md)>


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


## getNextAnnotationQueueItem

> QueueNextItemResponse getNextAnnotationQueueItem(queueId, page, limit, exclude, before, reviewStatus, excludeReviewStatus, includeCompleted, viewMode, includeAllAnnotations)

Get the next or previous item in the queue.

Query params:   exclude: comma-separated item IDs to skip   before:  item ID — returns the item immediately before this one in order   review_status: optional review status filter (for reviewer queues)   exclude_review_status: optional review status to omit (for annotator queues)   include_completed: when true, navigation can visit completed items too

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String exclude = "exclude_example"; // String | 
        UUID before = UUID.randomUUID(); // UUID | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String excludeReviewStatus = "excludeReviewStatus_example"; // String | 
        Boolean includeCompleted = true; // Boolean | 
        String viewMode = "viewMode_example"; // String | 
        Boolean includeAllAnnotations = true; // Boolean | 
        try {
            QueueNextItemResponse result = apiInstance.getNextAnnotationQueueItem(queueId, page, limit, exclude, before, reviewStatus, excludeReviewStatus, includeCompleted, viewMode, includeAllAnnotations);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#getNextAnnotationQueueItem");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **exclude** | **String**|  | [optional] |
| **before** | **UUID**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **excludeReviewStatus** | **String**|  | [optional] |
| **includeCompleted** | **Boolean**|  | [optional] |
| **viewMode** | **String**|  | [optional] |
| **includeAllAnnotations** | **Boolean**|  | [optional] |

### Return type

[**QueueNextItemResponse**](QueueNextItemResponse.md)


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

## getNextAnnotationQueueItemWithHttpInfo

> ApiResponse<QueueNextItemResponse> getNextAnnotationQueueItem getNextAnnotationQueueItemWithHttpInfo(queueId, page, limit, exclude, before, reviewStatus, excludeReviewStatus, includeCompleted, viewMode, includeAllAnnotations)

Get the next or previous item in the queue.

Query params:   exclude: comma-separated item IDs to skip   before:  item ID — returns the item immediately before this one in order   review_status: optional review status filter (for reviewer queues)   exclude_review_status: optional review status to omit (for annotator queues)   include_completed: when true, navigation can visit completed items too

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String exclude = "exclude_example"; // String | 
        UUID before = UUID.randomUUID(); // UUID | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String excludeReviewStatus = "excludeReviewStatus_example"; // String | 
        Boolean includeCompleted = true; // Boolean | 
        String viewMode = "viewMode_example"; // String | 
        Boolean includeAllAnnotations = true; // Boolean | 
        try {
            ApiResponse<QueueNextItemResponse> response = apiInstance.getNextAnnotationQueueItemWithHttpInfo(queueId, page, limit, exclude, before, reviewStatus, excludeReviewStatus, includeCompleted, viewMode, includeAllAnnotations);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#getNextAnnotationQueueItem");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **exclude** | **String**|  | [optional] |
| **before** | **UUID**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **excludeReviewStatus** | **String**|  | [optional] |
| **includeCompleted** | **Boolean**|  | [optional] |
| **viewMode** | **String**|  | [optional] |
| **includeAllAnnotations** | **Boolean**|  | [optional] |

### Return type

ApiResponse<[**QueueNextItemResponse**](QueueNextItemResponse.md)>


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


## importAnnotationQueueItemAnnotations

> QueueImportAnnotationsResponse importAnnotationQueueItemAnnotations(queueId, id, importAnnotations)



Import annotations from external sources.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        ImportAnnotations importAnnotations = new ImportAnnotations(); // ImportAnnotations | 
        try {
            QueueImportAnnotationsResponse result = apiInstance.importAnnotationQueueItemAnnotations(queueId, id, importAnnotations);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#importAnnotationQueueItemAnnotations");
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
| **importAnnotations** | [**ImportAnnotations**](ImportAnnotations.md)|  | |

### Return type

[**QueueImportAnnotationsResponse**](QueueImportAnnotationsResponse.md)


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

## importAnnotationQueueItemAnnotationsWithHttpInfo

> ApiResponse<QueueImportAnnotationsResponse> importAnnotationQueueItemAnnotations importAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id, importAnnotations)



Import annotations from external sources.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        ImportAnnotations importAnnotations = new ImportAnnotations(); // ImportAnnotations | 
        try {
            ApiResponse<QueueImportAnnotationsResponse> response = apiInstance.importAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id, importAnnotations);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#importAnnotationQueueItemAnnotations");
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
| **importAnnotations** | [**ImportAnnotations**](ImportAnnotations.md)|  | |

### Return type

ApiResponse<[**QueueImportAnnotationsResponse**](QueueImportAnnotationsResponse.md)>


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


## listAnnotationQueueItemAnnotations

> QueueItemAnnotationsResponse listAnnotationQueueItemAnnotations(queueId, id)



List all annotations for a queue item (across all annotators).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        try {
            QueueItemAnnotationsResponse result = apiInstance.listAnnotationQueueItemAnnotations(queueId, id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#listAnnotationQueueItemAnnotations");
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

[**QueueItemAnnotationsResponse**](QueueItemAnnotationsResponse.md)


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

## listAnnotationQueueItemAnnotationsWithHttpInfo

> ApiResponse<QueueItemAnnotationsResponse> listAnnotationQueueItemAnnotations listAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id)



List all annotations for a queue item (across all annotators).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        try {
            ApiResponse<QueueItemAnnotationsResponse> response = apiInstance.listAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#listAnnotationQueueItemAnnotations");
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

ApiResponse<[**QueueItemAnnotationsResponse**](QueueItemAnnotationsResponse.md)>


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


## listAnnotationQueueItems

> ListAnnotationQueueItems200Response listAnnotationQueueItems(queueId, page, limit, status, sourceType, assignedTo, reviewStatus, ordering)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        List<String> status = Arrays.asList(); // List<String> | 
        List<String> sourceType = Arrays.asList(); // List<String> | 
        String assignedTo = "assignedTo_example"; // String | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String ordering = "created_at"; // String | 
        try {
            ListAnnotationQueueItems200Response result = apiInstance.listAnnotationQueueItems(queueId, page, limit, status, sourceType, assignedTo, reviewStatus, ordering);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#listAnnotationQueueItems");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **status** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sourceType** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **assignedTo** | **String**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **ordering** | **String**|  | [optional] [enum: created_at, -created_at] |

### Return type

[**ListAnnotationQueueItems200Response**](ListAnnotationQueueItems200Response.md)


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

## listAnnotationQueueItemsWithHttpInfo

> ApiResponse<ListAnnotationQueueItems200Response> listAnnotationQueueItems listAnnotationQueueItemsWithHttpInfo(queueId, page, limit, status, sourceType, assignedTo, reviewStatus, ordering)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        List<String> status = Arrays.asList(); // List<String> | 
        List<String> sourceType = Arrays.asList(); // List<String> | 
        String assignedTo = "assignedTo_example"; // String | 
        String reviewStatus = "reviewStatus_example"; // String | 
        String ordering = "created_at"; // String | 
        try {
            ApiResponse<ListAnnotationQueueItems200Response> response = apiInstance.listAnnotationQueueItemsWithHttpInfo(queueId, page, limit, status, sourceType, assignedTo, reviewStatus, ordering);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#listAnnotationQueueItems");
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
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **status** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sourceType** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **assignedTo** | **String**|  | [optional] |
| **reviewStatus** | **String**|  | [optional] |
| **ordering** | **String**|  | [optional] [enum: created_at, -created_at] |

### Return type

ApiResponse<[**ListAnnotationQueueItems200Response**](ListAnnotationQueueItems200Response.md)>


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


## releaseAnnotationQueueItem

> QueueReleaseReservationResponse releaseAnnotationQueueItem(queueId, id, body)



Release reservation on an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        Object body = null; // Object | 
        try {
            QueueReleaseReservationResponse result = apiInstance.releaseAnnotationQueueItem(queueId, id, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#releaseAnnotationQueueItem");
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
| **body** | **Object**|  | |

### Return type

[**QueueReleaseReservationResponse**](QueueReleaseReservationResponse.md)


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

## releaseAnnotationQueueItemWithHttpInfo

> ApiResponse<QueueReleaseReservationResponse> releaseAnnotationQueueItem releaseAnnotationQueueItemWithHttpInfo(queueId, id, body)



Release reservation on an item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        Object body = null; // Object | 
        try {
            ApiResponse<QueueReleaseReservationResponse> response = apiInstance.releaseAnnotationQueueItemWithHttpInfo(queueId, id, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#releaseAnnotationQueueItem");
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
| **body** | **Object**|  | |

### Return type

ApiResponse<[**QueueReleaseReservationResponse**](QueueReleaseReservationResponse.md)>


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


## removeAnnotationQueueItems

> QueueBulkRemoveItemsResponse removeAnnotationQueueItems(queueId, bulkRemoveItems)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        BulkRemoveItems bulkRemoveItems = new BulkRemoveItems(); // BulkRemoveItems | 
        try {
            QueueBulkRemoveItemsResponse result = apiInstance.removeAnnotationQueueItems(queueId, bulkRemoveItems);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#removeAnnotationQueueItems");
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
| **bulkRemoveItems** | [**BulkRemoveItems**](BulkRemoveItems.md)|  | |

### Return type

[**QueueBulkRemoveItemsResponse**](QueueBulkRemoveItemsResponse.md)


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

## removeAnnotationQueueItemsWithHttpInfo

> ApiResponse<QueueBulkRemoveItemsResponse> removeAnnotationQueueItems removeAnnotationQueueItemsWithHttpInfo(queueId, bulkRemoveItems)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        BulkRemoveItems bulkRemoveItems = new BulkRemoveItems(); // BulkRemoveItems | 
        try {
            ApiResponse<QueueBulkRemoveItemsResponse> response = apiInstance.removeAnnotationQueueItemsWithHttpInfo(queueId, bulkRemoveItems);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#removeAnnotationQueueItems");
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
| **bulkRemoveItems** | [**BulkRemoveItems**](BulkRemoveItems.md)|  | |

### Return type

ApiResponse<[**QueueBulkRemoveItemsResponse**](QueueBulkRemoveItemsResponse.md)>


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


## skipAnnotationQueueItem

> QueueNavigationResponse skipAnnotationQueueItem(queueId, id, queueItemNavigationRequest)



Mark item as skipped and return next pending item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        QueueItemNavigationRequest queueItemNavigationRequest = new QueueItemNavigationRequest(); // QueueItemNavigationRequest | 
        try {
            QueueNavigationResponse result = apiInstance.skipAnnotationQueueItem(queueId, id, queueItemNavigationRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#skipAnnotationQueueItem");
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
| **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md)|  | |

### Return type

[**QueueNavigationResponse**](QueueNavigationResponse.md)


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

## skipAnnotationQueueItemWithHttpInfo

> ApiResponse<QueueNavigationResponse> skipAnnotationQueueItem skipAnnotationQueueItemWithHttpInfo(queueId, id, queueItemNavigationRequest)



Mark item as skipped and return next pending item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        QueueItemNavigationRequest queueItemNavigationRequest = new QueueItemNavigationRequest(); // QueueItemNavigationRequest | 
        try {
            ApiResponse<QueueNavigationResponse> response = apiInstance.skipAnnotationQueueItemWithHttpInfo(queueId, id, queueItemNavigationRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#skipAnnotationQueueItem");
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
| **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md)|  | |

### Return type

ApiResponse<[**QueueNavigationResponse**](QueueNavigationResponse.md)>


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


## submitAnnotationQueueItemAnnotations

> QueueSubmitAnnotationsResponse submitAnnotationQueueItemAnnotations(queueId, id, submitAnnotations)



Submit or update annotations for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        SubmitAnnotations submitAnnotations = new SubmitAnnotations(); // SubmitAnnotations | 
        try {
            QueueSubmitAnnotationsResponse result = apiInstance.submitAnnotationQueueItemAnnotations(queueId, id, submitAnnotations);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#submitAnnotationQueueItemAnnotations");
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
| **submitAnnotations** | [**SubmitAnnotations**](SubmitAnnotations.md)|  | |

### Return type

[**QueueSubmitAnnotationsResponse**](QueueSubmitAnnotationsResponse.md)


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

## submitAnnotationQueueItemAnnotationsWithHttpInfo

> ApiResponse<QueueSubmitAnnotationsResponse> submitAnnotationQueueItemAnnotations submitAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id, submitAnnotations)



Submit or update annotations for a queue item.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AnnotationQueueItemsApi;

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

        AnnotationQueueItemsApi apiInstance = new AnnotationQueueItemsApi(defaultClient);
        String queueId = "queueId_example"; // String | 
        UUID id = UUID.randomUUID(); // UUID | A UUID string identifying this queue item.
        SubmitAnnotations submitAnnotations = new SubmitAnnotations(); // SubmitAnnotations | 
        try {
            ApiResponse<QueueSubmitAnnotationsResponse> response = apiInstance.submitAnnotationQueueItemAnnotationsWithHttpInfo(queueId, id, submitAnnotations);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AnnotationQueueItemsApi#submitAnnotationQueueItemAnnotations");
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
| **submitAnnotations** | [**SubmitAnnotations**](SubmitAnnotations.md)|  | |

### Return type

ApiResponse<[**QueueSubmitAnnotationsResponse**](QueueSubmitAnnotationsResponse.md)>


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

