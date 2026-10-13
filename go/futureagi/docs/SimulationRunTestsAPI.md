# \SimulationRunTestsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreateRunTest**](SimulationRunTestsAPI.md#CreateRunTest) | **Post** /simulate/run-tests/create/ | 
[**DeleteRunTest**](SimulationRunTestsAPI.md#DeleteRunTest) | **Delete** /simulate/run-tests/{run_test_id}/ | 
[**ExecuteRunTest**](SimulationRunTestsAPI.md#ExecuteRunTest) | **Post** /simulate/run-tests/{run_test_id}/execute/ | 
[**GetRunTest**](SimulationRunTestsAPI.md#GetRunTest) | **Get** /simulate/run-tests/{run_test_id}/ | 
[**GetRunTestAnalytics**](SimulationRunTestsAPI.md#GetRunTestAnalytics) | **Get** /simulate/run-tests/{run_test_id}/analytics/ | 
[**GetRunTestStatus**](SimulationRunTestsAPI.md#GetRunTestStatus) | **Get** /simulate/run-tests/{run_test_id}/status/ | 
[**ListRunTestCallExecutions**](SimulationRunTestsAPI.md#ListRunTestCallExecutions) | **Get** /simulate/run-tests/{run_test_id}/call-executions/ | 
[**ListRunTestExecutions**](SimulationRunTestsAPI.md#ListRunTestExecutions) | **Get** /simulate/run-tests/{run_test_id}/executions/ | 
[**ListRunTests**](SimulationRunTestsAPI.md#ListRunTests) | **Get** /simulate/run-tests/ | 
[**UpdateRunTest**](SimulationRunTestsAPI.md#UpdateRunTest) | **Patch** /simulate/run-tests/{run_test_id}/ | 



## CreateRunTest

> RunTestResponse CreateRunTest(ctx).CreateRunTest(createRunTest).Execute()





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
	createRunTest := *openapiclient.NewCreateRunTest("Name_example", "AgentDefinitionId_example", []string{"ScenarioIds_example"}) // CreateRunTest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.CreateRunTest(context.Background()).CreateRunTest(createRunTest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.CreateRunTest``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateRunTest`: RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.CreateRunTest`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateRunTestRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createRunTest** | [**CreateRunTest**](CreateRunTest.md) |  | 

### Return type

[**RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeleteRunTest

> RunTestMessageResponse DeleteRunTest(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.DeleteRunTest(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.DeleteRunTest``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DeleteRunTest`: RunTestMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.DeleteRunTest`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteRunTestRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestMessageResponse**](RunTestMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ExecuteRunTest

> RunTestExecutionResponse ExecuteRunTest(ctx, runTestId).ExecuteRunTest(executeRunTest).Execute()





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
	runTestId := "runTestId_example" // string | 
	executeRunTest := *openapiclient.NewExecuteRunTest() // ExecuteRunTest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.ExecuteRunTest(context.Background(), runTestId).ExecuteRunTest(executeRunTest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.ExecuteRunTest``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ExecuteRunTest`: RunTestExecutionResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.ExecuteRunTest`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiExecuteRunTestRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **executeRunTest** | [**ExecuteRunTest**](ExecuteRunTest.md) |  | 

### Return type

[**RunTestExecutionResponse**](RunTestExecutionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetRunTest

> RunTestResponse GetRunTest(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.GetRunTest(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.GetRunTest``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetRunTest`: RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.GetRunTest`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetRunTestRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetRunTestAnalytics

> RunTestAnalytics GetRunTestAnalytics(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.GetRunTestAnalytics(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.GetRunTestAnalytics``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetRunTestAnalytics`: RunTestAnalytics
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.GetRunTestAnalytics`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetRunTestAnalyticsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestAnalytics**](RunTestAnalytics.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetRunTestStatus

> TestExecutionStatusSummary GetRunTestStatus(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.GetRunTestStatus(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.GetRunTestStatus``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetRunTestStatus`: TestExecutionStatusSummary
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.GetRunTestStatus`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetRunTestStatusRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**TestExecutionStatusSummary**](TestExecutionStatusSummary.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListRunTestCallExecutions

> RunTestCallExecutionsResponse ListRunTestCallExecutions(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.ListRunTestCallExecutions(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.ListRunTestCallExecutions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListRunTestCallExecutions`: RunTestCallExecutionsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.ListRunTestCallExecutions`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListRunTestCallExecutionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestCallExecutionsResponse**](RunTestCallExecutionsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListRunTestExecutions

> []TestExecutionItemResponse ListRunTestExecutions(ctx, runTestId).Execute()





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
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.ListRunTestExecutions(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.ListRunTestExecutions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListRunTestExecutions`: []TestExecutionItemResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.ListRunTestExecutions`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListRunTestExecutionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**[]TestExecutionItemResponse**](TestExecutionItemResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListRunTests

> []RunTestResponse ListRunTests(ctx).Search(search).SimulationType(simulationType).PromptTemplateId(promptTemplateId).Page(page).Limit(limit).Execute()





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
	search := "search_example" // string |  (optional) (default to "")
	simulationType := "simulationType_example" // string |  (optional)
	promptTemplateId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.ListRunTests(context.Background()).Search(search).SimulationType(simulationType).PromptTemplateId(promptTemplateId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.ListRunTests``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListRunTests`: []RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.ListRunTests`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListRunTestsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **string** |  | [default to &quot;&quot;]
 **simulationType** | **string** |  | 
 **promptTemplateId** | **string** |  | 
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | 

### Return type

[**[]RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateRunTest

> RunTestResponse UpdateRunTest(ctx, runTestId).UpdateRunTest(updateRunTest).Execute()





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
	runTestId := "runTestId_example" // string | 
	updateRunTest := *openapiclient.NewUpdateRunTest() // UpdateRunTest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationRunTestsAPI.UpdateRunTest(context.Background(), runTestId).UpdateRunTest(updateRunTest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationRunTestsAPI.UpdateRunTest``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateRunTest`: RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationRunTestsAPI.UpdateRunTest`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateRunTestRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **updateRunTest** | [**UpdateRunTest**](UpdateRunTest.md) |  | 

### Return type

[**RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

