# \AnnotationQueuesAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**AddAnnotationQueueLabel**](AnnotationQueuesAPI.md#AddAnnotationQueueLabel) | **Post** /model-hub/annotation-queues/{id}/add-label/ | 
[**ArchiveAnnotationQueue**](AnnotationQueuesAPI.md#ArchiveAnnotationQueue) | **Delete** /model-hub/annotation-queues/{id}/ | Archive a queue (soft delete).
[**CreateAnnotationQueue**](AnnotationQueuesAPI.md#CreateAnnotationQueue) | **Post** /model-hub/annotation-queues/ | 
[**ExportAnnotationQueue**](AnnotationQueuesAPI.md#ExportAnnotationQueue) | **Get** /model-hub/annotation-queues/{id}/export/ | 
[**ExportAnnotationQueueToDataset**](AnnotationQueuesAPI.md#ExportAnnotationQueueToDataset) | **Post** /model-hub/annotation-queues/{id}/export-to-dataset/ | 
[**GetAnnotationQueue**](AnnotationQueuesAPI.md#GetAnnotationQueue) | **Get** /model-hub/annotation-queues/{id}/ | 
[**GetAnnotationQueueAgreement**](AnnotationQueuesAPI.md#GetAnnotationQueueAgreement) | **Get** /model-hub/annotation-queues/{id}/agreement/ | 
[**GetAnnotationQueueAnalytics**](AnnotationQueuesAPI.md#GetAnnotationQueueAnalytics) | **Get** /model-hub/annotation-queues/{id}/analytics/ | 
[**GetAnnotationQueueProgress**](AnnotationQueuesAPI.md#GetAnnotationQueueProgress) | **Get** /model-hub/annotation-queues/{id}/progress/ | 
[**ListAnnotationQueueExportFields**](AnnotationQueuesAPI.md#ListAnnotationQueueExportFields) | **Get** /model-hub/annotation-queues/{id}/export-fields/ | 
[**ListAnnotationQueues**](AnnotationQueuesAPI.md#ListAnnotationQueues) | **Get** /model-hub/annotation-queues/ | 
[**RemoveAnnotationQueueLabel**](AnnotationQueuesAPI.md#RemoveAnnotationQueueLabel) | **Post** /model-hub/annotation-queues/{id}/remove-label/ | 
[**UpdateAnnotationQueue**](AnnotationQueuesAPI.md#UpdateAnnotationQueue) | **Patch** /model-hub/annotation-queues/{id}/ | 
[**UpdateAnnotationQueueStatus**](AnnotationQueuesAPI.md#UpdateAnnotationQueueStatus) | **Post** /model-hub/annotation-queues/{id}/update-status/ | 



## AddAnnotationQueueLabel

> QueueAddLabelResponse AddAnnotationQueueLabel(ctx, id).QueueLabelRequest(queueLabelRequest).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	queueLabelRequest := *openapiclient.NewQueueLabelRequest("LabelId_example") // QueueLabelRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.AddAnnotationQueueLabel(context.Background(), id).QueueLabelRequest(queueLabelRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.AddAnnotationQueueLabel``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AddAnnotationQueueLabel`: QueueAddLabelResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.AddAnnotationQueueLabel`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiAddAnnotationQueueLabelRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueLabelRequest** | [**QueueLabelRequest**](QueueLabelRequest.md) |  | 

### Return type

[**QueueAddLabelResponse**](QueueAddLabelResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ArchiveAnnotationQueue

> ArchiveAnnotationQueue(ctx, id).Execute()

Archive a queue (soft delete).



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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.AnnotationQueuesAPI.ArchiveAnnotationQueue(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.ArchiveAnnotationQueue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiArchiveAnnotationQueueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

 (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CreateAnnotationQueue

> AnnotationQueue CreateAnnotationQueue(ctx).AnnotationQueue(annotationQueue).Execute()





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
	annotationQueue := *openapiclient.NewAnnotationQueue("Name_example") // AnnotationQueue | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.CreateAnnotationQueue(context.Background()).AnnotationQueue(annotationQueue).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.CreateAnnotationQueue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateAnnotationQueue`: AnnotationQueue
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.CreateAnnotationQueue`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateAnnotationQueueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **annotationQueue** | [**AnnotationQueue**](AnnotationQueue.md) |  | 

### Return type

[**AnnotationQueue**](AnnotationQueue.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ExportAnnotationQueue

> QueueExportAnnotationsResponse ExportAnnotationQueue(ctx, id).ExportFormat(exportFormat).Status(status).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	exportFormat := "exportFormat_example" // string |  (optional)
	status := "status_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.ExportAnnotationQueue(context.Background(), id).ExportFormat(exportFormat).Status(status).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.ExportAnnotationQueue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ExportAnnotationQueue`: QueueExportAnnotationsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.ExportAnnotationQueue`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiExportAnnotationQueueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **exportFormat** | **string** |  | 
 **status** | **string** |  | 

### Return type

[**QueueExportAnnotationsResponse**](QueueExportAnnotationsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ExportAnnotationQueueToDataset

> QueueExportToDatasetResponse ExportAnnotationQueueToDataset(ctx, id).QueueExportToDatasetRequest(queueExportToDatasetRequest).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	queueExportToDatasetRequest := *openapiclient.NewQueueExportToDatasetRequest() // QueueExportToDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.ExportAnnotationQueueToDataset(context.Background(), id).QueueExportToDatasetRequest(queueExportToDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.ExportAnnotationQueueToDataset``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ExportAnnotationQueueToDataset`: QueueExportToDatasetResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.ExportAnnotationQueueToDataset`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiExportAnnotationQueueToDatasetRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueExportToDatasetRequest** | [**QueueExportToDatasetRequest**](QueueExportToDatasetRequest.md) |  | 

### Return type

[**QueueExportToDatasetResponse**](QueueExportToDatasetResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAnnotationQueue

> AnnotationQueue GetAnnotationQueue(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.GetAnnotationQueue(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.GetAnnotationQueue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAnnotationQueue`: AnnotationQueue
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.GetAnnotationQueue`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAnnotationQueueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**AnnotationQueue**](AnnotationQueue.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAnnotationQueueAgreement

> QueueAgreementResponse GetAnnotationQueueAgreement(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.GetAnnotationQueueAgreement(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.GetAnnotationQueueAgreement``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAnnotationQueueAgreement`: QueueAgreementResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.GetAnnotationQueueAgreement`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAnnotationQueueAgreementRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**QueueAgreementResponse**](QueueAgreementResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAnnotationQueueAnalytics

> QueueAnalyticsResponse GetAnnotationQueueAnalytics(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.GetAnnotationQueueAnalytics(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.GetAnnotationQueueAnalytics``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAnnotationQueueAnalytics`: QueueAnalyticsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.GetAnnotationQueueAnalytics`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAnnotationQueueAnalyticsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**QueueAnalyticsResponse**](QueueAnalyticsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAnnotationQueueProgress

> QueueProgressResponse GetAnnotationQueueProgress(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.GetAnnotationQueueProgress(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.GetAnnotationQueueProgress``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAnnotationQueueProgress`: QueueProgressResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.GetAnnotationQueueProgress`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAnnotationQueueProgressRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**QueueProgressResponse**](QueueProgressResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAnnotationQueueExportFields

> QueueExportFieldsResponse ListAnnotationQueueExportFields(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.ListAnnotationQueueExportFields(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.ListAnnotationQueueExportFields``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAnnotationQueueExportFields`: QueueExportFieldsResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.ListAnnotationQueueExportFields`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiListAnnotationQueueExportFieldsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**QueueExportFieldsResponse**](QueueExportFieldsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAnnotationQueues

> ListAnnotationQueues200Response ListAnnotationQueues(ctx).Page(page).Limit(limit).Status(status).Search(search).IncludeCounts(includeCounts).Execute()





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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	status := "status_example" // string |  (optional)
	search := "search_example" // string |  (optional)
	includeCounts := true // bool |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.ListAnnotationQueues(context.Background()).Page(page).Limit(limit).Status(status).Search(search).IncludeCounts(includeCounts).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.ListAnnotationQueues``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAnnotationQueues`: ListAnnotationQueues200Response
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.ListAnnotationQueues`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAnnotationQueuesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **status** | **string** |  | 
 **search** | **string** |  | 
 **includeCounts** | **bool** |  | 

### Return type

[**ListAnnotationQueues200Response**](ListAnnotationQueues200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## RemoveAnnotationQueueLabel

> QueueRemoveLabelResponse RemoveAnnotationQueueLabel(ctx, id).QueueLabelRequest(queueLabelRequest).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	queueLabelRequest := *openapiclient.NewQueueLabelRequest("LabelId_example") // QueueLabelRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.RemoveAnnotationQueueLabel(context.Background(), id).QueueLabelRequest(queueLabelRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.RemoveAnnotationQueueLabel``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `RemoveAnnotationQueueLabel`: QueueRemoveLabelResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.RemoveAnnotationQueueLabel`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiRemoveAnnotationQueueLabelRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueLabelRequest** | [**QueueLabelRequest**](QueueLabelRequest.md) |  | 

### Return type

[**QueueRemoveLabelResponse**](QueueRemoveLabelResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateAnnotationQueue

> AnnotationQueue UpdateAnnotationQueue(ctx, id).AnnotationQueue(annotationQueue).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	annotationQueue := *openapiclient.NewAnnotationQueue("Name_example") // AnnotationQueue | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.UpdateAnnotationQueue(context.Background(), id).AnnotationQueue(annotationQueue).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.UpdateAnnotationQueue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateAnnotationQueue`: AnnotationQueue
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.UpdateAnnotationQueue`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateAnnotationQueueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **annotationQueue** | [**AnnotationQueue**](AnnotationQueue.md) |  | 

### Return type

[**AnnotationQueue**](AnnotationQueue.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateAnnotationQueueStatus

> QueueStatusResponse UpdateAnnotationQueueStatus(ctx, id).QueueStatusRequest(queueStatusRequest).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	queueStatusRequest := *openapiclient.NewQueueStatusRequest("Status_example") // QueueStatusRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AnnotationQueuesAPI.UpdateAnnotationQueueStatus(context.Background(), id).QueueStatusRequest(queueStatusRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AnnotationQueuesAPI.UpdateAnnotationQueueStatus``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateAnnotationQueueStatus`: QueueStatusResponse
	fmt.Fprintf(os.Stdout, "Response from `AnnotationQueuesAPI.UpdateAnnotationQueueStatus`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateAnnotationQueueStatusRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueStatusRequest** | [**QueueStatusRequest**](QueueStatusRequest.md) |  | 

### Return type

[**QueueStatusResponse**](QueueStatusResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

