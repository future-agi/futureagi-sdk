# \AnnotationQueueItemsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**AddAnnotationQueueItems**](AnnotationQueueItemsAPI.md#AddAnnotationQueueItems) | **Post** /model-hub/annotation-queues/{queue_id}/items/add-items/ | 
[**AssignAnnotationQueueItems**](AnnotationQueueItemsAPI.md#AssignAnnotationQueueItems) | **Post** /model-hub/annotation-queues/{queue_id}/items/assign/ | 
[**CompleteAnnotationQueueItem**](AnnotationQueueItemsAPI.md#CompleteAnnotationQueueItem) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/complete/ | 
[**GetAnnotationQueueItemDetail**](AnnotationQueueItemsAPI.md#GetAnnotationQueueItemDetail) | **Get** /model-hub/annotation-queues/{queue_id}/items/{id}/annotate-detail/ | 
[**GetNextAnnotationQueueItem**](AnnotationQueueItemsAPI.md#GetNextAnnotationQueueItem) | **Get** /model-hub/annotation-queues/{queue_id}/items/next-item/ | Get the next or previous item in the queue.
[**ImportAnnotationQueueItemAnnotations**](AnnotationQueueItemsAPI.md#ImportAnnotationQueueItemAnnotations) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/import/ | 
[**ListAnnotationQueueItemAnnotations**](AnnotationQueueItemsAPI.md#ListAnnotationQueueItemAnnotations) | **Get** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/ | 
[**ListAnnotationQueueItems**](AnnotationQueueItemsAPI.md#ListAnnotationQueueItems) | **Get** /model-hub/annotation-queues/{queue_id}/items/ | 
[**ReleaseAnnotationQueueItem**](AnnotationQueueItemsAPI.md#ReleaseAnnotationQueueItem) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/release/ | 
[**RemoveAnnotationQueueItems**](AnnotationQueueItemsAPI.md#RemoveAnnotationQueueItems) | **Post** /model-hub/annotation-queues/{queue_id}/items/bulk-remove/ | 
[**SkipAnnotationQueueItem**](AnnotationQueueItemsAPI.md#SkipAnnotationQueueItem) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/skip/ | 
[**SubmitAnnotationQueueItemAnnotations**](AnnotationQueueItemsAPI.md#SubmitAnnotationQueueItemAnnotations) | **Post** /model-hub/annotation-queues/{queue_id}/items/{id}/annotations/submit/ | 



## AddAnnotationQueueItems

> QueueAddItemsResponse AddAnnotationQueueItems(ctx, queueId).AddItems(addItems).Execute()





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
	addItems := *openapiclient.NewAddItems() // AddItems | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.AddAnnotationQueueItems(context.Background(), queueId).AddItems(addItems).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.AddAnnotationQueueItems``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AddAnnotationQueueItems`: QueueAddItemsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.AddAnnotationQueueItems`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAddAnnotationQueueItemsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **addItems** | [**AddItems**](AddItems.md) |  | 

### Return type

[**QueueAddItemsResponse**](QueueAddItemsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AssignAnnotationQueueItems

> QueueAssignItemsResponse AssignAnnotationQueueItems(ctx, queueId).AssignItems(assignItems).Execute()





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
	assignItems := *openapiclient.NewAssignItems([]string{"ItemIds_example"}) // AssignItems | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.AssignAnnotationQueueItems(context.Background(), queueId).AssignItems(assignItems).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.AssignAnnotationQueueItems``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AssignAnnotationQueueItems`: QueueAssignItemsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.AssignAnnotationQueueItems`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAssignAnnotationQueueItemsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **assignItems** | [**AssignItems**](AssignItems.md) |  | 

### Return type

[**QueueAssignItemsResponse**](QueueAssignItemsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CompleteAnnotationQueueItem

> QueueNavigationResponse CompleteAnnotationQueueItem(ctx, queueId, id).QueueItemNavigationRequest(queueItemNavigationRequest).Execute()





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
	queueItemNavigationRequest := *openapiclient.NewQueueItemNavigationRequest() // QueueItemNavigationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.CompleteAnnotationQueueItem(context.Background(), queueId, id).QueueItemNavigationRequest(queueItemNavigationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.CompleteAnnotationQueueItem``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CompleteAnnotationQueueItem`: QueueNavigationResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.CompleteAnnotationQueueItem`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiCompleteAnnotationQueueItemRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md) |  | 

### Return type

[**QueueNavigationResponse**](QueueNavigationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAnnotationQueueItemDetail

> QueueAnnotateDetailResponse GetAnnotationQueueItemDetail(ctx, queueId, id).AnnotatorId(annotatorId).IncludeCompleted(includeCompleted).ViewMode(viewMode).ReviewStatus(reviewStatus).ExcludeReviewStatus(excludeReviewStatus).IncludeAllAnnotations(includeAllAnnotations).Reserve(reserve).Execute()





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
	annotatorId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	includeCompleted := true // bool |  (optional)
	viewMode := "viewMode_example" // string |  (optional)
	reviewStatus := "reviewStatus_example" // string |  (optional)
	excludeReviewStatus := "excludeReviewStatus_example" // string |  (optional)
	includeAllAnnotations := true // bool |  (optional)
	reserve := true // bool |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.GetAnnotationQueueItemDetail(context.Background(), queueId, id).AnnotatorId(annotatorId).IncludeCompleted(includeCompleted).ViewMode(viewMode).ReviewStatus(reviewStatus).ExcludeReviewStatus(excludeReviewStatus).IncludeAllAnnotations(includeAllAnnotations).Reserve(reserve).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.GetAnnotationQueueItemDetail``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAnnotationQueueItemDetail`: QueueAnnotateDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.GetAnnotationQueueItemDetail`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAnnotationQueueItemDetailRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **annotatorId** | **string** |  | 
 **includeCompleted** | **bool** |  | 
 **viewMode** | **string** |  | 
 **reviewStatus** | **string** |  | 
 **excludeReviewStatus** | **string** |  | 
 **includeAllAnnotations** | **bool** |  | 
 **reserve** | **bool** |  | 

### Return type

[**QueueAnnotateDetailResponse**](QueueAnnotateDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetNextAnnotationQueueItem

> QueueNextItemResponse GetNextAnnotationQueueItem(ctx, queueId).Page(page).Limit(limit).Exclude(exclude).Before(before).ReviewStatus(reviewStatus).ExcludeReviewStatus(excludeReviewStatus).IncludeCompleted(includeCompleted).ViewMode(viewMode).IncludeAllAnnotations(includeAllAnnotations).Execute()

Get the next or previous item in the queue.



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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	exclude := "exclude_example" // string |  (optional)
	before := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	reviewStatus := "reviewStatus_example" // string |  (optional)
	excludeReviewStatus := "excludeReviewStatus_example" // string |  (optional)
	includeCompleted := true // bool |  (optional)
	viewMode := "viewMode_example" // string |  (optional)
	includeAllAnnotations := true // bool |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.GetNextAnnotationQueueItem(context.Background(), queueId).Page(page).Limit(limit).Exclude(exclude).Before(before).ReviewStatus(reviewStatus).ExcludeReviewStatus(excludeReviewStatus).IncludeCompleted(includeCompleted).ViewMode(viewMode).IncludeAllAnnotations(includeAllAnnotations).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.GetNextAnnotationQueueItem``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetNextAnnotationQueueItem`: QueueNextItemResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.GetNextAnnotationQueueItem`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetNextAnnotationQueueItemRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **exclude** | **string** |  | 
 **before** | **string** |  | 
 **reviewStatus** | **string** |  | 
 **excludeReviewStatus** | **string** |  | 
 **includeCompleted** | **bool** |  | 
 **viewMode** | **string** |  | 
 **includeAllAnnotations** | **bool** |  | 

### Return type

[**QueueNextItemResponse**](QueueNextItemResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ImportAnnotationQueueItemAnnotations

> QueueImportAnnotationsResponse ImportAnnotationQueueItemAnnotations(ctx, queueId, id).ImportAnnotations(importAnnotations).Execute()





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
	importAnnotations := *openapiclient.NewImportAnnotations([]openapiclient.ImportAnnotationEntry{*openapiclient.NewImportAnnotationEntry("LabelId_example", map[string]interface{}{"key": interface{}(123)})}) // ImportAnnotations | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.ImportAnnotationQueueItemAnnotations(context.Background(), queueId, id).ImportAnnotations(importAnnotations).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.ImportAnnotationQueueItemAnnotations``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ImportAnnotationQueueItemAnnotations`: QueueImportAnnotationsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.ImportAnnotationQueueItemAnnotations`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiImportAnnotationQueueItemAnnotationsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **importAnnotations** | [**ImportAnnotations**](ImportAnnotations.md) |  | 

### Return type

[**QueueImportAnnotationsResponse**](QueueImportAnnotationsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAnnotationQueueItemAnnotations

> QueueItemAnnotationsResponse ListAnnotationQueueItemAnnotations(ctx, queueId, id).Execute()





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
	resp, r, err := apiClient.AnnotationQueueItemsAPI.ListAnnotationQueueItemAnnotations(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.ListAnnotationQueueItemAnnotations``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAnnotationQueueItemAnnotations`: QueueItemAnnotationsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.ListAnnotationQueueItemAnnotations`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiListAnnotationQueueItemAnnotationsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**QueueItemAnnotationsResponse**](QueueItemAnnotationsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAnnotationQueueItems

> ListAnnotationQueueItems200Response ListAnnotationQueueItems(ctx, queueId).Page(page).Limit(limit).Status(status).SourceType(sourceType).AssignedTo(assignedTo).ReviewStatus(reviewStatus).Ordering(ordering).Execute()





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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	status := []string{"Inner_example"} // []string |  (optional)
	sourceType := []string{"Inner_example"} // []string |  (optional)
	assignedTo := "assignedTo_example" // string |  (optional)
	reviewStatus := "reviewStatus_example" // string |  (optional)
	ordering := "ordering_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.ListAnnotationQueueItems(context.Background(), queueId).Page(page).Limit(limit).Status(status).SourceType(sourceType).AssignedTo(assignedTo).ReviewStatus(reviewStatus).Ordering(ordering).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.ListAnnotationQueueItems``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAnnotationQueueItems`: ListAnnotationQueueItems200Response
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.ListAnnotationQueueItems`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListAnnotationQueueItemsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **status** | **[]string** |  | 
 **sourceType** | **[]string** |  | 
 **assignedTo** | **string** |  | 
 **reviewStatus** | **string** |  | 
 **ordering** | **string** |  | 

### Return type

[**ListAnnotationQueueItems200Response**](ListAnnotationQueueItems200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ReleaseAnnotationQueueItem

> QueueReleaseReservationResponse ReleaseAnnotationQueueItem(ctx, queueId, id).Body(body).Execute()





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
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.ReleaseAnnotationQueueItem(context.Background(), queueId, id).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.ReleaseAnnotationQueueItem``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ReleaseAnnotationQueueItem`: QueueReleaseReservationResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.ReleaseAnnotationQueueItem`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiReleaseAnnotationQueueItemRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**QueueReleaseReservationResponse**](QueueReleaseReservationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## RemoveAnnotationQueueItems

> QueueBulkRemoveItemsResponse RemoveAnnotationQueueItems(ctx, queueId).BulkRemoveItems(bulkRemoveItems).Execute()





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
	bulkRemoveItems := *openapiclient.NewBulkRemoveItems([]string{"ItemIds_example"}) // BulkRemoveItems | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.RemoveAnnotationQueueItems(context.Background(), queueId).BulkRemoveItems(bulkRemoveItems).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.RemoveAnnotationQueueItems``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `RemoveAnnotationQueueItems`: QueueBulkRemoveItemsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.RemoveAnnotationQueueItems`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiRemoveAnnotationQueueItemsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **bulkRemoveItems** | [**BulkRemoveItems**](BulkRemoveItems.md) |  | 

### Return type

[**QueueBulkRemoveItemsResponse**](QueueBulkRemoveItemsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SkipAnnotationQueueItem

> QueueNavigationResponse SkipAnnotationQueueItem(ctx, queueId, id).QueueItemNavigationRequest(queueItemNavigationRequest).Execute()





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
	queueItemNavigationRequest := *openapiclient.NewQueueItemNavigationRequest() // QueueItemNavigationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.SkipAnnotationQueueItem(context.Background(), queueId, id).QueueItemNavigationRequest(queueItemNavigationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.SkipAnnotationQueueItem``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SkipAnnotationQueueItem`: QueueNavigationResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.SkipAnnotationQueueItem`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiSkipAnnotationQueueItemRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **queueItemNavigationRequest** | [**QueueItemNavigationRequest**](QueueItemNavigationRequest.md) |  | 

### Return type

[**QueueNavigationResponse**](QueueNavigationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SubmitAnnotationQueueItemAnnotations

> QueueSubmitAnnotationsResponse SubmitAnnotationQueueItemAnnotations(ctx, queueId, id).SubmitAnnotations(submitAnnotations).Execute()





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
	submitAnnotations := *openapiclient.NewSubmitAnnotations([]openapiclient.SubmitAnnotationEntry{*openapiclient.NewSubmitAnnotationEntry("LabelId_example", map[string]interface{}{"key": interface{}(123)})}) // SubmitAnnotations | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueueItemsAPI.SubmitAnnotationQueueItemAnnotations(context.Background(), queueId, id).SubmitAnnotations(submitAnnotations).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueueItemsAPI.SubmitAnnotationQueueItemAnnotations``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SubmitAnnotationQueueItemAnnotations`: QueueSubmitAnnotationsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueueItemsAPI.SubmitAnnotationQueueItemAnnotations`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiSubmitAnnotationQueueItemAnnotationsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **submitAnnotations** | [**SubmitAnnotations**](SubmitAnnotations.md) |  | 

### Return type

[**QueueSubmitAnnotationsResponse**](QueueSubmitAnnotationsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

