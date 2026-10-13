# \TracingAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreateBulkTraceAnnotation**](TracingAPI.md#CreateBulkTraceAnnotation) | **Post** /tracer/bulk-annotation/ | 
[**GetErrorFeedIssue**](TracingAPI.md#GetErrorFeedIssue) | **Get** /tracer/feed/issues/{cluster_id}/ | 
[**GetErrorFeedIssueStats**](TracingAPI.md#GetErrorFeedIssueStats) | **Get** /tracer/feed/issues/stats/ | 
[**GetTrace**](TracingAPI.md#GetTrace) | **Get** /tracer/trace/{id}/ | 
[**GetTraceGraphMethods**](TracingAPI.md#GetTraceGraphMethods) | **Post** /tracer/trace/get_graph_methods/ | 
[**GetTraceSession**](TracingAPI.md#GetTraceSession) | **Get** /tracer/trace-session/{id}/ | 
[**GetTraceSessionGraphData**](TracingAPI.md#GetTraceSessionGraphData) | **Post** /tracer/trace-session/get_session_graph_data/ | Fetch time-series session metrics for the observe graph.
[**GetVoiceCallDetail**](TracingAPI.md#GetVoiceCallDetail) | **Get** /tracer/trace/voice_call_detail/ | Return the heavy / detail-only fields for a single voice call.
[**ListErrorFeedIssues**](TracingAPI.md#ListErrorFeedIssues) | **Get** /tracer/feed/issues/ | 
[**ListTraceAnnotationLabels**](TracingAPI.md#ListTraceAnnotationLabels) | **Get** /tracer/get-annotation-labels/ | 
[**ListTraceProjects**](TracingAPI.md#ListTraceProjects) | **Get** /tracer/project/list_projects/ | List projects filtered by organization ID.
[**ListTraceProperties**](TracingAPI.md#ListTraceProperties) | **Get** /tracer/trace/get_properties/ | 
[**ListTraceSessions**](TracingAPI.md#ListTraceSessions) | **Get** /tracer/trace-session/list_sessions/ | 
[**ListTraceUsers**](TracingAPI.md#ListTraceUsers) | **Get** /tracer/users/ | 
[**ListTraces**](TracingAPI.md#ListTraces) | **Get** /tracer/trace/list_traces/ | 
[**ListVoiceCalls**](TracingAPI.md#ListVoiceCalls) | **Get** /tracer/trace/list_voice_calls/ | 
[**UpdateTraceTags**](TracingAPI.md#UpdateTraceTags) | **Patch** /tracer/trace/{id}/tags/ | 



## CreateBulkTraceAnnotation

> BulkAnnotationResponse CreateBulkTraceAnnotation(ctx).BulkAnnotationRequest(bulkAnnotationRequest).Execute()





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
	bulkAnnotationRequest := *openapiclient.NewBulkAnnotationRequest([]openapiclient.BulkAnnotationRecordRequest{*openapiclient.NewBulkAnnotationRecordRequest("ObservationSpanId_example")}) // BulkAnnotationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.CreateBulkTraceAnnotation(context.Background()).BulkAnnotationRequest(bulkAnnotationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.CreateBulkTraceAnnotation``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateBulkTraceAnnotation`: BulkAnnotationResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.CreateBulkTraceAnnotation`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateBulkTraceAnnotationRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bulkAnnotationRequest** | [**BulkAnnotationRequest**](BulkAnnotationRequest.md) |  | 

### Return type

[**BulkAnnotationResponse**](BulkAnnotationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetErrorFeedIssue

> FeedDetailApiResponse GetErrorFeedIssue(ctx, clusterId).ProjectId(projectId).Execute()





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
	clusterId := "clusterId_example" // string | 
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetErrorFeedIssue(context.Background(), clusterId).ProjectId(projectId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetErrorFeedIssue``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetErrorFeedIssue`: FeedDetailApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetErrorFeedIssue`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetErrorFeedIssueRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **projectId** | **string** |  | 

### Return type

[**FeedDetailApiResponse**](FeedDetailApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetErrorFeedIssueStats

> FeedStatsApiResponse GetErrorFeedIssueStats(ctx).ProjectId(projectId).TimeRangeDays(timeRangeDays).Execute()





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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	timeRangeDays := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetErrorFeedIssueStats(context.Background()).ProjectId(projectId).TimeRangeDays(timeRangeDays).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetErrorFeedIssueStats``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetErrorFeedIssueStats`: FeedStatsApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetErrorFeedIssueStats`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiGetErrorFeedIssueStatsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectId** | **string** |  | 
 **timeRangeDays** | **int32** |  | 

### Return type

[**FeedStatsApiResponse**](FeedStatsApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTrace

> Trace GetTrace(ctx, id).Execute()





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
	id := "id_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetTrace(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetTrace``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTrace`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetTrace`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTraceRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTraceGraphMethods

> ObserveGraphDataResponse GetTraceGraphMethods(ctx).ObserveGraphDataRequest(observeGraphDataRequest).Execute()





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
	observeGraphDataRequest := *openapiclient.NewObserveGraphDataRequest("ProjectId_example", *openapiclient.NewReqDataConfig("Id_example", "Type_example")) // ObserveGraphDataRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetTraceGraphMethods(context.Background()).ObserveGraphDataRequest(observeGraphDataRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetTraceGraphMethods``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTraceGraphMethods`: ObserveGraphDataResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetTraceGraphMethods`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiGetTraceGraphMethodsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **observeGraphDataRequest** | [**ObserveGraphDataRequest**](ObserveGraphDataRequest.md) |  | 

### Return type

[**ObserveGraphDataResponse**](ObserveGraphDataResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTraceSession

> TraceSession GetTraceSession(ctx, id).Execute()





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
	id := "id_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetTraceSession(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetTraceSession``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTraceSession`: TraceSession
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetTraceSession`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTraceSessionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**TraceSession**](TraceSession.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTraceSessionGraphData

> TraceSessionGraphDataRequest GetTraceSessionGraphData(ctx).TraceSessionGraphDataRequest(traceSessionGraphDataRequest).Execute()

Fetch time-series session metrics for the observe graph.



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
	traceSessionGraphDataRequest := *openapiclient.NewTraceSessionGraphDataRequest("ProjectId_example", *openapiclient.NewReqDataConfig("Id_example", "Type_example")) // TraceSessionGraphDataRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetTraceSessionGraphData(context.Background()).TraceSessionGraphDataRequest(traceSessionGraphDataRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetTraceSessionGraphData``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTraceSessionGraphData`: TraceSessionGraphDataRequest
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetTraceSessionGraphData`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiGetTraceSessionGraphDataRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **traceSessionGraphDataRequest** | [**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md) |  | 

### Return type

[**TraceSessionGraphDataRequest**](TraceSessionGraphDataRequest.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetVoiceCallDetail

> TracerTraceList200Response GetVoiceCallDetail(ctx).Page(page).Limit(limit).Execute()

Return the heavy / detail-only fields for a single voice call.



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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.GetVoiceCallDetail(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.GetVoiceCallDetail``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetVoiceCallDetail`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.GetVoiceCallDetail`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiGetVoiceCallDetailRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListErrorFeedIssues

> FeedListApiResponse ListErrorFeedIssues(ctx).ProjectId(projectId).Search(search).Status(status).FixLayer(fixLayer).Source(source).IssueGroup(issueGroup).TimeRangeDays(timeRangeDays).SortBy(sortBy).SortDir(sortDir).Limit(limit).Offset(offset).Execute()





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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	search := "search_example" // string |  (optional)
	status := "status_example" // string |  (optional)
	fixLayer := "fixLayer_example" // string |  (optional)
	source := "source_example" // string |  (optional)
	issueGroup := "issueGroup_example" // string |  (optional)
	timeRangeDays := int32(56) // int32 |  (optional)
	sortBy := "sortBy_example" // string |  (optional) (default to "last_seen")
	sortDir := "sortDir_example" // string |  (optional) (default to "desc")
	limit := int32(56) // int32 |  (optional) (default to 25)
	offset := int32(56) // int32 |  (optional) (default to 0)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListErrorFeedIssues(context.Background()).ProjectId(projectId).Search(search).Status(status).FixLayer(fixLayer).Source(source).IssueGroup(issueGroup).TimeRangeDays(timeRangeDays).SortBy(sortBy).SortDir(sortDir).Limit(limit).Offset(offset).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListErrorFeedIssues``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListErrorFeedIssues`: FeedListApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListErrorFeedIssues`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListErrorFeedIssuesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectId** | **string** |  | 
 **search** | **string** |  | 
 **status** | **string** |  | 
 **fixLayer** | **string** |  | 
 **source** | **string** |  | 
 **issueGroup** | **string** |  | 
 **timeRangeDays** | **int32** |  | 
 **sortBy** | **string** |  | [default to &quot;last_seen&quot;]
 **sortDir** | **string** |  | [default to &quot;desc&quot;]
 **limit** | **int32** |  | [default to 25]
 **offset** | **int32** |  | [default to 0]

### Return type

[**FeedListApiResponse**](FeedListApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraceAnnotationLabels

> GetAnnotationLabelsResponse ListTraceAnnotationLabels(ctx).ProjectId(projectId).Execute()





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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraceAnnotationLabels(context.Background()).ProjectId(projectId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraceAnnotationLabels``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraceAnnotationLabels`: GetAnnotationLabelsResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraceAnnotationLabels`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTraceAnnotationLabelsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectId** | **string** |  | 

### Return type

[**GetAnnotationLabelsResponse**](GetAnnotationLabelsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraceProjects

> ListTraceProjects200Response ListTraceProjects(ctx).Page(page).Limit(limit).Execute()

List projects filtered by organization ID.



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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraceProjects(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraceProjects``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraceProjects`: ListTraceProjects200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraceProjects`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTraceProjectsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListTraceProjects200Response**](ListTraceProjects200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraceProperties

> TracerTraceList200Response ListTraceProperties(ctx).Page(page).Limit(limit).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraceProperties(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraceProperties``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraceProperties`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraceProperties`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTracePropertiesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraceSessions

> TracerTraceSessionList200Response ListTraceSessions(ctx).Page(page).Limit(limit).ProjectId(projectId).UserId(userId).Bookmarked(bookmarked).Filters(filters).SortParams(sortParams).PageNumber(pageNumber).PageSize(pageSize).Interval(interval).Execute()





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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	userId := "userId_example" // string |  (optional)
	bookmarked := true // bool |  (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")
	sortParams := "sortParams_example" // string |  (optional) (default to "[]")
	pageNumber := int32(56) // int32 |  (optional) (default to 0)
	pageSize := int32(56) // int32 |  (optional) (default to 30)
	interval := "interval_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraceSessions(context.Background()).Page(page).Limit(limit).ProjectId(projectId).UserId(userId).Bookmarked(bookmarked).Filters(filters).SortParams(sortParams).PageNumber(pageNumber).PageSize(pageSize).Interval(interval).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraceSessions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraceSessions`: TracerTraceSessionList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraceSessions`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTraceSessionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **projectId** | **string** |  | 
 **userId** | **string** |  | 
 **bookmarked** | **bool** |  | 
 **filters** | **string** |  | [default to &quot;[]&quot;]
 **sortParams** | **string** |  | [default to &quot;[]&quot;]
 **pageNumber** | **int32** |  | [default to 0]
 **pageSize** | **int32** |  | [default to 30]
 **interval** | **string** |  | 

### Return type

[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraceUsers

> UsersResponse ListTraceUsers(ctx).ProjectId(projectId).Search(search).PageSize(pageSize).CurrentPageIndex(currentPageIndex).SortParams(sortParams).Filters(filters).Execute()





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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	search := "search_example" // string |  (optional)
	pageSize := int32(56) // int32 |  (optional)
	currentPageIndex := int32(56) // int32 |  (optional)
	sortParams := "sortParams_example" // string |  (optional) (default to "[]")
	filters := "filters_example" // string |  (optional) (default to "[]")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraceUsers(context.Background()).ProjectId(projectId).Search(search).PageSize(pageSize).CurrentPageIndex(currentPageIndex).SortParams(sortParams).Filters(filters).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraceUsers``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraceUsers`: UsersResponse
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraceUsers`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTraceUsersRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectId** | **string** |  | 
 **search** | **string** |  | 
 **pageSize** | **int32** |  | 
 **currentPageIndex** | **int32** |  | 
 **sortParams** | **string** |  | [default to &quot;[]&quot;]
 **filters** | **string** |  | [default to &quot;[]&quot;]

### Return type

[**UsersResponse**](UsersResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTraces

> TracerTraceList200Response ListTraces(ctx).ProjectVersionId(projectVersionId).Page(page).Limit(limit).TraceIds(traceIds).Filters(filters).SortParams(sortParams).PageNumber(pageNumber).PageSize(pageSize).Execute()





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
	projectVersionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	traceIds := "traceIds_example" // string |  (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")
	sortParams := "sortParams_example" // string |  (optional) (default to "[]")
	pageNumber := int32(56) // int32 |  (optional) (default to 0)
	pageSize := int32(56) // int32 |  (optional) (default to 30)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListTraces(context.Background()).ProjectVersionId(projectVersionId).Page(page).Limit(limit).TraceIds(traceIds).Filters(filters).SortParams(sortParams).PageNumber(pageNumber).PageSize(pageSize).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListTraces``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTraces`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListTraces`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListTracesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectVersionId** | **string** |  | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **traceIds** | **string** |  | 
 **filters** | **string** |  | [default to &quot;[]&quot;]
 **sortParams** | **string** |  | [default to &quot;[]&quot;]
 **pageNumber** | **int32** |  | [default to 0]
 **pageSize** | **int32** |  | [default to 30]

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListVoiceCalls

> TracerTraceList200Response ListVoiceCalls(ctx).Page(page).Limit(limit).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.ListVoiceCalls(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.ListVoiceCalls``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListVoiceCalls`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.ListVoiceCalls`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListVoiceCallsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateTraceTags

> TraceTagsUpdate UpdateTraceTags(ctx, id).TraceTagsUpdate(traceTagsUpdate).Execute()





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
	id := "id_example" // string | 
	traceTagsUpdate := *openapiclient.NewTraceTagsUpdate([]string{"Tags_example"}) // TraceTagsUpdate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracingAPI.UpdateTraceTags(context.Background(), id).TraceTagsUpdate(traceTagsUpdate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracingAPI.UpdateTraceTags``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateTraceTags`: TraceTagsUpdate
	fmt.Fprintf(os.Stdout, "Response from `TracingAPI.UpdateTraceTags`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateTraceTagsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **traceTagsUpdate** | [**TraceTagsUpdate**](TraceTagsUpdate.md) |  | 

### Return type

[**TraceTagsUpdate**](TraceTagsUpdate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

