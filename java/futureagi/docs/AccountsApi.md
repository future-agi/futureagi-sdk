# AccountsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**accountsOrganizationMembersReactivateCreate**](AccountsApi.md#accountsOrganizationMembersReactivateCreate) | **POST** /accounts/organization/members/reactivate/ | POST /accounts/organization/members/reactivate/ |
| [**accountsOrganizationMembersReactivateCreateWithHttpInfo**](AccountsApi.md#accountsOrganizationMembersReactivateCreateWithHttpInfo) | **POST** /accounts/organization/members/reactivate/ | POST /accounts/organization/members/reactivate/ |
| [**accountsOrganizationMembersRemoveDelete**](AccountsApi.md#accountsOrganizationMembersRemoveDelete) | **DELETE** /accounts/organization/members/remove/ | DELETE /accounts/organization/members/remove/ |
| [**accountsOrganizationMembersRemoveDeleteWithHttpInfo**](AccountsApi.md#accountsOrganizationMembersRemoveDeleteWithHttpInfo) | **DELETE** /accounts/organization/members/remove/ | DELETE /accounts/organization/members/remove/ |
| [**accountsOrganizationMembersRoleCreate**](AccountsApi.md#accountsOrganizationMembersRoleCreate) | **POST** /accounts/organization/members/role/ | POST /accounts/organization/members/role/ |
| [**accountsOrganizationMembersRoleCreateWithHttpInfo**](AccountsApi.md#accountsOrganizationMembersRoleCreateWithHttpInfo) | **POST** /accounts/organization/members/role/ | POST /accounts/organization/members/role/ |
| [**accountsWorkspaceMembersRemoveDelete**](AccountsApi.md#accountsWorkspaceMembersRemoveDelete) | **DELETE** /accounts/workspace/{workspace_id}/members/remove/ | DELETE /accounts/workspace/&lt;workspace_id&gt;/members/remove/ |
| [**accountsWorkspaceMembersRemoveDeleteWithHttpInfo**](AccountsApi.md#accountsWorkspaceMembersRemoveDeleteWithHttpInfo) | **DELETE** /accounts/workspace/{workspace_id}/members/remove/ | DELETE /accounts/workspace/&lt;workspace_id&gt;/members/remove/ |
| [**accountsWorkspaceMembersRoleCreate**](AccountsApi.md#accountsWorkspaceMembersRoleCreate) | **POST** /accounts/workspace/{workspace_id}/members/role/ | POST /accounts/workspace/&lt;workspace_id&gt;/members/role/ |
| [**accountsWorkspaceMembersRoleCreateWithHttpInfo**](AccountsApi.md#accountsWorkspaceMembersRoleCreateWithHttpInfo) | **POST** /accounts/workspace/{workspace_id}/members/role/ | POST /accounts/workspace/&lt;workspace_id&gt;/members/role/ |



## accountsOrganizationMembersReactivateCreate

> MemberUserMutationResponse accountsOrganizationMembersReactivateCreate(memberRemove)

POST /accounts/organization/members/reactivate/

Re-activates a deactivated org membership and restores workspace memberships that were soft-deactivated during removal.  If no prior workspace memberships exist, the user is added to the default workspace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRemove memberRemove = new MemberRemove(); // MemberRemove | 
        try {
            MemberUserMutationResponse result = apiInstance.accountsOrganizationMembersReactivateCreate(memberRemove);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersReactivateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRemove** | [**MemberRemove**](MemberRemove.md)|  | |

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## accountsOrganizationMembersReactivateCreateWithHttpInfo

> ApiResponse<MemberUserMutationResponse> accountsOrganizationMembersReactivateCreate accountsOrganizationMembersReactivateCreateWithHttpInfo(memberRemove)

POST /accounts/organization/members/reactivate/

Re-activates a deactivated org membership and restores workspace memberships that were soft-deactivated during removal.  If no prior workspace memberships exist, the user is added to the default workspace.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRemove memberRemove = new MemberRemove(); // MemberRemove | 
        try {
            ApiResponse<MemberUserMutationResponse> response = apiInstance.accountsOrganizationMembersReactivateCreateWithHttpInfo(memberRemove);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersReactivateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRemove** | [**MemberRemove**](MemberRemove.md)|  | |

### Return type

ApiResponse<[**MemberUserMutationResponse**](MemberUserMutationResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## accountsOrganizationMembersRemoveDelete

> MemberUserMutationResponse accountsOrganizationMembersRemoveDelete(memberRemove)

DELETE /accounts/organization/members/remove/

Soft-deactivates OrganizationMembership and cascades to workspace memberships.  Signals handle Redis clear + audit log.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRemove memberRemove = new MemberRemove(); // MemberRemove | 
        try {
            MemberUserMutationResponse result = apiInstance.accountsOrganizationMembersRemoveDelete(memberRemove);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersRemoveDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRemove** | [**MemberRemove**](MemberRemove.md)|  | |

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## accountsOrganizationMembersRemoveDeleteWithHttpInfo

> ApiResponse<MemberUserMutationResponse> accountsOrganizationMembersRemoveDelete accountsOrganizationMembersRemoveDeleteWithHttpInfo(memberRemove)

DELETE /accounts/organization/members/remove/

Soft-deactivates OrganizationMembership and cascades to workspace memberships.  Signals handle Redis clear + audit log.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRemove memberRemove = new MemberRemove(); // MemberRemove | 
        try {
            ApiResponse<MemberUserMutationResponse> response = apiInstance.accountsOrganizationMembersRemoveDeleteWithHttpInfo(memberRemove);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersRemoveDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRemove** | [**MemberRemove**](MemberRemove.md)|  | |

### Return type

ApiResponse<[**MemberUserMutationResponse**](MemberUserMutationResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## accountsOrganizationMembersRoleCreate

> MemberRoleUpdateResponse accountsOrganizationMembersRoleCreate(memberRoleUpdate)

POST /accounts/organization/members/role/

Update a member&#39;s org level and/or workspace level.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRoleUpdate memberRoleUpdate = new MemberRoleUpdate(); // MemberRoleUpdate | 
        try {
            MemberRoleUpdateResponse result = apiInstance.accountsOrganizationMembersRoleCreate(memberRoleUpdate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersRoleCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRoleUpdate** | [**MemberRoleUpdate**](MemberRoleUpdate.md)|  | |

### Return type

[**MemberRoleUpdateResponse**](MemberRoleUpdateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## accountsOrganizationMembersRoleCreateWithHttpInfo

> ApiResponse<MemberRoleUpdateResponse> accountsOrganizationMembersRoleCreate accountsOrganizationMembersRoleCreateWithHttpInfo(memberRoleUpdate)

POST /accounts/organization/members/role/

Update a member&#39;s org level and/or workspace level.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        MemberRoleUpdate memberRoleUpdate = new MemberRoleUpdate(); // MemberRoleUpdate | 
        try {
            ApiResponse<MemberRoleUpdateResponse> response = apiInstance.accountsOrganizationMembersRoleCreateWithHttpInfo(memberRoleUpdate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsOrganizationMembersRoleCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **memberRoleUpdate** | [**MemberRoleUpdate**](MemberRoleUpdate.md)|  | |

### Return type

ApiResponse<[**MemberRoleUpdateResponse**](MemberRoleUpdateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## accountsWorkspaceMembersRemoveDelete

> MemberUserMutationResponse accountsWorkspaceMembersRemoveDelete(workspaceId, workspaceMemberRemove)

DELETE /accounts/workspace/&lt;workspace_id&gt;/members/remove/

Remove a member from a workspace only (keeps org membership).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        WorkspaceMemberRemove workspaceMemberRemove = new WorkspaceMemberRemove(); // WorkspaceMemberRemove | 
        try {
            MemberUserMutationResponse result = apiInstance.accountsWorkspaceMembersRemoveDelete(workspaceId, workspaceMemberRemove);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsWorkspaceMembersRemoveDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **workspaceId** | **String**|  | |
| **workspaceMemberRemove** | [**WorkspaceMemberRemove**](WorkspaceMemberRemove.md)|  | |

### Return type

[**MemberUserMutationResponse**](MemberUserMutationResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## accountsWorkspaceMembersRemoveDeleteWithHttpInfo

> ApiResponse<MemberUserMutationResponse> accountsWorkspaceMembersRemoveDelete accountsWorkspaceMembersRemoveDeleteWithHttpInfo(workspaceId, workspaceMemberRemove)

DELETE /accounts/workspace/&lt;workspace_id&gt;/members/remove/

Remove a member from a workspace only (keeps org membership).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        WorkspaceMemberRemove workspaceMemberRemove = new WorkspaceMemberRemove(); // WorkspaceMemberRemove | 
        try {
            ApiResponse<MemberUserMutationResponse> response = apiInstance.accountsWorkspaceMembersRemoveDeleteWithHttpInfo(workspaceId, workspaceMemberRemove);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsWorkspaceMembersRemoveDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **workspaceId** | **String**|  | |
| **workspaceMemberRemove** | [**WorkspaceMemberRemove**](WorkspaceMemberRemove.md)|  | |

### Return type

ApiResponse<[**MemberUserMutationResponse**](MemberUserMutationResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## accountsWorkspaceMembersRoleCreate

> WorkspaceMemberRoleUpdateResponse accountsWorkspaceMembersRoleCreate(workspaceId, workspaceMemberRoleUpdate)

POST /accounts/workspace/&lt;workspace_id&gt;/members/role/

Update a member&#39;s workspace role.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        WorkspaceMemberRoleUpdate workspaceMemberRoleUpdate = new WorkspaceMemberRoleUpdate(); // WorkspaceMemberRoleUpdate | 
        try {
            WorkspaceMemberRoleUpdateResponse result = apiInstance.accountsWorkspaceMembersRoleCreate(workspaceId, workspaceMemberRoleUpdate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsWorkspaceMembersRoleCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **workspaceId** | **String**|  | |
| **workspaceMemberRoleUpdate** | [**WorkspaceMemberRoleUpdate**](WorkspaceMemberRoleUpdate.md)|  | |

### Return type

[**WorkspaceMemberRoleUpdateResponse**](WorkspaceMemberRoleUpdateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## accountsWorkspaceMembersRoleCreateWithHttpInfo

> ApiResponse<WorkspaceMemberRoleUpdateResponse> accountsWorkspaceMembersRoleCreate accountsWorkspaceMembersRoleCreateWithHttpInfo(workspaceId, workspaceMemberRoleUpdate)

POST /accounts/workspace/&lt;workspace_id&gt;/members/role/

Update a member&#39;s workspace role.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.AccountsApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        AccountsApi apiInstance = new AccountsApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        WorkspaceMemberRoleUpdate workspaceMemberRoleUpdate = new WorkspaceMemberRoleUpdate(); // WorkspaceMemberRoleUpdate | 
        try {
            ApiResponse<WorkspaceMemberRoleUpdateResponse> response = apiInstance.accountsWorkspaceMembersRoleCreateWithHttpInfo(workspaceId, workspaceMemberRoleUpdate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling AccountsApi#accountsWorkspaceMembersRoleCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **workspaceId** | **String**|  | |
| **workspaceMemberRoleUpdate** | [**WorkspaceMemberRoleUpdate**](WorkspaceMemberRoleUpdate.md)|  | |

### Return type

ApiResponse<[**WorkspaceMemberRoleUpdateResponse**](WorkspaceMemberRoleUpdateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **401** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

