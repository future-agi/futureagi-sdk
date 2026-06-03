# \SimulationPersonasAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreatePersona**](SimulationPersonasAPI.md#CreatePersona) | **Post** /simulate/api/personas/ | 
[**DeletePersona**](SimulationPersonasAPI.md#DeletePersona) | **Delete** /simulate/api/personas/{id}/ | 
[**GetPersona**](SimulationPersonasAPI.md#GetPersona) | **Get** /simulate/api/personas/{id}/ | 
[**ListPersonas**](SimulationPersonasAPI.md#ListPersonas) | **Get** /simulate/api/personas/ | 
[**UpdatePersona**](SimulationPersonasAPI.md#UpdatePersona) | **Patch** /simulate/api/personas/{id}/ | 



## CreatePersona

> PersonaCreate CreatePersona(ctx).PersonaCreate(personaCreate).Execute()





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
	personaCreate := *openapiclient.NewPersonaCreate("Name_example", "Description_example") // PersonaCreate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationPersonasAPI.CreatePersona(context.Background()).PersonaCreate(personaCreate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationPersonasAPI.CreatePersona``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreatePersona`: PersonaCreate
	fmt.Fprintf(os.Stdout, "Response from `SimulationPersonasAPI.CreatePersona`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreatePersonaRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **personaCreate** | [**PersonaCreate**](PersonaCreate.md) |  | 

### Return type

[**PersonaCreate**](PersonaCreate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeletePersona

> DeletePersona(ctx, id).Execute()





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
	r, err := apiClient.SimulationPersonasAPI.DeletePersona(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationPersonasAPI.DeletePersona``: %v\n", err)
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

Other parameters are passed through a pointer to a apiDeletePersonaRequest struct via the builder pattern


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


## GetPersona

> Persona GetPersona(ctx, id).Execute()





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
	resp, r, err := apiClient.SimulationPersonasAPI.GetPersona(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationPersonasAPI.GetPersona``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetPersona`: Persona
	fmt.Fprintf(os.Stdout, "Response from `SimulationPersonasAPI.GetPersona`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetPersonaRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**Persona**](Persona.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListPersonas

> ListPersonas200Response ListPersonas(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.SimulationPersonasAPI.ListPersonas(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationPersonasAPI.ListPersonas``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListPersonas`: ListPersonas200Response
	fmt.Fprintf(os.Stdout, "Response from `SimulationPersonasAPI.ListPersonas`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListPersonasRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListPersonas200Response**](ListPersonas200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdatePersona

> Persona UpdatePersona(ctx, id).Persona(persona).Execute()





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
	persona := *openapiclient.NewPersona("Name_example") // Persona | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationPersonasAPI.UpdatePersona(context.Background(), id).Persona(persona).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationPersonasAPI.UpdatePersona``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdatePersona`: Persona
	fmt.Fprintf(os.Stdout, "Response from `SimulationPersonasAPI.UpdatePersona`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdatePersonaRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **persona** | [**Persona**](Persona.md) |  | 

### Return type

[**Persona**](Persona.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

