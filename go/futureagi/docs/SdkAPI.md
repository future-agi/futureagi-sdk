# \SdkAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SdkApiV1ConfigureEvaluationsCreate**](SdkAPI.md#SdkApiV1ConfigureEvaluationsCreate) | **Post** /sdk/api/v1/configure-evaluations/ | 
[**SdkApiV1EvalCreate**](SdkAPI.md#SdkApiV1EvalCreate) | **Post** /sdk/api/v1/eval/ | 
[**SdkApiV1EvalRead**](SdkAPI.md#SdkApiV1EvalRead) | **Get** /sdk/api/v1/eval/{eval_id}/ | 
[**SdkApiV1EvaluatePipelineCreate**](SdkAPI.md#SdkApiV1EvaluatePipelineCreate) | **Post** /sdk/api/v1/evaluate-pipeline/ | 
[**SdkApiV1EvaluatePipelineList**](SdkAPI.md#SdkApiV1EvaluatePipelineList) | **Get** /sdk/api/v1/evaluate-pipeline/ | 
[**SdkApiV1GetEvalsList**](SdkAPI.md#SdkApiV1GetEvalsList) | **Get** /sdk/api/v1/get-evals/ | 
[**SdkApiV1NewEvalCreate**](SdkAPI.md#SdkApiV1NewEvalCreate) | **Post** /sdk/api/v1/new-eval/ | 
[**SdkApiV1NewEvalList**](SdkAPI.md#SdkApiV1NewEvalList) | **Get** /sdk/api/v1/new-eval/ | 



## SdkApiV1ConfigureEvaluationsCreate

> SDKConfigureEvaluationsResponse SdkApiV1ConfigureEvaluationsCreate(ctx).SDKConfigureEvaluationsRequest(sDKConfigureEvaluationsRequest).Execute()





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
	sDKConfigureEvaluationsRequest := *openapiclient.NewSDKConfigureEvaluationsRequest(*openapiclient.NewConfigureEvaluations("EvalTemplates_example", map[string]string{"key": "Inner_example"}), "Platform_example") // SDKConfigureEvaluationsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1ConfigureEvaluationsCreate(context.Background()).SDKConfigureEvaluationsRequest(sDKConfigureEvaluationsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1ConfigureEvaluationsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1ConfigureEvaluationsCreate`: SDKConfigureEvaluationsResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1ConfigureEvaluationsCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1ConfigureEvaluationsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sDKConfigureEvaluationsRequest** | [**SDKConfigureEvaluationsRequest**](SDKConfigureEvaluationsRequest.md) |  | 

### Return type

[**SDKConfigureEvaluationsResponse**](SDKConfigureEvaluationsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1EvalCreate

> SDKStandaloneEvalResponse SdkApiV1EvalCreate(ctx).SDKStandaloneEvalRequest(sDKStandaloneEvalRequest).Execute()





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
	sDKStandaloneEvalRequest := *openapiclient.NewSDKStandaloneEvalRequest([]openapiclient.SDKStandaloneEvalInput{*openapiclient.NewSDKStandaloneEvalInput()}, map[string]string{"key": "Inner_example"}) // SDKStandaloneEvalRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1EvalCreate(context.Background()).SDKStandaloneEvalRequest(sDKStandaloneEvalRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1EvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1EvalCreate`: SDKStandaloneEvalResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1EvalCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1EvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sDKStandaloneEvalRequest** | [**SDKStandaloneEvalRequest**](SDKStandaloneEvalRequest.md) |  | 

### Return type

[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1EvalRead

> SDKEvalTemplateResponse SdkApiV1EvalRead(ctx, evalId).Execute()





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
	evalId := "evalId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1EvalRead(context.Background(), evalId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1EvalRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1EvalRead`: SDKEvalTemplateResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1EvalRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1EvalReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**SDKEvalTemplateResponse**](SDKEvalTemplateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1EvaluatePipelineCreate

> SDKCICDEvaluationRunAcceptedResponse SdkApiV1EvaluatePipelineCreate(ctx).CICDJob(cICDJob).Execute()





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
	cICDJob := *openapiclient.NewCICDJob("ProjectName_example", "Version_example", []openapiclient.CICDEvaluationItem{*openapiclient.NewCICDEvaluationItem("EvalTemplate_example", map[string]string{"key": "Inner_example"})}) // CICDJob | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1EvaluatePipelineCreate(context.Background()).CICDJob(cICDJob).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1EvaluatePipelineCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1EvaluatePipelineCreate`: SDKCICDEvaluationRunAcceptedResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1EvaluatePipelineCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1EvaluatePipelineCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cICDJob** | [**CICDJob**](CICDJob.md) |  | 

### Return type

[**SDKCICDEvaluationRunAcceptedResponse**](SDKCICDEvaluationRunAcceptedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1EvaluatePipelineList

> SDKCICDEvaluationRunsResponse SdkApiV1EvaluatePipelineList(ctx).ProjectName(projectName).Versions(versions).Execute()





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
	projectName := "projectName_example" // string | 
	versions := "versions_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1EvaluatePipelineList(context.Background()).ProjectName(projectName).Versions(versions).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1EvaluatePipelineList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1EvaluatePipelineList`: SDKCICDEvaluationRunsResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1EvaluatePipelineList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1EvaluatePipelineListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **projectName** | **string** |  | 
 **versions** | **string** |  | 

### Return type

[**SDKCICDEvaluationRunsResponse**](SDKCICDEvaluationRunsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1GetEvalsList

> SDKGetEvalsResponse SdkApiV1GetEvalsList(ctx).Execute()





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
	resp, r, err := apiClient.SdkAPI.SdkApiV1GetEvalsList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1GetEvalsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1GetEvalsList`: SDKGetEvalsResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1GetEvalsList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1GetEvalsListRequest struct via the builder pattern


### Return type

[**SDKGetEvalsResponse**](SDKGetEvalsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1NewEvalCreate

> SDKStandaloneEvalResponse SdkApiV1NewEvalCreate(ctx).SDKStandaloneEvalV2Request(sDKStandaloneEvalV2Request).Execute()





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
	sDKStandaloneEvalV2Request := *openapiclient.NewSDKStandaloneEvalV2Request("EvalName_example", map[string]string{"key": "Inner_example"}) // SDKStandaloneEvalV2Request | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1NewEvalCreate(context.Background()).SDKStandaloneEvalV2Request(sDKStandaloneEvalV2Request).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1NewEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1NewEvalCreate`: SDKStandaloneEvalResponse
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1NewEvalCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1NewEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sDKStandaloneEvalV2Request** | [**SDKStandaloneEvalV2Request**](SDKStandaloneEvalV2Request.md) |  | 

### Return type

[**SDKStandaloneEvalResponse**](SDKStandaloneEvalResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SdkApiV1NewEvalList

> SDKStandaloneEvalV2Response SdkApiV1NewEvalList(ctx).EvalId(evalId).Execute()





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
	evalId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SdkAPI.SdkApiV1NewEvalList(context.Background()).EvalId(evalId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SdkAPI.SdkApiV1NewEvalList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SdkApiV1NewEvalList`: SDKStandaloneEvalV2Response
	fmt.Fprintf(os.Stdout, "Response from `SdkAPI.SdkApiV1NewEvalList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSdkApiV1NewEvalListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **evalId** | **string** |  | 

### Return type

[**SDKStandaloneEvalV2Response**](SDKStandaloneEvalV2Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

