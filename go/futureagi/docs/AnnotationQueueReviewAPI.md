# \AnnotationQueueReviewAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ReviewAnnotationQueueItem**](AnnotationQueueReviewAPI.md#ReviewAnnotationQueueItem) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/review/ | 



## ReviewAnnotationQueueItem

> QueueReviewItemResponse ReviewAnnotationQueueItem(ctx, queueId, id).ReviewItemRequest(reviewItemRequest).Execute()





### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
	openapiclient "github.com/future-agi/futureagi-sdk/go/futureagi"
)

func main() {
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this queue item.
	reviewItemRequest := *openapiclient.NewReviewItemRequest("Action_example") // ReviewItemRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueReviewAPI.ReviewAnnotationQueueItem(context.Background(), queueId, id).ReviewItemRequest(reviewItemRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueReviewAPI.ReviewAnnotationQueueItem``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ReviewAnnotationQueueItem`: QueueReviewItemResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueReviewAPI.ReviewAnnotationQueueItem`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiReviewAnnotationQueueItemRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **reviewItemRequest** | [**ReviewItemRequest**](ReviewItemRequest.md) |  | 

### Return type

[**QueueReviewItemResponse**](QueueReviewItemResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

