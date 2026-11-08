# \AccountsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**AccountsOrganizationMembersReactivateCreate**](AccountsAPI.md#AccountsOrganizationMembersReactivateCreate) | **Post** /accounts/organization/members/reactivate/ | POST /accounts/organization/members/reactivate/
[**AccountsOrganizationMembersRemoveDelete**](AccountsAPI.md#AccountsOrganizationMembersRemoveDelete) | **Delete** /accounts/organization/members/remove/ | DELETE /accounts/organization/members/remove/
[**AccountsOrganizationMembersRoleCreate**](AccountsAPI.md#AccountsOrganizationMembersRoleCreate) | **Post** /accounts/organization/members/role/ | POST /accounts/organization/members/role/
[**AccountsWorkspaceMembersRemoveDelete**](AccountsAPI.md#AccountsWorkspaceMembersRemoveDelete) | **Delete** /accounts/workspace/{workspace_id}/members/remove/ | DELETE /accounts/workspace/&lt;workspace_id&gt;/members/remove/
[**AccountsWorkspaceMembersRoleCreate**](AccountsAPI.md#AccountsWorkspaceMembersRoleCreate) | **Post** /accounts/workspace/{workspace_id}/members/role/ | POST /accounts/workspace/&lt;workspace_id&gt;/members/role/



## AccountsOrganizationMembersReactivateCreate

> MemberUserMutationResponse AccountsOrganizationMembersReactivateCreate(ctx).MemberRemove(memberRemove).Execute()

POST /accounts/organization/members/reactivate/



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
	memberRemove := *openapiclient.NewMemberRemove("UserId_example") // MemberRemove | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AccountsAPI.AccountsOrganizationMembersReactivateCreate(context.Background()).MemberRemove(memberRemove).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AccountsAPI.AccountsOrganizationMembersReactivateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AccountsOrganizationMembersReactivateCreate`: MemberUserMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `AccountsAPI.AccountsOrganizationMembersReactivateCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiAccountsOrganizationMembersReactivateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **memberRemove** | [**MemberRemove**](MemberRemove.md) |  | 

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AccountsOrganizationMembersRemoveDelete

> MemberUserMutationResponse AccountsOrganizationMembersRemoveDelete(ctx).MemberRemove(memberRemove).Execute()

DELETE /accounts/organization/members/remove/



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
	memberRemove := *openapiclient.NewMemberRemove("UserId_example") // MemberRemove | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AccountsAPI.AccountsOrganizationMembersRemoveDelete(context.Background()).MemberRemove(memberRemove).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AccountsAPI.AccountsOrganizationMembersRemoveDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AccountsOrganizationMembersRemoveDelete`: MemberUserMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `AccountsAPI.AccountsOrganizationMembersRemoveDelete`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiAccountsOrganizationMembersRemoveDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **memberRemove** | [**MemberRemove**](MemberRemove.md) |  | 

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AccountsOrganizationMembersRoleCreate

> MemberRoleUpdateResponse AccountsOrganizationMembersRoleCreate(ctx).MemberRoleUpdate(memberRoleUpdate).Execute()

POST /accounts/organization/members/role/



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
	memberRoleUpdate := *openapiclient.NewMemberRoleUpdate("UserId_example") // MemberRoleUpdate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AccountsAPI.AccountsOrganizationMembersRoleCreate(context.Background()).MemberRoleUpdate(memberRoleUpdate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AccountsAPI.AccountsOrganizationMembersRoleCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AccountsOrganizationMembersRoleCreate`: MemberRoleUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `AccountsAPI.AccountsOrganizationMembersRoleCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiAccountsOrganizationMembersRoleCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **memberRoleUpdate** | [**MemberRoleUpdate**](MemberRoleUpdate.md) |  | 

### Return type

[**MemberRoleUpdateResponse**](MemberRoleUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AccountsWorkspaceMembersRemoveDelete

> MemberUserMutationResponse AccountsWorkspaceMembersRemoveDelete(ctx, workspaceId).WorkspaceMemberRemove(workspaceMemberRemove).Execute()

DELETE /accounts/workspace/<workspace_id>/members/remove/



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
	workspaceMemberRemove := *openapiclient.NewWorkspaceMemberRemove("UserId_example") // WorkspaceMemberRemove | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AccountsAPI.AccountsWorkspaceMembersRemoveDelete(context.Background(), workspaceId).WorkspaceMemberRemove(workspaceMemberRemove).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AccountsAPI.AccountsWorkspaceMembersRemoveDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AccountsWorkspaceMembersRemoveDelete`: MemberUserMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `AccountsAPI.AccountsWorkspaceMembersRemoveDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**workspaceId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAccountsWorkspaceMembersRemoveDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **workspaceMemberRemove** | [**WorkspaceMemberRemove**](WorkspaceMemberRemove.md) |  | 

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AccountsWorkspaceMembersRoleCreate

> WorkspaceMemberRoleUpdateResponse AccountsWorkspaceMembersRoleCreate(ctx, workspaceId).WorkspaceMemberRoleUpdate(workspaceMemberRoleUpdate).Execute()

POST /accounts/workspace/<workspace_id>/members/role/



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
	workspaceMemberRoleUpdate := *openapiclient.NewWorkspaceMemberRoleUpdate("UserId_example", int32(123)) // WorkspaceMemberRoleUpdate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.AccountsAPI.AccountsWorkspaceMembersRoleCreate(context.Background(), workspaceId).WorkspaceMemberRoleUpdate(workspaceMemberRoleUpdate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `AccountsAPI.AccountsWorkspaceMembersRoleCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AccountsWorkspaceMembersRoleCreate`: WorkspaceMemberRoleUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `AccountsAPI.AccountsWorkspaceMembersRoleCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**workspaceId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAccountsWorkspaceMembersRoleCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **workspaceMemberRoleUpdate** | [**WorkspaceMemberRoleUpdate**](WorkspaceMemberRoleUpdate.md) |  | 

### Return type

[**WorkspaceMemberRoleUpdateResponse**](WorkspaceMemberRoleUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

