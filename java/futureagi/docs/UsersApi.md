# UsersApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getCurrentUser**](UsersApi.md#getCurrentUser) | **GET** /accounts/user-info/ |  |
| [**getCurrentUserWithHttpInfo**](UsersApi.md#getCurrentUserWithHttpInfo) | **GET** /accounts/user-info/ |  |
| [**listOrganizationMembers**](UsersApi.md#listOrganizationMembers) | **GET** /accounts/organization/members/ | GET /accounts/organization/members/ |
| [**listOrganizationMembersWithHttpInfo**](UsersApi.md#listOrganizationMembersWithHttpInfo) | **GET** /accounts/organization/members/ | GET /accounts/organization/members/ |
| [**listWorkspaceMembers**](UsersApi.md#listWorkspaceMembers) | **GET** /accounts/workspace/{workspace_id}/members/ | GET /accounts/workspace/&lt;workspace_id&gt;/members/ |
| [**listWorkspaceMembersWithHttpInfo**](UsersApi.md#listWorkspaceMembersWithHttpInfo) | **GET** /accounts/workspace/{workspace_id}/members/ | GET /accounts/workspace/&lt;workspace_id&gt;/members/ |
| [**listWorkspaces**](UsersApi.md#listWorkspaces) | **GET** /accounts/workspace/list/ |  |
| [**listWorkspacesWithHttpInfo**](UsersApi.md#listWorkspacesWithHttpInfo) | **GET** /accounts/workspace/list/ |  |
| [**switchWorkspace**](UsersApi.md#switchWorkspace) | **POST** /accounts/workspace/switch/ |  |
| [**switchWorkspaceWithHttpInfo**](UsersApi.md#switchWorkspaceWithHttpInfo) | **POST** /accounts/workspace/switch/ |  |



## getCurrentUser

> UserInfoResponse getCurrentUser()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        try {
            UserInfoResponse result = apiInstance.getCurrentUser();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#getCurrentUser");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**UserInfoResponse**](UserInfoResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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

## getCurrentUserWithHttpInfo

> ApiResponse<UserInfoResponse> getCurrentUser getCurrentUserWithHttpInfo()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        try {
            ApiResponse<UserInfoResponse> response = apiInstance.getCurrentUserWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#getCurrentUser");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

ApiResponse<[**UserInfoResponse**](UserInfoResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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


## listOrganizationMembers

> MemberListResponse listOrganizationMembers(page, limit, search, filterStatus, filterRole, sort)

GET /accounts/organization/members/

Returns UNION of active members + pending/expired invites. Status is derived at query time (Active / Pending / Expired).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        Integer page = 1; // Integer | 
        Integer limit = 20; // Integer | 
        String search = ""; // String | 
        List<String> filterStatus = Arrays.asList(); // List<String> | 
        List<String> filterRole = Arrays.asList(); // List<String> | 
        String sort = "name"; // String | 
        try {
            MemberListResponse result = apiInstance.listOrganizationMembers(page, limit, search, filterStatus, filterRole, sort);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listOrganizationMembers");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 20] |
| **search** | **String**|  | [optional] [default to ] |
| **filterStatus** | [**List&lt;String&gt;**](String.md)|  | [optional] [enum: Active, Pending, Expired, Deactivated] |
| **filterRole** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sort** | **String**|  | [optional] [default to -created_at] [enum: name, -name, email, -email, status, -status, type, -type, date_joined, -date_joined, created_at, -created_at, org_level, -org_level] |

### Return type

[**MemberListResponse**](MemberListResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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

## listOrganizationMembersWithHttpInfo

> ApiResponse<MemberListResponse> listOrganizationMembers listOrganizationMembersWithHttpInfo(page, limit, search, filterStatus, filterRole, sort)

GET /accounts/organization/members/

Returns UNION of active members + pending/expired invites. Status is derived at query time (Active / Pending / Expired).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        Integer page = 1; // Integer | 
        Integer limit = 20; // Integer | 
        String search = ""; // String | 
        List<String> filterStatus = Arrays.asList(); // List<String> | 
        List<String> filterRole = Arrays.asList(); // List<String> | 
        String sort = "name"; // String | 
        try {
            ApiResponse<MemberListResponse> response = apiInstance.listOrganizationMembersWithHttpInfo(page, limit, search, filterStatus, filterRole, sort);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listOrganizationMembers");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 20] |
| **search** | **String**|  | [optional] [default to ] |
| **filterStatus** | [**List&lt;String&gt;**](String.md)|  | [optional] [enum: Active, Pending, Expired, Deactivated] |
| **filterRole** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sort** | **String**|  | [optional] [default to -created_at] [enum: name, -name, email, -email, status, -status, type, -type, date_joined, -date_joined, created_at, -created_at, org_level, -org_level] |

### Return type

ApiResponse<[**MemberListResponse**](MemberListResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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


## listWorkspaceMembers

> MemberListResponse listWorkspaceMembers(workspaceId, page, limit, search, filterStatus, filterRole, sort)

GET /accounts/workspace/&lt;workspace_id&gt;/members/

Returns members of a specific workspace. Org Admin+ users who auto-access are included with derived WS Admin role.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 20; // Integer | 
        String search = ""; // String | 
        List<String> filterStatus = Arrays.asList(); // List<String> | 
        List<String> filterRole = Arrays.asList(); // List<String> | 
        String sort = "name"; // String | 
        try {
            MemberListResponse result = apiInstance.listWorkspaceMembers(workspaceId, page, limit, search, filterStatus, filterRole, sort);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listWorkspaceMembers");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 20] |
| **search** | **String**|  | [optional] [default to ] |
| **filterStatus** | [**List&lt;String&gt;**](String.md)|  | [optional] [enum: Active, Pending, Expired] |
| **filterRole** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sort** | **String**|  | [optional] [default to -created_at] [enum: name, -name, email, -email, status, -status, type, -type, date_joined, -date_joined, created_at, -created_at, ws_level, -ws_level] |

### Return type

[**MemberListResponse**](MemberListResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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

## listWorkspaceMembersWithHttpInfo

> ApiResponse<MemberListResponse> listWorkspaceMembers listWorkspaceMembersWithHttpInfo(workspaceId, page, limit, search, filterStatus, filterRole, sort)

GET /accounts/workspace/&lt;workspace_id&gt;/members/

Returns members of a specific workspace. Org Admin+ users who auto-access are included with derived WS Admin role.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        String workspaceId = "workspaceId_example"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 20; // Integer | 
        String search = ""; // String | 
        List<String> filterStatus = Arrays.asList(); // List<String> | 
        List<String> filterRole = Arrays.asList(); // List<String> | 
        String sort = "name"; // String | 
        try {
            ApiResponse<MemberListResponse> response = apiInstance.listWorkspaceMembersWithHttpInfo(workspaceId, page, limit, search, filterStatus, filterRole, sort);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listWorkspaceMembers");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 20] |
| **search** | **String**|  | [optional] [default to ] |
| **filterStatus** | [**List&lt;String&gt;**](String.md)|  | [optional] [enum: Active, Pending, Expired] |
| **filterRole** | [**List&lt;String&gt;**](String.md)|  | [optional] |
| **sort** | **String**|  | [optional] [default to -created_at] [enum: name, -name, email, -email, status, -status, type, -type, date_joined, -date_joined, created_at, -created_at, ws_level, -ws_level] |

### Return type

ApiResponse<[**MemberListResponse**](MemberListResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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


## listWorkspaces

> WorkspaceListPaginatedResponse listWorkspaces(page, limit, search, sort)



Get paginated list of workspaces

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        Integer page = 1; // Integer | 
        Integer limit = 10; // Integer | 
        String search = ""; // String | 
        String sort = ""; // String | 
        try {
            WorkspaceListPaginatedResponse result = apiInstance.listWorkspaces(page, limit, search, sort);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listWorkspaces");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 10] |
| **search** | **String**|  | [optional] [default to ] |
| **sort** | **String**|  | [optional] [default to ] |

### Return type

[**WorkspaceListPaginatedResponse**](WorkspaceListPaginatedResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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

## listWorkspacesWithHttpInfo

> ApiResponse<WorkspaceListPaginatedResponse> listWorkspaces listWorkspacesWithHttpInfo(page, limit, search, sort)



Get paginated list of workspaces

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        Integer page = 1; // Integer | 
        Integer limit = 10; // Integer | 
        String search = ""; // String | 
        String sort = ""; // String | 
        try {
            ApiResponse<WorkspaceListPaginatedResponse> response = apiInstance.listWorkspacesWithHttpInfo(page, limit, search, sort);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#listWorkspaces");
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
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] [default to 10] |
| **search** | **String**|  | [optional] [default to ] |
| **sort** | **String**|  | [optional] [default to ] |

### Return type

ApiResponse<[**WorkspaceListPaginatedResponse**](WorkspaceListPaginatedResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
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


## switchWorkspace

> SwitchWorkspaceResponse switchWorkspace(switchWorkspace)



Switch to a different workspace with proper validation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        SwitchWorkspace switchWorkspace = new SwitchWorkspace(); // SwitchWorkspace | 
        try {
            SwitchWorkspaceResponse result = apiInstance.switchWorkspace(switchWorkspace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#switchWorkspace");
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
| **switchWorkspace** | [**SwitchWorkspace**](SwitchWorkspace.md)|  | |

### Return type

[**SwitchWorkspaceResponse**](SwitchWorkspaceResponse.md)


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

## switchWorkspaceWithHttpInfo

> ApiResponse<SwitchWorkspaceResponse> switchWorkspace switchWorkspaceWithHttpInfo(switchWorkspace)



Switch to a different workspace with proper validation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.UsersApi;

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

        UsersApi apiInstance = new UsersApi(defaultClient);
        SwitchWorkspace switchWorkspace = new SwitchWorkspace(); // SwitchWorkspace | 
        try {
            ApiResponse<SwitchWorkspaceResponse> response = apiInstance.switchWorkspaceWithHttpInfo(switchWorkspace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling UsersApi#switchWorkspace");
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
| **switchWorkspace** | [**SwitchWorkspace**](SwitchWorkspace.md)|  | |

### Return type

ApiResponse<[**SwitchWorkspaceResponse**](SwitchWorkspaceResponse.md)>


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

