# \AlertsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**BulkMuteAlerts**](AlertsAPI.md#BulkMuteAlerts) | **Post** /tracer/user-alerts/bulk-mute/ | 
[**CreateAlert**](AlertsAPI.md#CreateAlert) | **Post** /tracer/user-alerts/ | 
[**DeleteAlert**](AlertsAPI.md#DeleteAlert) | **Delete** /tracer/user-alerts/{id}/ | 
[**GetAlert**](AlertsAPI.md#GetAlert) | **Get** /tracer/user-alerts/{id}/ | 
[**GetAlertDetails**](AlertsAPI.md#GetAlertDetails) | **Get** /tracer/user-alerts/{id}/details/ | 
[**GetAlertGraph**](AlertsAPI.md#GetAlertGraph) | **Get** /tracer/user-alerts/{id}/graph/ | Returns time-series data for a monitor&#39;s metric, suitable for graphing.
[**GetAlertLog**](AlertsAPI.md#GetAlertLog) | **Get** /tracer/user-alert-logs/{id}/ | 
[**ListAlertLogs**](AlertsAPI.md#ListAlertLogs) | **Get** /tracer/user-alert-logs/ | 
[**ListAlertLogsForAlert**](AlertsAPI.md#ListAlertLogsForAlert) | **Get** /tracer/user-alert-logs/{id}/list/ | 
[**ListAlertMetricOptions**](AlertsAPI.md#ListAlertMetricOptions) | **Get** /tracer/user-alerts/metric-options/ | 
[**ListAlerts**](AlertsAPI.md#ListAlerts) | **Get** /tracer/user-alerts/ | 
[**ListAllAlertLogs**](AlertsAPI.md#ListAllAlertLogs) | **Get** /tracer/user-alert-logs/all/ | 
[**PreviewAlertGraph**](AlertsAPI.md#PreviewAlertGraph) | **Post** /tracer/user-alerts/preview-graph/ | 
[**ResolveAlertLogs**](AlertsAPI.md#ResolveAlertLogs) | **Post** /tracer/user-alert-logs/resolve/ | 
[**UpdateAlert**](AlertsAPI.md#UpdateAlert) | **Patch** /tracer/user-alerts/{id}/ | 



## BulkMuteAlerts

> UserAlertMonitor BulkMuteAlerts(ctx).UserAlertMonitor(userAlertMonitor).Execute()





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
	userAlertMonitor := *openapiclient.NewUserAlertMonitor("Project_example", "Name_example", "MetricType_example", "ThresholdOperator_example", "Organization_example") // UserAlertMonitor | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AlertsAPI.BulkMuteAlerts(context.Background()).UserAlertMonitor(userAlertMonitor).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.BulkMuteAlerts``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `BulkMuteAlerts`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.BulkMuteAlerts`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiBulkMuteAlertsRequest struct via the builder pattern


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


## CreateAlert

> UserAlertMonitor CreateAlert(ctx).UserAlertMonitor(userAlertMonitor).Execute()





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
	userAlertMonitor := *openapiclient.NewUserAlertMonitor("Project_example", "Name_example", "MetricType_example", "ThresholdOperator_example", "Organization_example") // UserAlertMonitor | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AlertsAPI.CreateAlert(context.Background()).UserAlertMonitor(userAlertMonitor).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.CreateAlert``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateAlert`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.CreateAlert`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateAlertRequest struct via the builder pattern


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


## DeleteAlert

> DeleteAlert(ctx, id).Execute()





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
	r, err := apiClient.AlertsAPI.DeleteAlert(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.DeleteAlert``: %v\n", err)
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

Other parameters are passed through a pointer to a apiDeleteAlertRequest struct via the builder pattern


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


## GetAlert

> UserAlertMonitor GetAlert(ctx, id).Execute()





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
	resp, r, err := apiClient.AlertsAPI.GetAlert(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.GetAlert``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAlert`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.GetAlert`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAlertRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**UserAlertMonitor**](UserAlertMonitor.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAlertDetails

> UserAlertMonitor GetAlertDetails(ctx, id).Execute()





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
	resp, r, err := apiClient.AlertsAPI.GetAlertDetails(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.GetAlertDetails``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAlertDetails`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.GetAlertDetails`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAlertDetailsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**UserAlertMonitor**](UserAlertMonitor.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAlertGraph

> UserAlertMonitor GetAlertGraph(ctx, id).Execute()

Returns time-series data for a monitor's metric, suitable for graphing.



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
	resp, r, err := apiClient.AlertsAPI.GetAlertGraph(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.GetAlertGraph``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAlertGraph`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.GetAlertGraph`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAlertGraphRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**UserAlertMonitor**](UserAlertMonitor.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAlertLog

> UserAlertMonitorLog GetAlertLog(ctx, id).Execute()





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
	resp, r, err := apiClient.AlertsAPI.GetAlertLog(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.GetAlertLog``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAlertLog`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.GetAlertLog`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAlertLogRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAlertLogs

> ListAlertLogs200Response ListAlertLogs(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ListAlertLogs(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ListAlertLogs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAlertLogs`: ListAlertLogs200Response
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ListAlertLogs`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAlertLogsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListAlertLogs200Response**](ListAlertLogs200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAlertLogsForAlert

> UserAlertMonitorLog ListAlertLogsForAlert(ctx, id).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ListAlertLogsForAlert(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ListAlertLogsForAlert``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAlertLogsForAlert`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ListAlertLogsForAlert`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListAlertLogsForAlertRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAlertMetricOptions

> UserAlertMonitorMetricOptionsResponse ListAlertMetricOptions(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ListAlertMetricOptions(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ListAlertMetricOptions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAlertMetricOptions`: UserAlertMonitorMetricOptionsResponse
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ListAlertMetricOptions`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAlertMetricOptionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**UserAlertMonitorMetricOptionsResponse**](UserAlertMonitorMetricOptionsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAlerts

> ListAlerts200Response ListAlerts(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ListAlerts(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ListAlerts``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAlerts`: ListAlerts200Response
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ListAlerts`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAlertsRequest struct via the builder pattern


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


## ListAllAlertLogs

> ListAlertLogs200Response ListAllAlertLogs(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ListAllAlertLogs(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ListAllAlertLogs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAllAlertLogs`: ListAlertLogs200Response
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ListAllAlertLogs`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAllAlertLogsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListAlertLogs200Response**](ListAlertLogs200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## PreviewAlertGraph

> UserAlertMonitor PreviewAlertGraph(ctx).UserAlertMonitor(userAlertMonitor).Execute()





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
	userAlertMonitor := *openapiclient.NewUserAlertMonitor("Project_example", "Name_example", "MetricType_example", "ThresholdOperator_example", "Organization_example") // UserAlertMonitor | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AlertsAPI.PreviewAlertGraph(context.Background()).UserAlertMonitor(userAlertMonitor).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.PreviewAlertGraph``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `PreviewAlertGraph`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.PreviewAlertGraph`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiPreviewAlertGraphRequest struct via the builder pattern


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


## ResolveAlertLogs

> UserAlertMonitorLog ResolveAlertLogs(ctx).UserAlertMonitorLog(userAlertMonitorLog).Execute()





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
	resp, r, err := apiClient.AlertsAPI.ResolveAlertLogs(context.Background()).UserAlertMonitorLog(userAlertMonitorLog).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.ResolveAlertLogs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ResolveAlertLogs`: UserAlertMonitorLog
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.ResolveAlertLogs`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiResolveAlertLogsRequest struct via the builder pattern


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


## UpdateAlert

> UserAlertMonitor UpdateAlert(ctx, id).UserAlertMonitor(userAlertMonitor).Execute()





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
	resp, r, err := apiClient.AlertsAPI.UpdateAlert(context.Background(), id).UserAlertMonitor(userAlertMonitor).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AlertsAPI.UpdateAlert``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateAlert`: UserAlertMonitor
	fmt.Fprintf(os.Stdout, "Response from `AlertsAPI.UpdateAlert`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateAlertRequest struct via the builder pattern


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

