# \AnnotationQueueDiscussionAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreateAnnotationQueueItemComment**](AnnotationQueueDiscussionAPI.md#CreateAnnotationQueueItemComment) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ | 
[**ListAnnotationQueueItemDiscussion**](AnnotationQueueDiscussionAPI.md#ListAnnotationQueueItemDiscussion) | **Get** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/ | 
[**ReopenAnnotationQueueItemThread**](AnnotationQueueDiscussionAPI.md#ReopenAnnotationQueueItemThread) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/reopen/ | 
[**ResolveAnnotationQueueItemThread**](AnnotationQueueDiscussionAPI.md#ResolveAnnotationQueueItemThread) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/{thread_id}/resolve/ | 
[**ToggleAnnotationQueueItemCommentReaction**](AnnotationQueueDiscussionAPI.md#ToggleAnnotationQueueItemCommentReaction) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/discussion/comments/{comment_id}/reaction/ | 



## CreateAnnotationQueueItemComment

> QueueDiscussionResponse CreateAnnotationQueueItemComment(ctx, queueId, id).DiscussionCommentRequest(discussionCommentRequest).Execute()





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
	discussionCommentRequest := *openapiclient.NewDiscussionCommentRequest() // DiscussionCommentRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueDiscussionAPI.CreateAnnotationQueueItemComment(context.Background(), queueId, id).DiscussionCommentRequest(discussionCommentRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueDiscussionAPI.CreateAnnotationQueueItemComment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateAnnotationQueueItemComment`: QueueDiscussionResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueDiscussionAPI.CreateAnnotationQueueItemComment`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiCreateAnnotationQueueItemCommentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **discussionCommentRequest** | [**DiscussionCommentRequest**](DiscussionCommentRequest.md) |  | 

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAnnotationQueueItemDiscussion

> QueueDiscussionResponse ListAnnotationQueueItemDiscussion(ctx, queueId, id).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueDiscussionAPI.ListAnnotationQueueItemDiscussion(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueDiscussionAPI.ListAnnotationQueueItemDiscussion``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAnnotationQueueItemDiscussion`: QueueDiscussionResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueDiscussionAPI.ListAnnotationQueueItemDiscussion`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiListAnnotationQueueItemDiscussionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ReopenAnnotationQueueItemThread

> QueueDiscussionResponse ReopenAnnotationQueueItemThread(ctx, queueId, id, threadId).DiscussionThreadStatusRequest(discussionThreadStatusRequest).Execute()





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
	threadId := "threadId_example" // string | 
	discussionThreadStatusRequest := *openapiclient.NewDiscussionThreadStatusRequest() // DiscussionThreadStatusRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueDiscussionAPI.ReopenAnnotationQueueItemThread(context.Background(), queueId, id, threadId).DiscussionThreadStatusRequest(discussionThreadStatusRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueDiscussionAPI.ReopenAnnotationQueueItemThread``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ReopenAnnotationQueueItemThread`: QueueDiscussionResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueDiscussionAPI.ReopenAnnotationQueueItemThread`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 
**threadId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiReopenAnnotationQueueItemThreadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



 **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md) |  | 

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ResolveAnnotationQueueItemThread

> QueueDiscussionResponse ResolveAnnotationQueueItemThread(ctx, queueId, id, threadId).DiscussionThreadStatusRequest(discussionThreadStatusRequest).Execute()





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
	threadId := "threadId_example" // string | 
	discussionThreadStatusRequest := *openapiclient.NewDiscussionThreadStatusRequest() // DiscussionThreadStatusRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueDiscussionAPI.ResolveAnnotationQueueItemThread(context.Background(), queueId, id, threadId).DiscussionThreadStatusRequest(discussionThreadStatusRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueDiscussionAPI.ResolveAnnotationQueueItemThread``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ResolveAnnotationQueueItemThread`: QueueDiscussionResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueDiscussionAPI.ResolveAnnotationQueueItemThread`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 
**threadId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiResolveAnnotationQueueItemThreadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



 **discussionThreadStatusRequest** | [**DiscussionThreadStatusRequest**](DiscussionThreadStatusRequest.md) |  | 

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ToggleAnnotationQueueItemCommentReaction

> QueueDiscussionResponse ToggleAnnotationQueueItemCommentReaction(ctx, queueId, id, commentId).DiscussionReactionRequest(discussionReactionRequest).Execute()





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
	commentId := "commentId_example" // string | 
	discussionReactionRequest := *openapiclient.NewDiscussionReactionRequest() // DiscussionReactionRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueDiscussionAPI.ToggleAnnotationQueueItemCommentReaction(context.Background(), queueId, id, commentId).DiscussionReactionRequest(discussionReactionRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueDiscussionAPI.ToggleAnnotationQueueItemCommentReaction``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ToggleAnnotationQueueItemCommentReaction`: QueueDiscussionResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueDiscussionAPI.ToggleAnnotationQueueItemCommentReaction`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 
**commentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiToggleAnnotationQueueItemCommentReactionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



 **discussionReactionRequest** | [**DiscussionReactionRequest**](DiscussionReactionRequest.md) |  | 

### Return type

[**QueueDiscussionResponse**](QueueDiscussionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

