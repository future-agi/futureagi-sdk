# \UsersAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**GetCurrentUser**](UsersAPI.md#GetCurrentUser) | **Get** /accounts/user-info/ | 
[**ListOrganizationMembers**](UsersAPI.md#ListOrganizationMembers) | **Get** /accounts/organization/members/ | GET /accounts/organization/members/
[**ListWorkspaceMembers**](UsersAPI.md#ListWorkspaceMembers) | **Get** /accounts/workspace/{workspace_id}/members/ | GET /accounts/workspace/&lt;workspace_id&gt;/members/
[**ListWorkspaces**](UsersAPI.md#ListWorkspaces) | **Get** /accounts/workspace/list/ | 
[**SwitchWorkspace**](UsersAPI.md#SwitchWorkspace) | **Post** /accounts/workspace/switch/ | 



## GetCurrentUser

> UserInfoResponse GetCurrentUser(ctx).Execute()





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
	resp, r, err := apiClient.UsersAPI.GetCurrentUser(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `UsersAPI.GetCurrentUser``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetCurrentUser`: UserInfoResponse
	fmt.Fprintf(os.Stdout, "Response from `UsersAPI.GetCurrentUser`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiGetCurrentUserRequest struct via the builder pattern


### Return type

[**UserInfoResponse**](UserInfoResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListOrganizationMembers

> MemberListResponse ListOrganizationMembers(ctx).Page(page).Limit(limit).Search(search).FilterStatus(filterStatus).FilterRole(filterRole).Sort(sort).Execute()

GET /accounts/organization/members/



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
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional) (default to 20)
	search := "search_example" // string |  (optional) (default to "")
	filterStatus := []string{"FilterStatus_example"} // []string |  (optional)
	filterRole := []string{"Inner_example"} // []string |  (optional)
	sort := "sort_example" // string |  (optional) (default to "-created_at")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.UsersAPI.ListOrganizationMembers(context.Background()).Page(page).Limit(limit).Search(search).FilterStatus(filterStatus).FilterRole(filterRole).Sort(sort).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `UsersAPI.ListOrganizationMembers``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListOrganizationMembers`: MemberListResponse
	fmt.Fprintf(os.Stdout, "Response from `UsersAPI.ListOrganizationMembers`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListOrganizationMembersRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | [default to 20]
 **search** | **string** |  | [default to &quot;&quot;]
 **filterStatus** | **[]string** |  | 
 **filterRole** | **[]string** |  | 
 **sort** | **string** |  | [default to &quot;-created_at&quot;]

### Return type

[**MemberListResponse**](MemberListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListWorkspaceMembers

> MemberListResponse ListWorkspaceMembers(ctx, workspaceId).Page(page).Limit(limit).Search(search).FilterStatus(filterStatus).FilterRole(filterRole).Sort(sort).Execute()

GET /accounts/workspace/<workspace_id>/members/



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
	workspaceId := "workspaceId_example" // string | 
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional) (default to 20)
	search := "search_example" // string |  (optional) (default to "")
	filterStatus := []string{"FilterStatus_example"} // []string |  (optional)
	filterRole := []string{"Inner_example"} // []string |  (optional)
	sort := "sort_example" // string |  (optional) (default to "-created_at")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.UsersAPI.ListWorkspaceMembers(context.Background(), workspaceId).Page(page).Limit(limit).Search(search).FilterStatus(filterStatus).FilterRole(filterRole).Sort(sort).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `UsersAPI.ListWorkspaceMembers``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListWorkspaceMembers`: MemberListResponse
	fmt.Fprintf(os.Stdout, "Response from `UsersAPI.ListWorkspaceMembers`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**workspaceId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListWorkspaceMembersRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | [default to 20]
 **search** | **string** |  | [default to &quot;&quot;]
 **filterStatus** | **[]string** |  | 
 **filterRole** | **[]string** |  | 
 **sort** | **string** |  | [default to &quot;-created_at&quot;]

### Return type

[**MemberListResponse**](MemberListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListWorkspaces

> WorkspaceListPaginatedResponse ListWorkspaces(ctx).Page(page).Limit(limit).Search(search).Sort(sort).Execute()





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
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional) (default to 10)
	search := "search_example" // string |  (optional) (default to "")
	sort := "sort_example" // string |  (optional) (default to "")

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.UsersAPI.ListWorkspaces(context.Background()).Page(page).Limit(limit).Search(search).Sort(sort).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `UsersAPI.ListWorkspaces``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListWorkspaces`: WorkspaceListPaginatedResponse
	fmt.Fprintf(os.Stdout, "Response from `UsersAPI.ListWorkspaces`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListWorkspacesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | [default to 10]
 **search** | **string** |  | [default to &quot;&quot;]
 **sort** | **string** |  | [default to &quot;&quot;]

### Return type

[**WorkspaceListPaginatedResponse**](WorkspaceListPaginatedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SwitchWorkspace

> SwitchWorkspaceResponse SwitchWorkspace(ctx).SwitchWorkspace(switchWorkspace).Execute()





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
	switchWorkspace := *openapiclient.NewSwitchWorkspace("NewWorkspaceId_example") // SwitchWorkspace | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.UsersAPI.SwitchWorkspace(context.Background()).SwitchWorkspace(switchWorkspace).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `UsersAPI.SwitchWorkspace``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SwitchWorkspace`: SwitchWorkspaceResponse
	fmt.Fprintf(os.Stdout, "Response from `UsersAPI.SwitchWorkspace`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSwitchWorkspaceRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **switchWorkspace** | [**SwitchWorkspace**](SwitchWorkspace.md) |  | 

### Return type

[**SwitchWorkspaceResponse**](SwitchWorkspaceResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

