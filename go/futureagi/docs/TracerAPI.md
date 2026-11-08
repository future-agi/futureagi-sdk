# \TracerAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**TracerFeedIssuesCreateLinearIssueCreate**](TracerAPI.md#TracerFeedIssuesCreateLinearIssueCreate) | **Post** /tracer/feed/issues/{cluster_id}/create-linear-issue/ | 
[**TracerFeedIssuesDeepAnalysisCreate**](TracerAPI.md#TracerFeedIssuesDeepAnalysisCreate) | **Post** /tracer/feed/issues/{cluster_id}/deep-analysis/ | 
[**TracerFeedIssuesOverviewList**](TracerAPI.md#TracerFeedIssuesOverviewList) | **Get** /tracer/feed/issues/{cluster_id}/overview/ | 
[**TracerFeedIssuesPartialUpdate**](TracerAPI.md#TracerFeedIssuesPartialUpdate) | **Patch** /tracer/feed/issues/{cluster_id}/ | 
[**TracerFeedIssuesRootCauseList**](TracerAPI.md#TracerFeedIssuesRootCauseList) | **Get** /tracer/feed/issues/{cluster_id}/root-cause/ | GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id&#x3D;X
[**TracerFeedIssuesSidebarList**](TracerAPI.md#TracerFeedIssuesSidebarList) | **Get** /tracer/feed/issues/{cluster_id}/sidebar/ | GET /tracer/feed/issues/{cluster_id}/sidebar/
[**TracerFeedIssuesTracesList**](TracerAPI.md#TracerFeedIssuesTracesList) | **Get** /tracer/feed/issues/{cluster_id}/traces/ | 
[**TracerFeedIssuesTrendsList**](TracerAPI.md#TracerFeedIssuesTrendsList) | **Get** /tracer/feed/issues/{cluster_id}/trends/ | 
[**TracerTraceAgentGraph**](TracerAPI.md#TracerTraceAgentGraph) | **Get** /tracer/trace/agent_graph/ | Return the aggregate agent graph for a project.
[**TracerTraceAnnotationCreate**](TracerAPI.md#TracerTraceAnnotationCreate) | **Post** /tracer/trace-annotation/ | 
[**TracerTraceAnnotationDelete**](TracerAPI.md#TracerTraceAnnotationDelete) | **Delete** /tracer/trace-annotation/{id}/ | 
[**TracerTraceAnnotationGetAnnotationValues**](TracerAPI.md#TracerTraceAnnotationGetAnnotationValues) | **Get** /tracer/trace-annotation/get_annotation_values/ | 
[**TracerTraceAnnotationList**](TracerAPI.md#TracerTraceAnnotationList) | **Get** /tracer/trace-annotation/ | 
[**TracerTraceAnnotationPartialUpdate**](TracerAPI.md#TracerTraceAnnotationPartialUpdate) | **Patch** /tracer/trace-annotation/{id}/ | 
[**TracerTraceAnnotationRead**](TracerAPI.md#TracerTraceAnnotationRead) | **Get** /tracer/trace-annotation/{id}/ | 
[**TracerTraceAnnotationUpdate**](TracerAPI.md#TracerTraceAnnotationUpdate) | **Put** /tracer/trace-annotation/{id}/ | 
[**TracerTraceBulkCreate**](TracerAPI.md#TracerTraceBulkCreate) | **Post** /tracer/trace/bulk_create/ | 
[**TracerTraceCompareTraces**](TracerAPI.md#TracerTraceCompareTraces) | **Post** /tracer/trace/compare_traces/ | 
[**TracerTraceCreate**](TracerAPI.md#TracerTraceCreate) | **Post** /tracer/trace/ | 
[**TracerTraceDelete**](TracerAPI.md#TracerTraceDelete) | **Delete** /tracer/trace/{id}/ | 
[**TracerTraceGetEvalNames**](TracerAPI.md#TracerTraceGetEvalNames) | **Get** /tracer/trace/get_eval_names/ | 
[**TracerTraceGetTraceExportData**](TracerAPI.md#TracerTraceGetTraceExportData) | **Get** /tracer/trace/get_trace_export_data/ | 
[**TracerTraceGetTraceIdByIndex**](TracerAPI.md#TracerTraceGetTraceIdByIndex) | **Get** /tracer/trace/get_trace_id_by_index/ | 
[**TracerTraceGetTraceIdByIndexObserve**](TracerAPI.md#TracerTraceGetTraceIdByIndexObserve) | **Get** /tracer/trace/get_trace_id_by_index_observe/ | 
[**TracerTraceList**](TracerAPI.md#TracerTraceList) | **Get** /tracer/trace/ | 
[**TracerTraceListTracesOfSession**](TracerAPI.md#TracerTraceListTracesOfSession) | **Get** /tracer/trace/list_traces_of_session/ | 
[**TracerTracePartialUpdate**](TracerAPI.md#TracerTracePartialUpdate) | **Patch** /tracer/trace/{id}/ | 
[**TracerTraceSessionCreate**](TracerAPI.md#TracerTraceSessionCreate) | **Post** /tracer/trace-session/ | 
[**TracerTraceSessionDelete**](TracerAPI.md#TracerTraceSessionDelete) | **Delete** /tracer/trace-session/{id}/ | 
[**TracerTraceSessionEvalLogs**](TracerAPI.md#TracerTraceSessionEvalLogs) | **Get** /tracer/trace-session/{id}/eval_logs/ | Session-scoped eval log feed for TracesDrawer&#39;s \&quot;Evals\&quot; tab.
[**TracerTraceSessionGetSessionFilterValues**](TracerAPI.md#TracerTraceSessionGetSessionFilterValues) | **Get** /tracer/trace-session/get_session_filter_values/ | 
[**TracerTraceSessionGetTraceSessionExportData**](TracerAPI.md#TracerTraceSessionGetTraceSessionExportData) | **Get** /tracer/trace-session/get_trace_session_export_data/ | 
[**TracerTraceSessionList**](TracerAPI.md#TracerTraceSessionList) | **Get** /tracer/trace-session/ | 
[**TracerTraceSessionPartialUpdate**](TracerAPI.md#TracerTraceSessionPartialUpdate) | **Patch** /tracer/trace-session/{id}/ | 
[**TracerTraceSessionUpdate**](TracerAPI.md#TracerTraceSessionUpdate) | **Put** /tracer/trace-session/{id}/ | 
[**TracerTraceUpdate**](TracerAPI.md#TracerTraceUpdate) | **Put** /tracer/trace/{id}/ | 
[**TracerUserAlertLogsCreate**](TracerAPI.md#TracerUserAlertLogsCreate) | **Post** /tracer/user-alert-logs/ | 
[**TracerUserAlertLogsDelete**](TracerAPI.md#TracerUserAlertLogsDelete) | **Delete** /tracer/user-alert-logs/{id}/ | 
[**TracerUserAlertLogsPartialUpdate**](TracerAPI.md#TracerUserAlertLogsPartialUpdate) | **Patch** /tracer/user-alert-logs/{id}/ | 
[**TracerUserAlertLogsUpdate**](TracerAPI.md#TracerUserAlertLogsUpdate) | **Put** /tracer/user-alert-logs/{id}/ | 
[**TracerUserAlertsDuplicate**](TracerAPI.md#TracerUserAlertsDuplicate) | **Post** /tracer/user-alerts/duplicate/ | 
[**TracerUserAlertsListMonitors**](TracerAPI.md#TracerUserAlertsListMonitors) | **Get** /tracer/user-alerts/list_monitors/ | 
[**TracerUserAlertsUpdate**](TracerAPI.md#TracerUserAlertsUpdate) | **Put** /tracer/user-alerts/{id}/ | 
[**TracerUsersGetCodeExampleList**](TracerAPI.md#TracerUsersGetCodeExampleList) | **Get** /tracer/users/get_code_example/ | 



## TracerFeedIssuesCreateLinearIssueCreate

> CreateLinearIssueResponse TracerFeedIssuesCreateLinearIssueCreate(ctx, clusterId).CreateLinearIssue(createLinearIssue).Execute()





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
	createLinearIssue := *openapiclient.NewCreateLinearIssue("TeamId_example") // CreateLinearIssue | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesCreateLinearIssueCreate(context.Background(), clusterId).CreateLinearIssue(createLinearIssue).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesCreateLinearIssueCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesCreateLinearIssueCreate`: CreateLinearIssueResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesCreateLinearIssueCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesCreateLinearIssueCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **createLinearIssue** | [**CreateLinearIssue**](CreateLinearIssue.md) |  | 

### Return type

[**CreateLinearIssueResponse**](CreateLinearIssueResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesDeepAnalysisCreate

> DeepAnalysisDispatchApiResponse TracerFeedIssuesDeepAnalysisCreate(ctx, clusterId).DeepAnalysisBody(deepAnalysisBody).Execute()





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
	deepAnalysisBody := *openapiclient.NewDeepAnalysisBody("TraceId_example") // DeepAnalysisBody | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesDeepAnalysisCreate(context.Background(), clusterId).DeepAnalysisBody(deepAnalysisBody).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesDeepAnalysisCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesDeepAnalysisCreate`: DeepAnalysisDispatchApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesDeepAnalysisCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesDeepAnalysisCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **deepAnalysisBody** | [**DeepAnalysisBody**](DeepAnalysisBody.md) |  | 

### Return type

[**DeepAnalysisDispatchApiResponse**](DeepAnalysisDispatchApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesOverviewList

> OverviewApiResponse TracerFeedIssuesOverviewList(ctx, clusterId).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesOverviewList(context.Background(), clusterId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesOverviewList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesOverviewList`: OverviewApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesOverviewList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesOverviewListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**OverviewApiResponse**](OverviewApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesPartialUpdate

> FeedDetailApiResponse TracerFeedIssuesPartialUpdate(ctx, clusterId).FeedUpdateBody(feedUpdateBody).Execute()





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
	feedUpdateBody := *openapiclient.NewFeedUpdateBody() // FeedUpdateBody | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesPartialUpdate(context.Background(), clusterId).FeedUpdateBody(feedUpdateBody).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesPartialUpdate`: FeedDetailApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **feedUpdateBody** | [**FeedUpdateBody**](FeedUpdateBody.md) |  | 

### Return type

[**FeedDetailApiResponse**](FeedDetailApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesRootCauseList

> DeepAnalysisApiResponse TracerFeedIssuesRootCauseList(ctx, clusterId).TraceId(traceId).Execute()

GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id=X



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
	traceId := "traceId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesRootCauseList(context.Background(), clusterId).TraceId(traceId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesRootCauseList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesRootCauseList`: DeepAnalysisApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesRootCauseList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesRootCauseListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **traceId** | **string** |  | 

### Return type

[**DeepAnalysisApiResponse**](DeepAnalysisApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesSidebarList

> FeedSidebarApiResponse TracerFeedIssuesSidebarList(ctx, clusterId).TraceId(traceId).Execute()

GET /tracer/feed/issues/{cluster_id}/sidebar/



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
	traceId := "traceId_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesSidebarList(context.Background(), clusterId).TraceId(traceId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesSidebarList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesSidebarList`: FeedSidebarApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesSidebarList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesSidebarListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **traceId** | **string** |  | 

### Return type

[**FeedSidebarApiResponse**](FeedSidebarApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesTracesList

> TracesTabApiResponse TracerFeedIssuesTracesList(ctx, clusterId).Limit(limit).Offset(offset).Execute()





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
	limit := int32(56) // int32 |  (optional) (default to 50)
	offset := int32(56) // int32 |  (optional) (default to 0)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesTracesList(context.Background(), clusterId).Limit(limit).Offset(offset).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesTracesList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesTracesList`: TracesTabApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesTracesList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesTracesListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **limit** | **int32** |  | [default to 50]
 **offset** | **int32** |  | [default to 0]

### Return type

[**TracesTabApiResponse**](TracesTabApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerFeedIssuesTrendsList

> TrendsTabApiResponse TracerFeedIssuesTrendsList(ctx, clusterId).Days(days).Execute()





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
	days := int32(56) // int32 |  (optional) (default to 14)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerFeedIssuesTrendsList(context.Background(), clusterId).Days(days).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerFeedIssuesTrendsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerFeedIssuesTrendsList`: TrendsTabApiResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerFeedIssuesTrendsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**clusterId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerFeedIssuesTrendsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **days** | **int32** |  | [default to 14]

### Return type

[**TrendsTabApiResponse**](TrendsTabApiResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAgentGraph

> TracerTraceList200Response TracerTraceAgentGraph(ctx).ProjectId(projectId).Page(page).Limit(limit).Filters(filters).Execute()

Return the aggregate agent graph for a project.



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
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceAgentGraph(context.Background()).ProjectId(projectId).Page(page).Limit(limit).Filters(filters).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAgentGraph``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAgentGraph`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAgentGraph`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAgentGraphRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectId** | **string** |  | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **filters** | **string** |  | [default to &quot;[]&quot;]

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


## TracerTraceAnnotationCreate

> GetTraceAnnotation TracerTraceAnnotationCreate(ctx).GetTraceAnnotation(getTraceAnnotation).Execute()





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
	getTraceAnnotation := *openapiclient.NewGetTraceAnnotation() // GetTraceAnnotation | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationCreate(context.Background()).GetTraceAnnotation(getTraceAnnotation).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationCreate`: GetTraceAnnotation
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md) |  | 

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAnnotationDelete

> TracerTraceAnnotationDelete(ctx, id).Execute()





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
	r, err := apiClient.TracerAPI.TracerTraceAnnotationDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationDeleteRequest struct via the builder pattern


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


## TracerTraceAnnotationGetAnnotationValues

> GetTraceAnnotationValuesResponse TracerTraceAnnotationGetAnnotationValues(ctx).Page(page).Limit(limit).ObservationSpanId(observationSpanId).TraceId(traceId).Annotators(annotators).ExcludeAnnotators(excludeAnnotators).Execute()





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
	observationSpanId := "observationSpanId_example" // string |  (optional)
	traceId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	annotators := "annotators_example" // string |  (optional)
	excludeAnnotators := "excludeAnnotators_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationGetAnnotationValues(context.Background()).Page(page).Limit(limit).ObservationSpanId(observationSpanId).TraceId(traceId).Annotators(annotators).ExcludeAnnotators(excludeAnnotators).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationGetAnnotationValues``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationGetAnnotationValues`: GetTraceAnnotationValuesResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationGetAnnotationValues`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationGetAnnotationValuesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **observationSpanId** | **string** |  | 
 **traceId** | **string** |  | 
 **annotators** | **string** |  | 
 **excludeAnnotators** | **string** |  | 

### Return type

[**GetTraceAnnotationValuesResponse**](GetTraceAnnotationValuesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAnnotationList

> TracerTraceAnnotationList200Response TracerTraceAnnotationList(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationList(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationList`: TracerTraceAnnotationList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**TracerTraceAnnotationList200Response**](TracerTraceAnnotationList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAnnotationPartialUpdate

> GetTraceAnnotation TracerTraceAnnotationPartialUpdate(ctx, id).GetTraceAnnotation(getTraceAnnotation).Execute()





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
	getTraceAnnotation := *openapiclient.NewGetTraceAnnotation() // GetTraceAnnotation | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationPartialUpdate(context.Background(), id).GetTraceAnnotation(getTraceAnnotation).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationPartialUpdate`: GetTraceAnnotation
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md) |  | 

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAnnotationRead

> GetTraceAnnotation TracerTraceAnnotationRead(ctx, id).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationRead`: GetTraceAnnotation
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceAnnotationUpdate

> GetTraceAnnotation TracerTraceAnnotationUpdate(ctx, id).GetTraceAnnotation(getTraceAnnotation).Execute()





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
	getTraceAnnotation := *openapiclient.NewGetTraceAnnotation() // GetTraceAnnotation | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceAnnotationUpdate(context.Background(), id).GetTraceAnnotation(getTraceAnnotation).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceAnnotationUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceAnnotationUpdate`: GetTraceAnnotation
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceAnnotationUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceAnnotationUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md) |  | 

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceBulkCreate

> Trace TracerTraceBulkCreate(ctx).Trace(trace).Execute()





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
	trace := *openapiclient.NewTrace("Project_example") // Trace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceBulkCreate(context.Background()).Trace(trace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceBulkCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceBulkCreate`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceBulkCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceBulkCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **trace** | [**Trace**](Trace.md) |  | 

### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceCompareTraces

> Trace TracerTraceCompareTraces(ctx).Trace(trace).Execute()





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
	trace := *openapiclient.NewTrace("Project_example") // Trace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceCompareTraces(context.Background()).Trace(trace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceCompareTraces``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceCompareTraces`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceCompareTraces`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceCompareTracesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **trace** | [**Trace**](Trace.md) |  | 

### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceCreate

> Trace TracerTraceCreate(ctx).Trace(trace).Execute()





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
	trace := *openapiclient.NewTrace("Project_example") // Trace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceCreate(context.Background()).Trace(trace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceCreate`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **trace** | [**Trace**](Trace.md) |  | 

### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceDelete

> TracerTraceDelete(ctx, id).Execute()





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
	r, err := apiClient.TracerAPI.TracerTraceDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceDeleteRequest struct via the builder pattern


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


## TracerTraceGetEvalNames

> TracerTraceList200Response TracerTraceGetEvalNames(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceGetEvalNames(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceGetEvalNames``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceGetEvalNames`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceGetEvalNames`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceGetEvalNamesRequest struct via the builder pattern


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


## TracerTraceGetTraceExportData

> TracerTraceList200Response TracerTraceGetTraceExportData(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceGetTraceExportData(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceGetTraceExportData``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceGetTraceExportData`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceGetTraceExportData`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceGetTraceExportDataRequest struct via the builder pattern


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


## TracerTraceGetTraceIdByIndex

> TracerTraceList200Response TracerTraceGetTraceIdByIndex(ctx).TraceId(traceId).ProjectVersionId(projectVersionId).Page(page).Limit(limit).Filters(filters).Execute()





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
	traceId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	projectVersionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceGetTraceIdByIndex(context.Background()).TraceId(traceId).ProjectVersionId(projectVersionId).Page(page).Limit(limit).Filters(filters).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceGetTraceIdByIndex``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceGetTraceIdByIndex`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceGetTraceIdByIndex`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceGetTraceIdByIndexRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **traceId** | **string** |  | 
 **projectVersionId** | **string** |  | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **filters** | **string** |  | [default to &quot;[]&quot;]

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


## TracerTraceGetTraceIdByIndexObserve

> TracerTraceList200Response TracerTraceGetTraceIdByIndexObserve(ctx).TraceId(traceId).ProjectId(projectId).Page(page).Limit(limit).Filters(filters).Execute()





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
	traceId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceGetTraceIdByIndexObserve(context.Background()).TraceId(traceId).ProjectId(projectId).Page(page).Limit(limit).Filters(filters).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceGetTraceIdByIndexObserve``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceGetTraceIdByIndexObserve`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceGetTraceIdByIndexObserve`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceGetTraceIdByIndexObserveRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **traceId** | **string** |  | 
 **projectId** | **string** |  | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **filters** | **string** |  | [default to &quot;[]&quot;]

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


## TracerTraceList

> TracerTraceList200Response TracerTraceList(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceList(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceList`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceListRequest struct via the builder pattern


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


## TracerTraceListTracesOfSession

> TracerTraceList200Response TracerTraceListTracesOfSession(ctx).Page(page).Limit(limit).ProjectId(projectId).ProjectVersionId(projectVersionId).SessionId(sessionId).Filters(filters).PageNumber(pageNumber).PageSize(pageSize).Interval(interval).Execute()





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
	projectVersionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	sessionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	filters := "filters_example" // string |  (optional) (default to "[]")
	pageNumber := int32(56) // int32 |  (optional) (default to 0)
	pageSize := int32(56) // int32 |  (optional) (default to 30)
	interval := "interval_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceListTracesOfSession(context.Background()).Page(page).Limit(limit).ProjectId(projectId).ProjectVersionId(projectVersionId).SessionId(sessionId).Filters(filters).PageNumber(pageNumber).PageSize(pageSize).Interval(interval).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceListTracesOfSession``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceListTracesOfSession`: TracerTraceList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceListTracesOfSession`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceListTracesOfSessionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **projectId** | **string** |  | 
 **projectVersionId** | **string** |  | 
 **sessionId** | **string** |  | 
 **filters** | **string** |  | [default to &quot;[]&quot;]
 **pageNumber** | **int32** |  | [default to 0]
 **pageSize** | **int32** |  | [default to 30]
 **interval** | **string** |  | 

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


## TracerTracePartialUpdate

> Trace TracerTracePartialUpdate(ctx, id).Trace(trace).Execute()





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
	trace := *openapiclient.NewTrace("Project_example") // Trace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTracePartialUpdate(context.Background(), id).Trace(trace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTracePartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTracePartialUpdate`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTracePartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTracePartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **trace** | [**Trace**](Trace.md) |  | 

### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceSessionCreate

> TraceSession TracerTraceSessionCreate(ctx).TraceSession(traceSession).Execute()





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
	traceSession := *openapiclient.NewTraceSession("Project_example") // TraceSession | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionCreate(context.Background()).TraceSession(traceSession).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionCreate`: TraceSession
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **traceSession** | [**TraceSession**](TraceSession.md) |  | 

### Return type

[**TraceSession**](TraceSession.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceSessionDelete

> TracerTraceSessionDelete(ctx, id).Execute()





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
	r, err := apiClient.TracerAPI.TracerTraceSessionDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionDeleteRequest struct via the builder pattern


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


## TracerTraceSessionEvalLogs

> TraceSession TracerTraceSessionEvalLogs(ctx, id).Execute()

Session-scoped eval log feed for TracesDrawer's \"Evals\" tab.



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
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionEvalLogs(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionEvalLogs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionEvalLogs`: TraceSession
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionEvalLogs`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionEvalLogsRequest struct via the builder pattern


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


## TracerTraceSessionGetSessionFilterValues

> TracerTraceSessionList200Response TracerTraceSessionGetSessionFilterValues(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionGetSessionFilterValues(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionGetSessionFilterValues``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionGetSessionFilterValues`: TracerTraceSessionList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionGetSessionFilterValues`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionGetSessionFilterValuesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

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


## TracerTraceSessionGetTraceSessionExportData

> TracerTraceSessionList200Response TracerTraceSessionGetTraceSessionExportData(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionGetTraceSessionExportData(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionGetTraceSessionExportData``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionGetTraceSessionExportData`: TracerTraceSessionList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionGetTraceSessionExportData`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionGetTraceSessionExportDataRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

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


## TracerTraceSessionList

> TracerTraceSessionList200Response TracerTraceSessionList(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionList(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionList`: TracerTraceSessionList200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

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


## TracerTraceSessionPartialUpdate

> TraceSession TracerTraceSessionPartialUpdate(ctx, id).TraceSession(traceSession).Execute()





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
	traceSession := *openapiclient.NewTraceSession("Project_example") // TraceSession | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionPartialUpdate(context.Background(), id).TraceSession(traceSession).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionPartialUpdate`: TraceSession
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **traceSession** | [**TraceSession**](TraceSession.md) |  | 

### Return type

[**TraceSession**](TraceSession.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceSessionUpdate

> TraceSession TracerTraceSessionUpdate(ctx, id).TraceSession(traceSession).Execute()





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
	traceSession := *openapiclient.NewTraceSession("Project_example") // TraceSession | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceSessionUpdate(context.Background(), id).TraceSession(traceSession).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceSessionUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceSessionUpdate`: TraceSession
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceSessionUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceSessionUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **traceSession** | [**TraceSession**](TraceSession.md) |  | 

### Return type

[**TraceSession**](TraceSession.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerTraceUpdate

> Trace TracerTraceUpdate(ctx, id).Trace(trace).Execute()





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
	trace := *openapiclient.NewTrace("Project_example") // Trace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerTraceUpdate(context.Background(), id).Trace(trace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerTraceUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerTraceUpdate`: Trace
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerTraceUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerTraceUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **trace** | [**Trace**](Trace.md) |  | 

### Return type

[**Trace**](Trace.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertLogsCreate

> UserAlertMonitorLog TracerUserAlertLogsCreate(ctx).UserAlertMonitorLog(userAlertMonitorLog).Execute()





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
	userAlertMonitorLog := *openapiclient.NewUserAlertMonitorLog("Type_example", "Message_example") // UserAlertMonitorLog | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUserAlertLogsCreate(context.Background()).UserAlertMonitorLog(userAlertMonitorLog).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertLogsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertLogsCreate`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertLogsCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertLogsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md) |  | 

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertLogsDelete

> TracerUserAlertLogsDelete(ctx, id).Execute()





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
	r, err := apiClient.TracerAPI.TracerUserAlertLogsDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertLogsDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertLogsDeleteRequest struct via the builder pattern


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


## TracerUserAlertLogsPartialUpdate

> UserAlertMonitorLog TracerUserAlertLogsPartialUpdate(ctx, id).UserAlertMonitorLog(userAlertMonitorLog).Execute()





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
	userAlertMonitorLog := *openapiclient.NewUserAlertMonitorLog("Type_example", "Message_example") // UserAlertMonitorLog | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUserAlertLogsPartialUpdate(context.Background(), id).UserAlertMonitorLog(userAlertMonitorLog).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertLogsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertLogsPartialUpdate`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertLogsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertLogsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md) |  | 

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertLogsUpdate

> UserAlertMonitorLog TracerUserAlertLogsUpdate(ctx, id).UserAlertMonitorLog(userAlertMonitorLog).Execute()





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
	userAlertMonitorLog := *openapiclient.NewUserAlertMonitorLog("Type_example", "Message_example") // UserAlertMonitorLog | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUserAlertLogsUpdate(context.Background(), id).UserAlertMonitorLog(userAlertMonitorLog).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertLogsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertLogsUpdate`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertLogsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertLogsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md) |  | 

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertsDuplicate

> UserAlertMonitorDuplicateResponse TracerUserAlertsDuplicate(ctx).UserAlertMonitorDuplicate(userAlertMonitorDuplicate).Execute()





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
	userAlertMonitorDuplicate := *openapiclient.NewUserAlertMonitorDuplicate("Id_example", "Name_example") // UserAlertMonitorDuplicate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUserAlertsDuplicate(context.Background()).UserAlertMonitorDuplicate(userAlertMonitorDuplicate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertsDuplicate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertsDuplicate`: UserAlertMonitorDuplicateResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertsDuplicate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertsDuplicateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userAlertMonitorDuplicate** | [**UserAlertMonitorDuplicate**](UserAlertMonitorDuplicate.md) |  | 

### Return type

[**UserAlertMonitorDuplicateResponse**](UserAlertMonitorDuplicateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertsListMonitors

> ListAlerts200Response TracerUserAlertsListMonitors(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.TracerAPI.TracerUserAlertsListMonitors(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertsListMonitors``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertsListMonitors`: ListAlerts200Response
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertsListMonitors`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertsListMonitorsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListAlerts200Response**](ListAlerts200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUserAlertsUpdate

> UserAlertMonitor TracerUserAlertsUpdate(ctx, id).UserAlertMonitor(userAlertMonitor).Execute()





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
	userAlertMonitor := *openapiclient.NewUserAlertMonitor("Project_example", "Name_example", "MetricType_example", "ThresholdOperator_example", "Organization_example") // UserAlertMonitor | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUserAlertsUpdate(context.Background(), id).UserAlertMonitor(userAlertMonitor).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUserAlertsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUserAlertsUpdate`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUserAlertsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiTracerUserAlertsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **userAlertMonitor** | [**UserAlertMonitor**](UserAlertMonitor.md) |  | 

### Return type

[**UserAlertMonitor**](UserAlertMonitor.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## TracerUsersGetCodeExampleList

> UserCodeExampleResponse TracerUsersGetCodeExampleList(ctx).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.TracerAPI.TracerUsersGetCodeExampleList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `TracerAPI.TracerUsersGetCodeExampleList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `TracerUsersGetCodeExampleList`: UserCodeExampleResponse
	fmt.Fprintf(os.Stdout, "Response from `TracerAPI.TracerUsersGetCodeExampleList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiTracerUsersGetCodeExampleListRequest struct via the builder pattern


### Return type

[**UserCodeExampleResponse**](UserCodeExampleResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

