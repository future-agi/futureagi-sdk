# \ModelHubAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ModelHubAnnotationQueuesAutomationRulesCreate**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesCreate) | **Post** /model-hub/annotation-queues/{queue_id}/automation-rules/ | 
[**ModelHubAnnotationQueuesAutomationRulesDelete**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesDelete) | **Delete** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/ | 
[**ModelHubAnnotationQueuesAutomationRulesEvaluate**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesEvaluate) | **Post** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/evaluate/ | Trigger a manual rule run with a sync-or-async branch.
[**ModelHubAnnotationQueuesAutomationRulesList**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesList) | **Get** /model-hub/annotation-queues/{queue_id}/automation-rules/ | 
[**ModelHubAnnotationQueuesAutomationRulesPartialUpdate**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesPartialUpdate) | **Patch** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/ | 
[**ModelHubAnnotationQueuesAutomationRulesPreview**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesPreview) | **Get** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/preview/ | 
[**ModelHubAnnotationQueuesAutomationRulesRead**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesRead) | **Get** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/ | 
[**ModelHubAnnotationQueuesAutomationRulesUpdate**](ModelHubAPI.md#ModelHubAnnotationQueuesAutomationRulesUpdate) | **Put** /model-hub/annotation-queues/{queue_id}/automation-rules/{id}/ | 
[**ModelHubAnnotationQueuesForSource**](ModelHubAPI.md#ModelHubAnnotationQueuesForSource) | **Get** /model-hub/annotation-queues/for-source/ | 
[**ModelHubAnnotationQueuesGetOrCreateDefault**](ModelHubAPI.md#ModelHubAnnotationQueuesGetOrCreateDefault) | **Post** /model-hub/annotation-queues/get-or-create-default/ | 
[**ModelHubAnnotationQueuesHardDelete**](ModelHubAPI.md#ModelHubAnnotationQueuesHardDelete) | **Post** /model-hub/annotation-queues/{id}/hard-delete/ | Permanently remove a queue + everything attached.
[**ModelHubAnnotationQueuesItemsCreate**](ModelHubAPI.md#ModelHubAnnotationQueuesItemsCreate) | **Post** /model-hub/annotation-queues/{queue_id}/items/ | 
[**ModelHubAnnotationQueuesItemsDelete**](ModelHubAPI.md#ModelHubAnnotationQueuesItemsDelete) | **Delete** /model-hub/annotation-queues/{queue_id}/items/{id}/ | 
[**ModelHubAnnotationQueuesItemsPartialUpdate**](ModelHubAPI.md#ModelHubAnnotationQueuesItemsPartialUpdate) | **Patch** /model-hub/annotation-queues/{queue_id}/items/{id}/ | 
[**ModelHubAnnotationQueuesItemsRead**](ModelHubAPI.md#ModelHubAnnotationQueuesItemsRead) | **Get** /model-hub/annotation-queues/{queue_id}/items/{id}/ | 
[**ModelHubAnnotationQueuesItemsUpdate**](ModelHubAPI.md#ModelHubAnnotationQueuesItemsUpdate) | **Put** /model-hub/annotation-queues/{queue_id}/items/{id}/ | 
[**ModelHubAnnotationQueuesRestore**](ModelHubAPI.md#ModelHubAnnotationQueuesRestore) | **Post** /model-hub/annotation-queues/{id}/restore/ | 
[**ModelHubAnnotationQueuesUpdate**](ModelHubAPI.md#ModelHubAnnotationQueuesUpdate) | **Put** /model-hub/annotation-queues/{id}/ | 
[**ModelHubAnnotationsLabelsCreate**](ModelHubAPI.md#ModelHubAnnotationsLabelsCreate) | **Post** /model-hub/annotations-labels/ | 
[**ModelHubAnnotationsLabelsDelete**](ModelHubAPI.md#ModelHubAnnotationsLabelsDelete) | **Delete** /model-hub/annotations-labels/{id}/ | 
[**ModelHubAnnotationsLabelsList**](ModelHubAPI.md#ModelHubAnnotationsLabelsList) | **Get** /model-hub/annotations-labels/ | 
[**ModelHubAnnotationsLabelsPartialUpdate**](ModelHubAPI.md#ModelHubAnnotationsLabelsPartialUpdate) | **Patch** /model-hub/annotations-labels/{id}/ | 
[**ModelHubAnnotationsLabelsRead**](ModelHubAPI.md#ModelHubAnnotationsLabelsRead) | **Get** /model-hub/annotations-labels/{id}/ | 
[**ModelHubAnnotationsLabelsRestore**](ModelHubAPI.md#ModelHubAnnotationsLabelsRestore) | **Post** /model-hub/annotations-labels/{id}/restore/ | 
[**ModelHubAnnotationsLabelsUpdate**](ModelHubAPI.md#ModelHubAnnotationsLabelsUpdate) | **Put** /model-hub/annotations-labels/{id}/ | 
[**ModelHubApiKeysCreate**](ModelHubAPI.md#ModelHubApiKeysCreate) | **Post** /model-hub/api-keys/ | 
[**ModelHubApiKeysDelete**](ModelHubAPI.md#ModelHubApiKeysDelete) | **Delete** /model-hub/api-keys/{id}/ | Soft-delete an API key.
[**ModelHubApiKeysList**](ModelHubAPI.md#ModelHubApiKeysList) | **Get** /model-hub/api-keys/ | 
[**ModelHubApiKeysPartialUpdate**](ModelHubAPI.md#ModelHubApiKeysPartialUpdate) | **Patch** /model-hub/api-keys/{id}/ | 
[**ModelHubApiKeysRead**](ModelHubAPI.md#ModelHubApiKeysRead) | **Get** /model-hub/api-keys/{id}/ | 
[**ModelHubApiKeysUpdate**](ModelHubAPI.md#ModelHubApiKeysUpdate) | **Put** /model-hub/api-keys/{id}/ | 
[**ModelHubApiModelsListList**](ModelHubAPI.md#ModelHubApiModelsListList) | **Get** /model-hub/api/models_list/ | 
[**ModelHubDatasetRunPromptStatsList**](ModelHubAPI.md#ModelHubDatasetRunPromptStatsList) | **Get** /model-hub/dataset/{dataset_id}/run-prompt-stats/ | 
[**ModelHubDatasetsAddApiColumnCreate**](ModelHubAPI.md#ModelHubDatasetsAddApiColumnCreate) | **Post** /model-hub/datasets/{dataset_id}/add-api-column/ | 
[**ModelHubDatasetsAddVectorDbColumnCreate**](ModelHubAPI.md#ModelHubDatasetsAddVectorDbColumnCreate) | **Post** /model-hub/datasets/{dataset_id}/add_vector_db_column/ | 
[**ModelHubDatasetsClassifyColumnCreate**](ModelHubAPI.md#ModelHubDatasetsClassifyColumnCreate) | **Post** /model-hub/datasets/{dataset_id}/classify-column/ | 
[**ModelHubDatasetsCompareDatasetsAddEvalCreate**](ModelHubAPI.md#ModelHubDatasetsCompareDatasetsAddEvalCreate) | **Post** /model-hub/datasets/{dataset_id}/compare-datasets/add-eval/ | 
[**ModelHubDatasetsCompareDatasetsCreate**](ModelHubAPI.md#ModelHubDatasetsCompareDatasetsCreate) | **Post** /model-hub/datasets/{dataset_id}/compare-datasets/ | 
[**ModelHubDatasetsCompareDatasetsDownloadCreate**](ModelHubAPI.md#ModelHubDatasetsCompareDatasetsDownloadCreate) | **Post** /model-hub/datasets/{dataset_id}/compare-datasets/download/ | 
[**ModelHubDatasetsCompareDatasetsStartEvalCreate**](ModelHubAPI.md#ModelHubDatasetsCompareDatasetsStartEvalCreate) | **Post** /model-hub/datasets/{dataset_id}/compare-datasets/start-eval/ | 
[**ModelHubDatasetsCompareGetEvalsListCreate**](ModelHubAPI.md#ModelHubDatasetsCompareGetEvalsListCreate) | **Post** /model-hub/datasets/compare/get-evals-list/ | 
[**ModelHubDatasetsComparePreviewRunEvalCreate**](ModelHubAPI.md#ModelHubDatasetsComparePreviewRunEvalCreate) | **Post** /model-hub/datasets/compare/preview-run-eval/ | 
[**ModelHubDatasetsCompareStatsCreate**](ModelHubAPI.md#ModelHubDatasetsCompareStatsCreate) | **Post** /model-hub/datasets/{dataset_id}/compare-stats/ | 
[**ModelHubDatasetsConditionalColumnCreate**](ModelHubAPI.md#ModelHubDatasetsConditionalColumnCreate) | **Post** /model-hub/datasets/{dataset_id}/conditional-column/ | 
[**ModelHubDatasetsDeleteCompareDelete**](ModelHubAPI.md#ModelHubDatasetsDeleteCompareDelete) | **Delete** /model-hub/datasets/delete-compare/{compare_id}/ | 
[**ModelHubDatasetsDeleteCompareRead**](ModelHubAPI.md#ModelHubDatasetsDeleteCompareRead) | **Get** /model-hub/datasets/delete-compare/{compare_id}/ | 
[**ModelHubDatasetsDuplicateRowsCreate**](ModelHubAPI.md#ModelHubDatasetsDuplicateRowsCreate) | **Post** /model-hub/datasets/{dataset_id}/duplicate-rows/ | 
[**ModelHubDatasetsExplanationSummaryRead**](ModelHubAPI.md#ModelHubDatasetsExplanationSummaryRead) | **Get** /model-hub/datasets/explanation-summary/{dataset_id}/ | 
[**ModelHubDatasetsExplanationSummaryRefreshCreate**](ModelHubAPI.md#ModelHubDatasetsExplanationSummaryRefreshCreate) | **Post** /model-hub/datasets/explanation-summary/{dataset_id}/refresh/ | 
[**ModelHubDatasetsExtractEntitiesCreate**](ModelHubAPI.md#ModelHubDatasetsExtractEntitiesCreate) | **Post** /model-hub/datasets/{dataset_id}/extract-entities/ | 
[**ModelHubDatasetsGetCompareRowDelete**](ModelHubAPI.md#ModelHubDatasetsGetCompareRowDelete) | **Delete** /model-hub/datasets/get-compare-row/{compare_id}/{row_id}/ | 
[**ModelHubDatasetsGetCompareRowRead**](ModelHubAPI.md#ModelHubDatasetsGetCompareRowRead) | **Get** /model-hub/datasets/get-compare-row/{compare_id}/{row_id}/ | 
[**ModelHubDatasetsHuggingfaceDetailCreate**](ModelHubAPI.md#ModelHubDatasetsHuggingfaceDetailCreate) | **Post** /model-hub/datasets/huggingface/detail/ | 
[**ModelHubDatasetsHuggingfaceListCreate**](ModelHubAPI.md#ModelHubDatasetsHuggingfaceListCreate) | **Post** /model-hub/datasets/huggingface/list/ | 
[**ModelHubDatasetsMergeCreate**](ModelHubAPI.md#ModelHubDatasetsMergeCreate) | **Post** /model-hub/datasets/{dataset_id}/merge/ | 
[**ModelHubDatasetsPreviewCreate**](ModelHubAPI.md#ModelHubDatasetsPreviewCreate) | **Post** /model-hub/datasets/{dataset_id}/preview/{operation_type}/ | 
[**ModelHubDeleteEvalTemplateCreate**](ModelHubAPI.md#ModelHubDeleteEvalTemplateCreate) | **Post** /model-hub/delete-eval-template/ | 
[**ModelHubDevelopsAddAsNewCreate**](ModelHubAPI.md#ModelHubDevelopsAddAsNewCreate) | **Post** /model-hub/develops/add-as-new/ | 
[**ModelHubDevelopsAddEmptyColumnsCreate**](ModelHubAPI.md#ModelHubDevelopsAddEmptyColumnsCreate) | **Post** /model-hub/develops/{dataset_id}/add_empty_columns/ | 
[**ModelHubDevelopsAddEmptyRowsCreate**](ModelHubAPI.md#ModelHubDevelopsAddEmptyRowsCreate) | **Post** /model-hub/develops/{dataset_id}/add_empty_rows/ | 
[**ModelHubDevelopsAddMultipleStaticColumnsCreate**](ModelHubAPI.md#ModelHubDevelopsAddMultipleStaticColumnsCreate) | **Post** /model-hub/develops/{dataset_id}/add_multiple_static_columns/ | Add multiple static columns to a dataset at once.
[**ModelHubDevelopsAddRowsFromExistingDatasetCreate**](ModelHubAPI.md#ModelHubDevelopsAddRowsFromExistingDatasetCreate) | **Post** /model-hub/develops/{dataset_id}/add_rows_from_existing_dataset/ | 
[**ModelHubDevelopsAddRowsFromFileCreate**](ModelHubAPI.md#ModelHubDevelopsAddRowsFromFileCreate) | **Post** /model-hub/develops/add_rows_from_file/ | 
[**ModelHubDevelopsAddRowsFromHuggingfaceCreate**](ModelHubAPI.md#ModelHubDevelopsAddRowsFromHuggingfaceCreate) | **Post** /model-hub/develops/{dataset_id}/add_rows_from_huggingface/ | 
[**ModelHubDevelopsAddRowsSdkCreate**](ModelHubAPI.md#ModelHubDevelopsAddRowsSdkCreate) | **Post** /model-hub/develops/add_rows_sdk/ | 
[**ModelHubDevelopsAddRunPromptColumnCreate**](ModelHubAPI.md#ModelHubDevelopsAddRunPromptColumnCreate) | **Post** /model-hub/develops/add_run_prompt_column/ | 
[**ModelHubDevelopsAddStaticColumnCreate**](ModelHubAPI.md#ModelHubDevelopsAddStaticColumnCreate) | **Post** /model-hub/develops/{dataset_id}/add_static_column/ | 
[**ModelHubDevelopsAddSyntheticDataCreate**](ModelHubAPI.md#ModelHubDevelopsAddSyntheticDataCreate) | **Post** /model-hub/develops/{dataset_id}/add_synthetic_data/ | 
[**ModelHubDevelopsAddUserEvalCreate**](ModelHubAPI.md#ModelHubDevelopsAddUserEvalCreate) | **Post** /model-hub/develops/{dataset_id}/add_user_eval/ | 
[**ModelHubDevelopsCloneDatasetCreate**](ModelHubAPI.md#ModelHubDevelopsCloneDatasetCreate) | **Post** /model-hub/develops/clone-dataset/{dataset_id}/ | 
[**ModelHubDevelopsCreateDatasetCreate**](ModelHubAPI.md#ModelHubDevelopsCreateDatasetCreate) | **Post** /model-hub/develops/{exp_dataset_id}/create-dataset/ | 
[**ModelHubDevelopsCreateDatasetFromHuggingfaceCreate**](ModelHubAPI.md#ModelHubDevelopsCreateDatasetFromHuggingfaceCreate) | **Post** /model-hub/develops/create-dataset-from-huggingface/ | 
[**ModelHubDevelopsCreateSyntheticDatasetCreate**](ModelHubAPI.md#ModelHubDevelopsCreateSyntheticDatasetCreate) | **Post** /model-hub/develops/create-synthetic-dataset/ | 
[**ModelHubDevelopsDatasetCreationProgressRead**](ModelHubAPI.md#ModelHubDevelopsDatasetCreationProgressRead) | **Get** /model-hub/develops/dataset-creation-progress/{dataset_id}/ | 
[**ModelHubDevelopsDeleteDatasetDelete**](ModelHubAPI.md#ModelHubDevelopsDeleteDatasetDelete) | **Delete** /model-hub/develops/delete_dataset/ | 
[**ModelHubDevelopsDeleteTemplateEvalDelete**](ModelHubAPI.md#ModelHubDevelopsDeleteTemplateEvalDelete) | **Delete** /model-hub/develops/{dataset_id}/delete_template_eval/{eval_id}/ | 
[**ModelHubDevelopsDeleteUserEvalDelete**](ModelHubAPI.md#ModelHubDevelopsDeleteUserEvalDelete) | **Delete** /model-hub/develops/{dataset_id}/delete_user_eval/{eval_id}/ | 
[**ModelHubDevelopsEditAndRunUserEvalCreate**](ModelHubAPI.md#ModelHubDevelopsEditAndRunUserEvalCreate) | **Post** /model-hub/develops/{dataset_id}/edit_and_run_user_eval/{eval_id}/ | 
[**ModelHubDevelopsEditDatasetBehaviorUpdate**](ModelHubAPI.md#ModelHubDevelopsEditDatasetBehaviorUpdate) | **Put** /model-hub/develops/{dataset_id}/edit_dataset_behavior/ | 
[**ModelHubDevelopsEditRunPromptColumnCreate**](ModelHubAPI.md#ModelHubDevelopsEditRunPromptColumnCreate) | **Post** /model-hub/develops/edit_run_prompt_column/ | 
[**ModelHubDevelopsExtractJsonColumnCreate**](ModelHubAPI.md#ModelHubDevelopsExtractJsonColumnCreate) | **Post** /model-hub/develops/{dataset_id}/extract-json-column/ | 
[**ModelHubDevelopsGetCellDataCreate**](ModelHubAPI.md#ModelHubDevelopsGetCellDataCreate) | **Post** /model-hub/develops/get-cell-data/ | 
[**ModelHubDevelopsGetDerivedDatasetsRead**](ModelHubAPI.md#ModelHubDevelopsGetDerivedDatasetsRead) | **Get** /model-hub/develops/get-derived-datasets/{dataset_id}/ | 
[**ModelHubDevelopsGetEvalStructureRead**](ModelHubAPI.md#ModelHubDevelopsGetEvalStructureRead) | **Get** /model-hub/develops/{dataset_id}/get_eval_structure/{eval_id}/ | 
[**ModelHubDevelopsGetEvalsListList**](ModelHubAPI.md#ModelHubDevelopsGetEvalsListList) | **Get** /model-hub/develops/{dataset_id}/get_evals_list/ | 
[**ModelHubDevelopsGetExperimentDatasetTableList**](ModelHubAPI.md#ModelHubDevelopsGetExperimentDatasetTableList) | **Get** /model-hub/develops/{experiment_dataset_id}/get-experiment-dataset-table/ | 
[**ModelHubDevelopsGetFunctionListList**](ModelHubAPI.md#ModelHubDevelopsGetFunctionListList) | **Get** /model-hub/develops/get_function_list/ | 
[**ModelHubDevelopsGetHuggingfaceDatasetConfigCreate**](ModelHubAPI.md#ModelHubDevelopsGetHuggingfaceDatasetConfigCreate) | **Post** /model-hub/develops/get-huggingface-dataset-config/ | 
[**ModelHubDevelopsGetRowDiffCreate**](ModelHubAPI.md#ModelHubDevelopsGetRowDiffCreate) | **Post** /model-hub/develops/get-row-diff/ | 
[**ModelHubDevelopsPreviewRunEvalCreate**](ModelHubAPI.md#ModelHubDevelopsPreviewRunEvalCreate) | **Post** /model-hub/develops/{dataset_id}/preview_run_eval/ | 
[**ModelHubDevelopsPreviewRunPromptColumnCreate**](ModelHubAPI.md#ModelHubDevelopsPreviewRunPromptColumnCreate) | **Post** /model-hub/develops/preview_run_prompt_column/ | 
[**ModelHubDevelopsProviderStatusList**](ModelHubAPI.md#ModelHubDevelopsProviderStatusList) | **Get** /model-hub/develops/provider-status/ | 
[**ModelHubDevelopsRetrieveRunPromptColumnConfigList**](ModelHubAPI.md#ModelHubDevelopsRetrieveRunPromptColumnConfigList) | **Get** /model-hub/develops/retrieve_run_prompt_column_config/ | 
[**ModelHubDevelopsRetrieveRunPromptOptionsList**](ModelHubAPI.md#ModelHubDevelopsRetrieveRunPromptOptionsList) | **Get** /model-hub/develops/retrieve_run_prompt_options/ | 
[**ModelHubDevelopsStartEvalsProcessCreate**](ModelHubAPI.md#ModelHubDevelopsStartEvalsProcessCreate) | **Post** /model-hub/develops/{dataset_id}/start_evals_process/ | 
[**ModelHubDevelopsStopUserEvalCreate**](ModelHubAPI.md#ModelHubDevelopsStopUserEvalCreate) | **Post** /model-hub/develops/{dataset_id}/stop_user_eval/{eval_id}/ | POST /develops/&lt;dataset_id&gt;/stop_user_eval/&lt;eval_id&gt;/ Stops a running evaluation by setting its status to Completed.
[**ModelHubDevelopsSyntheticConfigList**](ModelHubAPI.md#ModelHubDevelopsSyntheticConfigList) | **Get** /model-hub/develops/{dataset_id}/synthetic-config/ | 
[**ModelHubDevelopsUpdateColumnNameUpdate**](ModelHubAPI.md#ModelHubDevelopsUpdateColumnNameUpdate) | **Put** /model-hub/develops/{dataset_id}/update_column_name/{column_id}/ | 
[**ModelHubDevelopsUpdateColumnTypeUpdate**](ModelHubAPI.md#ModelHubDevelopsUpdateColumnTypeUpdate) | **Put** /model-hub/develops/{dataset_id}/update_column_type/{column_id}/ | 
[**ModelHubDevelopsUpdateSyntheticConfigUpdate**](ModelHubAPI.md#ModelHubDevelopsUpdateSyntheticConfigUpdate) | **Put** /model-hub/develops/{dataset_id}/update-synthetic-config/ | 
[**ModelHubEvalTemplatesBulkDeleteCreate**](ModelHubAPI.md#ModelHubEvalTemplatesBulkDeleteCreate) | **Post** /model-hub/eval-templates/bulk-delete/ | POST /model-hub/eval-templates/bulk-delete/
[**ModelHubEvalTemplatesCompositeExecuteAdhocCreate**](ModelHubAPI.md#ModelHubEvalTemplatesCompositeExecuteAdhocCreate) | **Post** /model-hub/eval-templates/composite/execute-adhoc/ | POST /model-hub/eval-templates/composite/execute-adhoc/
[**ModelHubEvalTemplatesCompositeExecuteCreate**](ModelHubAPI.md#ModelHubEvalTemplatesCompositeExecuteCreate) | **Post** /model-hub/eval-templates/{template_id}/composite/execute/ | POST /model-hub/eval-templates/&lt;template_id&gt;/composite/execute/
[**ModelHubEvalTemplatesCompositeList**](ModelHubAPI.md#ModelHubEvalTemplatesCompositeList) | **Get** /model-hub/eval-templates/{template_id}/composite/ | GET /model-hub/eval-templates/&lt;id&gt;/composite/
[**ModelHubEvalTemplatesCompositePartialUpdate**](ModelHubAPI.md#ModelHubEvalTemplatesCompositePartialUpdate) | **Patch** /model-hub/eval-templates/{template_id}/composite/ | PATCH — partial update of a composite eval.
[**ModelHubEvalTemplatesCreateCompositeCreate**](ModelHubAPI.md#ModelHubEvalTemplatesCreateCompositeCreate) | **Post** /model-hub/eval-templates/create-composite/ | POST /model-hub/eval-templates/create-composite/
[**ModelHubEvalTemplatesCreateV2Create**](ModelHubAPI.md#ModelHubEvalTemplatesCreateV2Create) | **Post** /model-hub/eval-templates/create-v2/ | POST /model-hub/eval-templates/create-v2/
[**ModelHubEvalTemplatesDetailList**](ModelHubAPI.md#ModelHubEvalTemplatesDetailList) | **Get** /model-hub/eval-templates/{template_id}/detail/ | GET /model-hub/eval-templates/&lt;id&gt;/detail/
[**ModelHubEvalTemplatesFeedbackListList**](ModelHubAPI.md#ModelHubEvalTemplatesFeedbackListList) | **Get** /model-hub/eval-templates/{template_id}/feedback-list/ | GET /model-hub/eval-templates/&lt;id&gt;/feedback-list/
[**ModelHubEvalTemplatesGroundTruthConfigList**](ModelHubAPI.md#ModelHubEvalTemplatesGroundTruthConfigList) | **Get** /model-hub/eval-templates/{template_id}/ground-truth-config/ | GET/PUT /model-hub/eval-templates/&lt;id&gt;/ground-truth-config/
[**ModelHubEvalTemplatesGroundTruthConfigUpdate**](ModelHubAPI.md#ModelHubEvalTemplatesGroundTruthConfigUpdate) | **Put** /model-hub/eval-templates/{template_id}/ground-truth-config/ | GET/PUT /model-hub/eval-templates/&lt;id&gt;/ground-truth-config/
[**ModelHubEvalTemplatesGroundTruthList**](ModelHubAPI.md#ModelHubEvalTemplatesGroundTruthList) | **Get** /model-hub/eval-templates/{template_id}/ground-truth/ | 
[**ModelHubEvalTemplatesGroundTruthUploadCreate**](ModelHubAPI.md#ModelHubEvalTemplatesGroundTruthUploadCreate) | **Post** /model-hub/eval-templates/{template_id}/ground-truth/upload/ | POST /model-hub/eval-templates/&lt;id&gt;/ground-truth/upload/
[**ModelHubEvalTemplatesListChartsCreate**](ModelHubAPI.md#ModelHubEvalTemplatesListChartsCreate) | **Post** /model-hub/eval-templates/list-charts/ | POST /model-hub/eval-templates/list-charts/
[**ModelHubEvalTemplatesListCreate**](ModelHubAPI.md#ModelHubEvalTemplatesListCreate) | **Post** /model-hub/eval-templates/list/ | POST /model-hub/eval-templates/list/
[**ModelHubEvalTemplatesUpdateUpdate**](ModelHubAPI.md#ModelHubEvalTemplatesUpdateUpdate) | **Put** /model-hub/eval-templates/{template_id}/update/ | PUT /model-hub/eval-templates/&lt;id&gt;/update/
[**ModelHubEvalTemplatesUsageList**](ModelHubAPI.md#ModelHubEvalTemplatesUsageList) | **Get** /model-hub/eval-templates/{template_id}/usage/ | GET /model-hub/eval-templates/&lt;id&gt;/usage/
[**ModelHubEvalTemplatesVersionsCreateCreate**](ModelHubAPI.md#ModelHubEvalTemplatesVersionsCreateCreate) | **Post** /model-hub/eval-templates/{template_id}/versions/create/ | POST /model-hub/eval-templates/&lt;id&gt;/versions/create/
[**ModelHubEvalTemplatesVersionsList**](ModelHubAPI.md#ModelHubEvalTemplatesVersionsList) | **Get** /model-hub/eval-templates/{template_id}/versions/ | GET /model-hub/eval-templates/&lt;id&gt;/versions/
[**ModelHubEvalTemplatesVersionsRestoreCreate**](ModelHubAPI.md#ModelHubEvalTemplatesVersionsRestoreCreate) | **Post** /model-hub/eval-templates/{template_id}/versions/{version_id}/restore/ | POST /model-hub/eval-templates/&lt;id&gt;/versions/&lt;version_id&gt;/restore/
[**ModelHubEvalTemplatesVersionsSetDefaultUpdate**](ModelHubAPI.md#ModelHubEvalTemplatesVersionsSetDefaultUpdate) | **Put** /model-hub/eval-templates/{template_id}/versions/{version_id}/set-default/ | PUT /model-hub/eval-templates/&lt;id&gt;/versions/&lt;version_id&gt;/set-default/
[**ModelHubExperimentsV2DerivedVariablesList**](ModelHubAPI.md#ModelHubExperimentsV2DerivedVariablesList) | **Get** /model-hub/experiments/v2/{experiment_id}/derived-variables/ | 
[**ModelHubExperimentsV2EvaluationsStatsList**](ModelHubAPI.md#ModelHubExperimentsV2EvaluationsStatsList) | **Get** /model-hub/experiments/v2/{experiment_id}/evaluations/{evaluation_id}/stats/ | 
[**ModelHubExperimentsV2FeedbackCreate**](ModelHubAPI.md#ModelHubExperimentsV2FeedbackCreate) | **Post** /model-hub/experiments/v2/{experiment_id}/feedback/ | 
[**ModelHubExperimentsV2FeedbackGetFeedbackDetailsList**](ModelHubAPI.md#ModelHubExperimentsV2FeedbackGetFeedbackDetailsList) | **Get** /model-hub/experiments/v2/{experiment_id}/feedback/get-feedback-details/ | 
[**ModelHubExperimentsV2FeedbackGetTemplateList**](ModelHubAPI.md#ModelHubExperimentsV2FeedbackGetTemplateList) | **Get** /model-hub/experiments/v2/{experiment_id}/feedback/get-template/ | 
[**ModelHubExperimentsV2FeedbackSubmitFeedbackCreate**](ModelHubAPI.md#ModelHubExperimentsV2FeedbackSubmitFeedbackCreate) | **Post** /model-hub/experiments/v2/{experiment_id}/feedback/submit-feedback/ | 
[**ModelHubExperimentsV2RerunCellsCreate**](ModelHubAPI.md#ModelHubExperimentsV2RerunCellsCreate) | **Post** /model-hub/experiments/v2/{experiment_id}/rerun-cells/ | Rerun specific cells or columns in a V2 experiment.
[**ModelHubExperimentsV2RowDiffCreate**](ModelHubAPI.md#ModelHubExperimentsV2RowDiffCreate) | **Post** /model-hub/experiments/v2/row-diff/ | 
[**ModelHubExperimentsV2SuggestNameRead**](ModelHubAPI.md#ModelHubExperimentsV2SuggestNameRead) | **Get** /model-hub/experiments/v2/suggest-name/{dataset_id}/ | 
[**ModelHubExperimentsV2ValidateNameList**](ModelHubAPI.md#ModelHubExperimentsV2ValidateNameList) | **Get** /model-hub/experiments/v2/validate-name/ | 
[**ModelHubKnowledgeBaseCreate**](ModelHubAPI.md#ModelHubKnowledgeBaseCreate) | **Post** /model-hub/knowledge-base/ | 
[**ModelHubKnowledgeBaseDelete**](ModelHubAPI.md#ModelHubKnowledgeBaseDelete) | **Delete** /model-hub/knowledge-base/ | 
[**ModelHubKnowledgeBaseFilesCreate**](ModelHubAPI.md#ModelHubKnowledgeBaseFilesCreate) | **Post** /model-hub/knowledge-base/files/ | 
[**ModelHubKnowledgeBaseFilesDelete**](ModelHubAPI.md#ModelHubKnowledgeBaseFilesDelete) | **Delete** /model-hub/knowledge-base/files/ | 
[**ModelHubKnowledgeBaseGetList**](ModelHubAPI.md#ModelHubKnowledgeBaseGetList) | **Get** /model-hub/knowledge-base/get/ | 
[**ModelHubKnowledgeBaseList**](ModelHubAPI.md#ModelHubKnowledgeBaseList) | **Get** /model-hub/knowledge-base/ | 
[**ModelHubKnowledgeBaseListList**](ModelHubAPI.md#ModelHubKnowledgeBaseListList) | **Get** /model-hub/knowledge-base/list/ | 
[**ModelHubKnowledgeBasePartialUpdate**](ModelHubAPI.md#ModelHubKnowledgeBasePartialUpdate) | **Patch** /model-hub/knowledge-base/ | 
[**ModelHubPromptHistoryExecutionsGetExecutionDetails**](ModelHubAPI.md#ModelHubPromptHistoryExecutionsGetExecutionDetails) | **Get** /model-hub/prompt-history-executions/execution-details/{execution_id}/ | 
[**ModelHubPromptHistoryExecutionsList**](ModelHubAPI.md#ModelHubPromptHistoryExecutionsList) | **Get** /model-hub/prompt-history-executions/ | 
[**ModelHubPromptHistoryExecutionsRead**](ModelHubAPI.md#ModelHubPromptHistoryExecutionsRead) | **Get** /model-hub/prompt-history-executions/{id}/ | 
[**ModelHubPromptLabelsAssignLabelById**](ModelHubAPI.md#ModelHubPromptLabelsAssignLabelById) | **Post** /model-hub/prompt-labels/{template_id}/{label_id}/assign-label-by-id/ | 
[**ModelHubPromptLabelsAssignMultipleLabels**](ModelHubAPI.md#ModelHubPromptLabelsAssignMultipleLabels) | **Post** /model-hub/prompt-labels/assign-multiple-labels/ | 
[**ModelHubPromptLabelsCreate**](ModelHubAPI.md#ModelHubPromptLabelsCreate) | **Post** /model-hub/prompt-labels/ | 
[**ModelHubPromptLabelsCreateSystemLabels**](ModelHubAPI.md#ModelHubPromptLabelsCreateSystemLabels) | **Post** /model-hub/prompt-labels/create-system-labels/ | 
[**ModelHubPromptLabelsDelete**](ModelHubAPI.md#ModelHubPromptLabelsDelete) | **Delete** /model-hub/prompt-labels/{id}/ | 
[**ModelHubPromptLabelsGetByName**](ModelHubAPI.md#ModelHubPromptLabelsGetByName) | **Get** /model-hub/prompt-labels/get-by-name/ | Fetch a prompt version by template name and either explicit version or label.
[**ModelHubPromptLabelsList**](ModelHubAPI.md#ModelHubPromptLabelsList) | **Get** /model-hub/prompt-labels/ | 
[**ModelHubPromptLabelsPartialUpdate**](ModelHubAPI.md#ModelHubPromptLabelsPartialUpdate) | **Patch** /model-hub/prompt-labels/{id}/ | 
[**ModelHubPromptLabelsRead**](ModelHubAPI.md#ModelHubPromptLabelsRead) | **Get** /model-hub/prompt-labels/{id}/ | 
[**ModelHubPromptLabelsRemoveLabelFromVersion**](ModelHubAPI.md#ModelHubPromptLabelsRemoveLabelFromVersion) | **Post** /model-hub/prompt-labels/remove/ | 
[**ModelHubPromptLabelsSetDefault**](ModelHubAPI.md#ModelHubPromptLabelsSetDefault) | **Post** /model-hub/prompt-labels/set-default/ | 
[**ModelHubPromptLabelsTemplateLabels**](ModelHubAPI.md#ModelHubPromptLabelsTemplateLabels) | **Get** /model-hub/prompt-labels/template-labels/ | 
[**ModelHubPromptLabelsUpdate**](ModelHubAPI.md#ModelHubPromptLabelsUpdate) | **Put** /model-hub/prompt-labels/{id}/ | 
[**ModelHubPromptTemplatesAddNewDraft**](ModelHubAPI.md#ModelHubPromptTemplatesAddNewDraft) | **Post** /model-hub/prompt-templates/{id}/add-new-draft/ | 
[**ModelHubPromptTemplatesAnalyzePrompt**](ModelHubAPI.md#ModelHubPromptTemplatesAnalyzePrompt) | **Post** /model-hub/prompt-templates/analyze-prompt/ | 
[**ModelHubPromptTemplatesBulkDelete**](ModelHubAPI.md#ModelHubPromptTemplatesBulkDelete) | **Post** /model-hub/prompt-templates/bulk-delete/ | 
[**ModelHubPromptTemplatesCommit**](ModelHubAPI.md#ModelHubPromptTemplatesCommit) | **Post** /model-hub/prompt-templates/{id}/commit/ | 
[**ModelHubPromptTemplatesCompareVersions**](ModelHubAPI.md#ModelHubPromptTemplatesCompareVersions) | **Post** /model-hub/prompt-templates/{id}/compare-versions/ | 
[**ModelHubPromptTemplatesCreate**](ModelHubAPI.md#ModelHubPromptTemplatesCreate) | **Post** /model-hub/prompt-templates/ | 
[**ModelHubPromptTemplatesCreateDraft**](ModelHubAPI.md#ModelHubPromptTemplatesCreateDraft) | **Post** /model-hub/prompt-templates/create-draft/ | 
[**ModelHubPromptTemplatesDelete**](ModelHubAPI.md#ModelHubPromptTemplatesDelete) | **Delete** /model-hub/prompt-templates/{id}/ | 
[**ModelHubPromptTemplatesDeleteEvaluationConfig**](ModelHubAPI.md#ModelHubPromptTemplatesDeleteEvaluationConfig) | **Delete** /model-hub/prompt-templates/{id}/delete-evaluation-config/ | Delete an evaluation configuration by name from a PromptTemplate.
[**ModelHubPromptTemplatesDerivedVariablesExtractCreate**](ModelHubAPI.md#ModelHubPromptTemplatesDerivedVariablesExtractCreate) | **Post** /model-hub/prompt-templates/{prompt_id}/derived-variables/extract/ | Manually trigger extraction of derived variables from outputs.
[**ModelHubPromptTemplatesDerivedVariablesList**](ModelHubAPI.md#ModelHubPromptTemplatesDerivedVariablesList) | **Get** /model-hub/prompt-templates/{prompt_id}/derived-variables/ | Get all derived variables for a prompt template.
[**ModelHubPromptTemplatesDerivedVariablesPreviewCreate**](ModelHubAPI.md#ModelHubPromptTemplatesDerivedVariablesPreviewCreate) | **Post** /model-hub/prompt-templates/derived-variables/preview/ | Preview derived variables from JSON content without saving.
[**ModelHubPromptTemplatesDerivedVariablesSchemaList**](ModelHubAPI.md#ModelHubPromptTemplatesDerivedVariablesSchemaList) | **Get** /model-hub/prompt-templates/{prompt_id}/derived-variables/{column_name}/schema/ | Get the schema for derived variables of a specific column.
[**ModelHubPromptTemplatesGeneratePrompt**](ModelHubAPI.md#ModelHubPromptTemplatesGeneratePrompt) | **Post** /model-hub/prompt-templates/generate-prompt/ | 
[**ModelHubPromptTemplatesGenerateVariables**](ModelHubAPI.md#ModelHubPromptTemplatesGenerateVariables) | **Post** /model-hub/prompt-templates/generate-variables/ | Generate synthetic data for prompt variables using the SyntheticDataAgent.
[**ModelHubPromptTemplatesGetAllVariables**](ModelHubAPI.md#ModelHubPromptTemplatesGetAllVariables) | **Get** /model-hub/prompt-templates/{id}/all-variables/ | 
[**ModelHubPromptTemplatesGetEvaluationConfigs**](ModelHubAPI.md#ModelHubPromptTemplatesGetEvaluationConfigs) | **Get** /model-hub/prompt-templates/{id}/evaluation-configs/ | 
[**ModelHubPromptTemplatesGetNextVersion**](ModelHubAPI.md#ModelHubPromptTemplatesGetNextVersion) | **Get** /model-hub/prompt-templates/{id}/get-next-version/ | 
[**ModelHubPromptTemplatesGetRunStatus**](ModelHubAPI.md#ModelHubPromptTemplatesGetRunStatus) | **Get** /model-hub/prompt-templates/{id}/get-run-status/ | 
[**ModelHubPromptTemplatesGetSdkCode**](ModelHubAPI.md#ModelHubPromptTemplatesGetSdkCode) | **Get** /model-hub/prompt-templates/{id}/get-sdk-code/{language}/ | 
[**ModelHubPromptTemplatesGetTemplateByName**](ModelHubAPI.md#ModelHubPromptTemplatesGetTemplateByName) | **Get** /model-hub/prompt-templates/get-template-by-name/ | 
[**ModelHubPromptTemplatesImprovePrompt**](ModelHubAPI.md#ModelHubPromptTemplatesImprovePrompt) | **Post** /model-hub/prompt-templates/improve-prompt/ | 
[**ModelHubPromptTemplatesList**](ModelHubAPI.md#ModelHubPromptTemplatesList) | **Get** /model-hub/prompt-templates/ | 
[**ModelHubPromptTemplatesPartialUpdate**](ModelHubAPI.md#ModelHubPromptTemplatesPartialUpdate) | **Patch** /model-hub/prompt-templates/{id}/ | 
[**ModelHubPromptTemplatesRead**](ModelHubAPI.md#ModelHubPromptTemplatesRead) | **Get** /model-hub/prompt-templates/{id}/ | 
[**ModelHubPromptTemplatesRetrieveEvaluations**](ModelHubAPI.md#ModelHubPromptTemplatesRetrieveEvaluations) | **Get** /model-hub/prompt-templates/{id}/evaluations/ | 
[**ModelHubPromptTemplatesRunEvalsOnMultipleVersions**](ModelHubAPI.md#ModelHubPromptTemplatesRunEvalsOnMultipleVersions) | **Post** /model-hub/prompt-templates/{id}/run-evals-on-multiple-versions/ | 
[**ModelHubPromptTemplatesRunTemplate**](ModelHubAPI.md#ModelHubPromptTemplatesRunTemplate) | **Post** /model-hub/prompt-templates/{id}/run_template/ | 
[**ModelHubPromptTemplatesSaveName**](ModelHubAPI.md#ModelHubPromptTemplatesSaveName) | **Post** /model-hub/prompt-templates/{id}/save-name/ | 
[**ModelHubPromptTemplatesSavePromptFolder**](ModelHubAPI.md#ModelHubPromptTemplatesSavePromptFolder) | **Post** /model-hub/prompt-templates/{id}/save-prompt-folder/ | 
[**ModelHubPromptTemplatesSetDefault**](ModelHubAPI.md#ModelHubPromptTemplatesSetDefault) | **Post** /model-hub/prompt-templates/{id}/set_default/ | 
[**ModelHubPromptTemplatesStopStreaming**](ModelHubAPI.md#ModelHubPromptTemplatesStopStreaming) | **Get** /model-hub/prompt-templates/{id}/stop-streaming/ | 
[**ModelHubPromptTemplatesUpdate**](ModelHubAPI.md#ModelHubPromptTemplatesUpdate) | **Put** /model-hub/prompt-templates/{id}/ | 
[**ModelHubPromptTemplatesUpdateEvaluationConfigs**](ModelHubAPI.md#ModelHubPromptTemplatesUpdateEvaluationConfigs) | **Post** /model-hub/prompt-templates/{id}/update-evaluation-configs/ | Add or update evaluation configurations for a PromptTemplate.
[**ModelHubPromptTemplatesVersions**](ModelHubAPI.md#ModelHubPromptTemplatesVersions) | **Get** /model-hub/prompt-templates/{id}/versions/ | 
[**ModelHubScoresBulkCreate**](ModelHubAPI.md#ModelHubScoresBulkCreate) | **Post** /model-hub/scores/bulk/ | 
[**ModelHubScoresCreate**](ModelHubAPI.md#ModelHubScoresCreate) | **Post** /model-hub/scores/ | 
[**ModelHubScoresDelete**](ModelHubAPI.md#ModelHubScoresDelete) | **Delete** /model-hub/scores/{id}/ | Soft-delete a score.
[**ModelHubScoresForSource**](ModelHubAPI.md#ModelHubScoresForSource) | **Get** /model-hub/scores/for-source/ | 
[**ModelHubScoresList**](ModelHubAPI.md#ModelHubScoresList) | **Get** /model-hub/scores/ | Universal Score CRUD.
[**ModelHubScoresPartialUpdate**](ModelHubAPI.md#ModelHubScoresPartialUpdate) | **Patch** /model-hub/scores/{id}/ | Universal Score CRUD.
[**ModelHubScoresRead**](ModelHubAPI.md#ModelHubScoresRead) | **Get** /model-hub/scores/{id}/ | Universal Score CRUD.
[**ModelHubScoresUpdate**](ModelHubAPI.md#ModelHubScoresUpdate) | **Put** /model-hub/scores/{id}/ | Universal Score CRUD.



## ModelHubAnnotationQueuesAutomationRulesCreate

> AutomationRule ModelHubAnnotationQueuesAutomationRulesCreate(ctx, queueId).AutomationRule(automationRule).Execute()





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
	queueId := "queueId_example" // string | 
	automationRule := *openapiclient.NewAutomationRule("Name_example", "SourceType_example") // AutomationRule | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesCreate(context.Background(), queueId).AutomationRule(automationRule).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesCreate`: AutomationRule
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **automationRule** | [**AutomationRule**](AutomationRule.md) |  | 

### Return type

[**AutomationRule**](AutomationRule.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesDelete

> ModelHubAnnotationQueuesAutomationRulesDelete(ctx, queueId, id).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesDelete(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesDeleteRequest struct via the builder pattern


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


## ModelHubAnnotationQueuesAutomationRulesEvaluate

> AutomationRuleEvaluateResponse ModelHubAnnotationQueuesAutomationRulesEvaluate(ctx, queueId, id).Body(body).Execute()

Trigger a manual rule run with a sync-or-async branch.



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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesEvaluate(context.Background(), queueId, id).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesEvaluate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesEvaluate`: AutomationRuleEvaluateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesEvaluate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesEvaluateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**AutomationRuleEvaluateResponse**](AutomationRuleEvaluateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesList

> ModelHubAnnotationQueuesAutomationRulesList200Response ModelHubAnnotationQueuesAutomationRulesList(ctx, queueId).Page(page).Limit(limit).Execute()





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
	queueId := "queueId_example" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesList(context.Background(), queueId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesList`: ModelHubAnnotationQueuesAutomationRulesList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubAnnotationQueuesAutomationRulesList200Response**](ModelHubAnnotationQueuesAutomationRulesList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesPartialUpdate

> AutomationRule ModelHubAnnotationQueuesAutomationRulesPartialUpdate(ctx, queueId, id).AutomationRule(automationRule).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.
	automationRule := *openapiclient.NewAutomationRule("Name_example", "SourceType_example") // AutomationRule | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPartialUpdate(context.Background(), queueId, id).AutomationRule(automationRule).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesPartialUpdate`: AutomationRule
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **automationRule** | [**AutomationRule**](AutomationRule.md) |  | 

### Return type

[**AutomationRule**](AutomationRule.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesPreview

> AutomationRuleEvaluateResponse ModelHubAnnotationQueuesAutomationRulesPreview(ctx, queueId, id).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPreview(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPreview``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesPreview`: AutomationRuleEvaluateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesPreview`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesPreviewRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**AutomationRuleEvaluateResponse**](AutomationRuleEvaluateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesRead

> AutomationRule ModelHubAnnotationQueuesAutomationRulesRead(ctx, queueId, id).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesRead(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesRead`: AutomationRule
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**AutomationRule**](AutomationRule.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesAutomationRulesUpdate

> AutomationRule ModelHubAnnotationQueuesAutomationRulesUpdate(ctx, queueId, id).AutomationRule(automationRule).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this automation rule.
	automationRule := *openapiclient.NewAutomationRule("Name_example", "SourceType_example") // AutomationRule | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesUpdate(context.Background(), queueId, id).AutomationRule(automationRule).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesAutomationRulesUpdate`: AutomationRule
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesAutomationRulesUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this automation rule. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesAutomationRulesUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **automationRule** | [**AutomationRule**](AutomationRule.md) |  | 

### Return type

[**AutomationRule**](AutomationRule.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesForSource

> QueueForSourceResponse ModelHubAnnotationQueuesForSource(ctx).Page(page).Limit(limit).SourceType(sourceType).SourceId(sourceId).Sources(sources).Execute()





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
	sourceType := "sourceType_example" // string |  (optional)
	sourceId := "sourceId_example" // string |  (optional)
	sources := "sources_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesForSource(context.Background()).Page(page).Limit(limit).SourceType(sourceType).SourceId(sourceId).Sources(sources).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesForSource``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesForSource`: QueueForSourceResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesForSource`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesForSourceRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **sourceType** | **string** |  | 
 **sourceId** | **string** |  | 
 **sources** | **string** |  | 

### Return type

[**QueueForSourceResponse**](QueueForSourceResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesGetOrCreateDefault

> QueueDefaultResponse ModelHubAnnotationQueuesGetOrCreateDefault(ctx).QueueDefaultRequest(queueDefaultRequest).Execute()





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
	queueDefaultRequest := *openapiclient.NewQueueDefaultRequest() // QueueDefaultRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesGetOrCreateDefault(context.Background()).QueueDefaultRequest(queueDefaultRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesGetOrCreateDefault``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesGetOrCreateDefault`: QueueDefaultResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesGetOrCreateDefault`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesGetOrCreateDefaultRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **queueDefaultRequest** | [**QueueDefaultRequest**](QueueDefaultRequest.md) |  | 

### Return type

[**QueueDefaultResponse**](QueueDefaultResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesHardDelete

> QueueHardDeleteResponse ModelHubAnnotationQueuesHardDelete(ctx, id).QueueHardDeleteRequest(queueHardDeleteRequest).Execute()

Permanently remove a queue + everything attached.



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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	queueHardDeleteRequest := *openapiclient.NewQueueHardDeleteRequest(false, "ConfirmName_example") // QueueHardDeleteRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesHardDelete(context.Background(), id).QueueHardDeleteRequest(queueHardDeleteRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesHardDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesHardDelete`: QueueHardDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesHardDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesHardDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueHardDeleteRequest** | [**QueueHardDeleteRequest**](QueueHardDeleteRequest.md) |  | 

### Return type

[**QueueHardDeleteResponse**](QueueHardDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesItemsCreate

> QueueItem ModelHubAnnotationQueuesItemsCreate(ctx, queueId).QueueItem(queueItem).Execute()





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
	queueId := "queueId_example" // string | 
	queueItem := *openapiclient.NewQueueItem("SourceType_example") // QueueItem | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesItemsCreate(context.Background(), queueId).QueueItem(queueItem).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesItemsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesItemsCreate`: QueueItem
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesItemsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesItemsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **queueItem** | [**QueueItem**](QueueItem.md) |  | 

### Return type

[**QueueItem**](QueueItem.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesItemsDelete

> ModelHubAnnotationQueuesItemsDelete(ctx, queueId, id).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this queue item.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesItemsDelete(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesItemsDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesItemsDeleteRequest struct via the builder pattern


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


## ModelHubAnnotationQueuesItemsPartialUpdate

> QueueItem ModelHubAnnotationQueuesItemsPartialUpdate(ctx, queueId, id).QueueItem(queueItem).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this queue item.
	queueItem := *openapiclient.NewQueueItem("SourceType_example") // QueueItem | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesItemsPartialUpdate(context.Background(), queueId, id).QueueItem(queueItem).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesItemsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesItemsPartialUpdate`: QueueItem
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesItemsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesItemsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **queueItem** | [**QueueItem**](QueueItem.md) |  | 

### Return type

[**QueueItem**](QueueItem.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesItemsRead

> QueueItem ModelHubAnnotationQueuesItemsRead(ctx, queueId, id).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this queue item.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesItemsRead(context.Background(), queueId, id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesItemsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesItemsRead`: QueueItem
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesItemsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesItemsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**QueueItem**](QueueItem.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesItemsUpdate

> QueueItem ModelHubAnnotationQueuesItemsUpdate(ctx, queueId, id).QueueItem(queueItem).Execute()





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
	queueId := "queueId_example" // string | 
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this queue item.
	queueItem := *openapiclient.NewQueueItem("SourceType_example") // QueueItem | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesItemsUpdate(context.Background(), queueId, id).QueueItem(queueItem).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesItemsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesItemsUpdate`: QueueItem
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesItemsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**queueId** | **string** |  | 
**id** | **string** | A UUID string identifying this queue item. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesItemsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **queueItem** | [**QueueItem**](QueueItem.md) |  | 

### Return type

[**QueueItem**](QueueItem.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesRestore

> QueueStatusResponse ModelHubAnnotationQueuesRestore(ctx, id).Body(body).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesRestore(context.Background(), id).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesRestore``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesRestore`: QueueStatusResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesRestore`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesRestoreRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**QueueStatusResponse**](QueueStatusResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationQueuesUpdate

> AnnotationQueue ModelHubAnnotationQueuesUpdate(ctx, id).AnnotationQueue(annotationQueue).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this annotation queue.
	annotationQueue := *openapiclient.NewAnnotationQueue("Name_example") // AnnotationQueue | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationQueuesUpdate(context.Background(), id).AnnotationQueue(annotationQueue).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationQueuesUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationQueuesUpdate`: AnnotationQueue
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationQueuesUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this annotation queue. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationQueuesUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **annotationQueue** | [**AnnotationQueue**](AnnotationQueue.md) |  | 

### Return type

[**AnnotationQueue**](AnnotationQueue.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsCreate

> AnnotationsLabels ModelHubAnnotationsLabelsCreate(ctx).AnnotationsLabels(annotationsLabels).Execute()





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
	annotationsLabels := *openapiclient.NewAnnotationsLabels("Name_example", "Type_example") // AnnotationsLabels | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsCreate(context.Background()).AnnotationsLabels(annotationsLabels).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsCreate`: AnnotationsLabels
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **annotationsLabels** | [**AnnotationsLabels**](AnnotationsLabels.md) |  | 

### Return type

[**AnnotationsLabels**](AnnotationsLabels.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsDelete

> ModelHubAnnotationsLabelsDelete(ctx, id).Execute()





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
	r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsDelete``: %v\n", err)
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

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsDeleteRequest struct via the builder pattern


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


## ModelHubAnnotationsLabelsList

> []AnnotationsLabels ModelHubAnnotationsLabelsList(ctx).Page(page).Limit(limit).Dataset(dataset).ProjectId(projectId).Type_(type_).Search(search).IncludeUsageCount(includeUsageCount).IncludeArchived(includeArchived).Execute()





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
	dataset := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	projectId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	type_ := "type__example" // string |  (optional)
	search := "search_example" // string |  (optional)
	includeUsageCount := true // bool |  (optional)
	includeArchived := true // bool |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsList(context.Background()).Page(page).Limit(limit).Dataset(dataset).ProjectId(projectId).Type_(type_).Search(search).IncludeUsageCount(includeUsageCount).IncludeArchived(includeArchived).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsList`: []AnnotationsLabels
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **dataset** | **string** |  | 
 **projectId** | **string** |  | 
 **type_** | **string** |  | 
 **search** | **string** |  | 
 **includeUsageCount** | **bool** |  | 
 **includeArchived** | **bool** |  | 

### Return type

[**[]AnnotationsLabels**](AnnotationsLabels.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsPartialUpdate

> AnnotationsLabels ModelHubAnnotationsLabelsPartialUpdate(ctx, id).AnnotationsLabels(annotationsLabels).Execute()





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
	annotationsLabels := *openapiclient.NewAnnotationsLabels("Name_example", "Type_example") // AnnotationsLabels | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsPartialUpdate(context.Background(), id).AnnotationsLabels(annotationsLabels).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsPartialUpdate`: AnnotationsLabels
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **annotationsLabels** | [**AnnotationsLabels**](AnnotationsLabels.md) |  | 

### Return type

[**AnnotationsLabels**](AnnotationsLabels.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsRead

> AnnotationsLabels ModelHubAnnotationsLabelsRead(ctx, id).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsRead`: AnnotationsLabels
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**AnnotationsLabels**](AnnotationsLabels.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsRestore

> AnnotationLabelRestoreResponse ModelHubAnnotationsLabelsRestore(ctx, id).Body(body).Execute()





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
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsRestore(context.Background(), id).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsRestore``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsRestore`: AnnotationLabelRestoreResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsRestore`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsRestoreRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**AnnotationLabelRestoreResponse**](AnnotationLabelRestoreResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubAnnotationsLabelsUpdate

> AnnotationsLabels ModelHubAnnotationsLabelsUpdate(ctx, id).AnnotationsLabels(annotationsLabels).Execute()





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
	annotationsLabels := *openapiclient.NewAnnotationsLabels("Name_example", "Type_example") // AnnotationsLabels | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubAnnotationsLabelsUpdate(context.Background(), id).AnnotationsLabels(annotationsLabels).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubAnnotationsLabelsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubAnnotationsLabelsUpdate`: AnnotationsLabels
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubAnnotationsLabelsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubAnnotationsLabelsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **annotationsLabels** | [**AnnotationsLabels**](AnnotationsLabels.md) |  | 

### Return type

[**AnnotationsLabels**](AnnotationsLabels.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiKeysCreate

> ApiKey ModelHubApiKeysCreate(ctx).ApiKey(apiKey).Execute()





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
	apiKey := *openapiclient.NewApiKey("Provider_example") // ApiKey | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiKeysCreate(context.Background()).ApiKey(apiKey).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiKeysCreate`: ApiKey
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiKeysCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiKeysCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiKey** | [**ApiKey**](ApiKey.md) |  | 

### Return type

[**ApiKey**](ApiKey.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiKeysDelete

> ModelHubApiKeysDelete(ctx, id).Execute()

Soft-delete an API key.



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
	r, err := apiClient.ModelHubAPI.ModelHubApiKeysDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysDelete``: %v\n", err)
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

Other parameters are passed through a pointer to a apiModelHubApiKeysDeleteRequest struct via the builder pattern


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


## ModelHubApiKeysList

> ModelHubApiKeysList200Response ModelHubApiKeysList(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiKeysList(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiKeysList`: ModelHubApiKeysList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiKeysList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiKeysListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubApiKeysList200Response**](ModelHubApiKeysList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiKeysPartialUpdate

> ApiKey ModelHubApiKeysPartialUpdate(ctx, id).ApiKey(apiKey).Execute()





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
	apiKey := *openapiclient.NewApiKey("Provider_example") // ApiKey | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiKeysPartialUpdate(context.Background(), id).ApiKey(apiKey).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiKeysPartialUpdate`: ApiKey
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiKeysPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiKeysPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **apiKey** | [**ApiKey**](ApiKey.md) |  | 

### Return type

[**ApiKey**](ApiKey.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiKeysRead

> ApiKey ModelHubApiKeysRead(ctx, id).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiKeysRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiKeysRead`: ApiKey
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiKeysRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiKeysReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ApiKey**](ApiKey.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiKeysUpdate

> ApiKey ModelHubApiKeysUpdate(ctx, id).ApiKey(apiKey).Execute()





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
	apiKey := *openapiclient.NewApiKey("Provider_example") // ApiKey | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiKeysUpdate(context.Background(), id).ApiKey(apiKey).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiKeysUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiKeysUpdate`: ApiKey
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiKeysUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiKeysUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **apiKey** | [**ApiKey**](ApiKey.md) |  | 

### Return type

[**ApiKey**](ApiKey.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubApiModelsListList

> ModelHubPaginatedResponse ModelHubApiModelsListList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubApiModelsListList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubApiModelsListList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubApiModelsListList`: ModelHubPaginatedResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubApiModelsListList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubApiModelsListListRequest struct via the builder pattern


### Return type

[**ModelHubPaginatedResponse**](ModelHubPaginatedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetRunPromptStatsList

> DatasetRunPromptStatsResponse ModelHubDatasetRunPromptStatsList(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetRunPromptStatsList(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetRunPromptStatsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetRunPromptStatsList`: DatasetRunPromptStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetRunPromptStatsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetRunPromptStatsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetRunPromptStatsResponse**](DatasetRunPromptStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsAddApiColumnCreate

> DynamicColumnCreateResponse ModelHubDatasetsAddApiColumnCreate(ctx, datasetId).AddApiColumnRequest(addApiColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	addApiColumnRequest := *openapiclient.NewAddApiColumnRequest("ColumnName_example", map[string]interface{}{"key": interface{}(123)}) // AddApiColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsAddApiColumnCreate(context.Background(), datasetId).AddApiColumnRequest(addApiColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsAddApiColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsAddApiColumnCreate`: DynamicColumnCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsAddApiColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsAddApiColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **addApiColumnRequest** | [**AddApiColumnRequest**](AddApiColumnRequest.md) |  | 

### Return type

[**DynamicColumnCreateResponse**](DynamicColumnCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsAddVectorDbColumnCreate

> DynamicColumnCreateResponse ModelHubDatasetsAddVectorDbColumnCreate(ctx, datasetId).VectorDBColumnRequest(vectorDBColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	vectorDBColumnRequest := *openapiclient.NewVectorDBColumnRequest("ColumnId_example", "SubType_example", "ApiKey_example") // VectorDBColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsAddVectorDbColumnCreate(context.Background(), datasetId).VectorDBColumnRequest(vectorDBColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsAddVectorDbColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsAddVectorDbColumnCreate`: DynamicColumnCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsAddVectorDbColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsAddVectorDbColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **vectorDBColumnRequest** | [**VectorDBColumnRequest**](VectorDBColumnRequest.md) |  | 

### Return type

[**DynamicColumnCreateResponse**](DynamicColumnCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsClassifyColumnCreate

> DynamicColumnCreateResponse ModelHubDatasetsClassifyColumnCreate(ctx, datasetId).ClassifyColumnRequest(classifyColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	classifyColumnRequest := *openapiclient.NewClassifyColumnRequest("ColumnId_example", []string{"Labels_example"}) // ClassifyColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsClassifyColumnCreate(context.Background(), datasetId).ClassifyColumnRequest(classifyColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsClassifyColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsClassifyColumnCreate`: DynamicColumnCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsClassifyColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsClassifyColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **classifyColumnRequest** | [**ClassifyColumnRequest**](ClassifyColumnRequest.md) |  | 

### Return type

[**DynamicColumnCreateResponse**](DynamicColumnCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareDatasetsAddEvalCreate

> DevelopDatasetMessageResponse ModelHubDatasetsCompareDatasetsAddEvalCreate(ctx, datasetId).CompareExperimentEvalRequest(compareExperimentEvalRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	compareExperimentEvalRequest := *openapiclient.NewCompareExperimentEvalRequest("Name_example", "TemplateId_example", map[string]interface{}{"key": interface{}(123)}) // CompareExperimentEvalRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareDatasetsAddEvalCreate(context.Background(), datasetId).CompareExperimentEvalRequest(compareExperimentEvalRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareDatasetsAddEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareDatasetsAddEvalCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareDatasetsAddEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareDatasetsAddEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compareExperimentEvalRequest** | [**CompareExperimentEvalRequest**](CompareExperimentEvalRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareDatasetsCreate

> CompareDatasetResponse ModelHubDatasetsCompareDatasetsCreate(ctx, datasetId).CompareDataset(compareDataset).Execute()





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
	datasetId := "datasetId_example" // string | 
	compareDataset := *openapiclient.NewCompareDataset("BaseColumnName_example", []string{"DatasetIds_example"}) // CompareDataset | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareDatasetsCreate(context.Background(), datasetId).CompareDataset(compareDataset).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareDatasetsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareDatasetsCreate`: CompareDatasetResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareDatasetsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareDatasetsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compareDataset** | [**CompareDataset**](CompareDataset.md) |  | 

### Return type

[**CompareDatasetResponse**](CompareDatasetResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareDatasetsDownloadCreate

> *os.File ModelHubDatasetsCompareDatasetsDownloadCreate(ctx, datasetId).CompareDataset(compareDataset).Execute()





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
	datasetId := "datasetId_example" // string | 
	compareDataset := *openapiclient.NewCompareDataset("BaseColumnName_example", []string{"DatasetIds_example"}) // CompareDataset | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareDatasetsDownloadCreate(context.Background(), datasetId).CompareDataset(compareDataset).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareDatasetsDownloadCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareDatasetsDownloadCreate`: *os.File
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareDatasetsDownloadCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareDatasetsDownloadCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compareDataset** | [**CompareDataset**](CompareDataset.md) |  | 

### Return type

[***os.File**](*os.File.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareDatasetsStartEvalCreate

> DevelopDatasetMessageResponse ModelHubDatasetsCompareDatasetsStartEvalCreate(ctx, datasetId).CompareStartEvalsRequest(compareStartEvalsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	compareStartEvalsRequest := *openapiclient.NewCompareStartEvalsRequest([]string{"UserEvalNames_example"}) // CompareStartEvalsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareDatasetsStartEvalCreate(context.Background(), datasetId).CompareStartEvalsRequest(compareStartEvalsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareDatasetsStartEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareDatasetsStartEvalCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareDatasetsStartEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareDatasetsStartEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compareStartEvalsRequest** | [**CompareStartEvalsRequest**](CompareStartEvalsRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareGetEvalsListCreate

> CompareEvalListResponse ModelHubDatasetsCompareGetEvalsListCreate(ctx).CompareEvalsListRequest(compareEvalsListRequest).Execute()





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
	compareEvalsListRequest := *openapiclient.NewCompareEvalsListRequest("EvalType_example", []string{"DatasetIds_example"}) // CompareEvalsListRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareGetEvalsListCreate(context.Background()).CompareEvalsListRequest(compareEvalsListRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareGetEvalsListCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareGetEvalsListCreate`: CompareEvalListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareGetEvalsListCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareGetEvalsListCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **compareEvalsListRequest** | [**CompareEvalsListRequest**](CompareEvalsListRequest.md) |  | 

### Return type

[**CompareEvalListResponse**](CompareEvalListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsComparePreviewRunEvalCreate

> EvalPreviewResponse ModelHubDatasetsComparePreviewRunEvalCreate(ctx).ComparePreviewRunEvalRequest(comparePreviewRunEvalRequest).Execute()





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
	comparePreviewRunEvalRequest := *openapiclient.NewComparePreviewRunEvalRequest(map[string]interface{}{"key": interface{}(123)}, "TemplateId_example", []string{"DatasetIds_example"}) // ComparePreviewRunEvalRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsComparePreviewRunEvalCreate(context.Background()).ComparePreviewRunEvalRequest(comparePreviewRunEvalRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsComparePreviewRunEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsComparePreviewRunEvalCreate`: EvalPreviewResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsComparePreviewRunEvalCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsComparePreviewRunEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **comparePreviewRunEvalRequest** | [**ComparePreviewRunEvalRequest**](ComparePreviewRunEvalRequest.md) |  | 

### Return type

[**EvalPreviewResponse**](EvalPreviewResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsCompareStatsCreate

> CompareDatasetStatsResponse ModelHubDatasetsCompareStatsCreate(ctx, datasetId).CompareDatasetStatsRequest(compareDatasetStatsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	compareDatasetStatsRequest := *openapiclient.NewCompareDatasetStatsRequest("BaseColumnName_example", []string{"DatasetIds_example"}) // CompareDatasetStatsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsCompareStatsCreate(context.Background(), datasetId).CompareDatasetStatsRequest(compareDatasetStatsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsCompareStatsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsCompareStatsCreate`: CompareDatasetStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsCompareStatsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsCompareStatsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compareDatasetStatsRequest** | [**CompareDatasetStatsRequest**](CompareDatasetStatsRequest.md) |  | 

### Return type

[**CompareDatasetStatsResponse**](CompareDatasetStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsConditionalColumnCreate

> DynamicColumnCreateResponse ModelHubDatasetsConditionalColumnCreate(ctx, datasetId).ConditionalColumnRequest(conditionalColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	conditionalColumnRequest := *openapiclient.NewConditionalColumnRequest([]map[string]interface{}{map[string]interface{}{"key": interface{}(123)}}, "NewColumnName_example") // ConditionalColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsConditionalColumnCreate(context.Background(), datasetId).ConditionalColumnRequest(conditionalColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsConditionalColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsConditionalColumnCreate`: DynamicColumnCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsConditionalColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsConditionalColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **conditionalColumnRequest** | [**ConditionalColumnRequest**](ConditionalColumnRequest.md) |  | 

### Return type

[**DynamicColumnCreateResponse**](DynamicColumnCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsDeleteCompareDelete

> CompareDatasetDeleteResponse ModelHubDatasetsDeleteCompareDelete(ctx, compareId).Execute()





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
	compareId := "compareId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsDeleteCompareDelete(context.Background(), compareId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsDeleteCompareDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsDeleteCompareDelete`: CompareDatasetDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsDeleteCompareDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**compareId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsDeleteCompareDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CompareDatasetDeleteResponse**](CompareDatasetDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsDeleteCompareRead

> CompareDatasetRowResponse ModelHubDatasetsDeleteCompareRead(ctx, compareId).Execute()





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
	compareId := "compareId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsDeleteCompareRead(context.Background(), compareId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsDeleteCompareRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsDeleteCompareRead`: CompareDatasetRowResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsDeleteCompareRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**compareId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsDeleteCompareReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CompareDatasetRowResponse**](CompareDatasetRowResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsDuplicateRowsCreate

> DuplicateRowsResponse ModelHubDatasetsDuplicateRowsCreate(ctx, datasetId).DuplicateRowsRequest(duplicateRowsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	duplicateRowsRequest := *openapiclient.NewDuplicateRowsRequest() // DuplicateRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsDuplicateRowsCreate(context.Background(), datasetId).DuplicateRowsRequest(duplicateRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsDuplicateRowsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsDuplicateRowsCreate`: DuplicateRowsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsDuplicateRowsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsDuplicateRowsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **duplicateRowsRequest** | [**DuplicateRowsRequest**](DuplicateRowsRequest.md) |  | 

### Return type

[**DuplicateRowsResponse**](DuplicateRowsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsExplanationSummaryRead

> DatasetExplanationSummaryResponse ModelHubDatasetsExplanationSummaryRead(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsExplanationSummaryRead(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsExplanationSummaryRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsExplanationSummaryRead`: DatasetExplanationSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsExplanationSummaryRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsExplanationSummaryReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetExplanationSummaryResponse**](DatasetExplanationSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsExplanationSummaryRefreshCreate

> DatasetExplanationSummaryResponse ModelHubDatasetsExplanationSummaryRefreshCreate(ctx, datasetId).Body(body).Execute()





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
	datasetId := "datasetId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsExplanationSummaryRefreshCreate(context.Background(), datasetId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsExplanationSummaryRefreshCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsExplanationSummaryRefreshCreate`: DatasetExplanationSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsExplanationSummaryRefreshCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsExplanationSummaryRefreshCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**DatasetExplanationSummaryResponse**](DatasetExplanationSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsExtractEntitiesCreate

> DynamicColumnMessageResponse ModelHubDatasetsExtractEntitiesCreate(ctx, datasetId).ExtractEntitiesRequest(extractEntitiesRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	extractEntitiesRequest := *openapiclient.NewExtractEntitiesRequest("ColumnId_example", "Instruction_example") // ExtractEntitiesRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsExtractEntitiesCreate(context.Background(), datasetId).ExtractEntitiesRequest(extractEntitiesRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsExtractEntitiesCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsExtractEntitiesCreate`: DynamicColumnMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsExtractEntitiesCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsExtractEntitiesCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **extractEntitiesRequest** | [**ExtractEntitiesRequest**](ExtractEntitiesRequest.md) |  | 

### Return type

[**DynamicColumnMessageResponse**](DynamicColumnMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsGetCompareRowDelete

> CompareDatasetDeleteResponse ModelHubDatasetsGetCompareRowDelete(ctx, compareId, rowId).Execute()





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
	compareId := "compareId_example" // string | 
	rowId := "rowId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsGetCompareRowDelete(context.Background(), compareId, rowId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsGetCompareRowDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsGetCompareRowDelete`: CompareDatasetDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsGetCompareRowDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**compareId** | **string** |  | 
**rowId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsGetCompareRowDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**CompareDatasetDeleteResponse**](CompareDatasetDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsGetCompareRowRead

> CompareDatasetRowResponse ModelHubDatasetsGetCompareRowRead(ctx, compareId, rowId).Execute()





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
	compareId := "compareId_example" // string | 
	rowId := "rowId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsGetCompareRowRead(context.Background(), compareId, rowId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsGetCompareRowRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsGetCompareRowRead`: CompareDatasetRowResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsGetCompareRowRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**compareId** | **string** |  | 
**rowId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsGetCompareRowReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**CompareDatasetRowResponse**](CompareDatasetRowResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsHuggingfaceDetailCreate

> HuggingFaceDatasetDetailResponse ModelHubDatasetsHuggingfaceDetailCreate(ctx).HuggingFaceDatasetDetailRequest(huggingFaceDatasetDetailRequest).Execute()





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
	huggingFaceDatasetDetailRequest := *openapiclient.NewHuggingFaceDatasetDetailRequest("DatasetId_example") // HuggingFaceDatasetDetailRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsHuggingfaceDetailCreate(context.Background()).HuggingFaceDatasetDetailRequest(huggingFaceDatasetDetailRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsHuggingfaceDetailCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsHuggingfaceDetailCreate`: HuggingFaceDatasetDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsHuggingfaceDetailCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsHuggingfaceDetailCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **huggingFaceDatasetDetailRequest** | [**HuggingFaceDatasetDetailRequest**](HuggingFaceDatasetDetailRequest.md) |  | 

### Return type

[**HuggingFaceDatasetDetailResponse**](HuggingFaceDatasetDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsHuggingfaceListCreate

> HuggingFaceDatasetListResponse ModelHubDatasetsHuggingfaceListCreate(ctx).HuggingFaceDatasetListRequest(huggingFaceDatasetListRequest).Execute()





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
	huggingFaceDatasetListRequest := *openapiclient.NewHuggingFaceDatasetListRequest() // HuggingFaceDatasetListRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsHuggingfaceListCreate(context.Background()).HuggingFaceDatasetListRequest(huggingFaceDatasetListRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsHuggingfaceListCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsHuggingfaceListCreate`: HuggingFaceDatasetListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsHuggingfaceListCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsHuggingfaceListCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **huggingFaceDatasetListRequest** | [**HuggingFaceDatasetListRequest**](HuggingFaceDatasetListRequest.md) |  | 

### Return type

[**HuggingFaceDatasetListResponse**](HuggingFaceDatasetListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsMergeCreate

> MergeDatasetResponse ModelHubDatasetsMergeCreate(ctx, datasetId).MergeDatasetRequest(mergeDatasetRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	mergeDatasetRequest := *openapiclient.NewMergeDatasetRequest("TargetDatasetId_example") // MergeDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsMergeCreate(context.Background(), datasetId).MergeDatasetRequest(mergeDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsMergeCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsMergeCreate`: MergeDatasetResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsMergeCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsMergeCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **mergeDatasetRequest** | [**MergeDatasetRequest**](MergeDatasetRequest.md) |  | 

### Return type

[**MergeDatasetResponse**](MergeDatasetResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDatasetsPreviewCreate

> PreviewDatasetOperationResponse ModelHubDatasetsPreviewCreate(ctx, datasetId, operationType).PreviewDatasetOperationRequest(previewDatasetOperationRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	operationType := "operationType_example" // string | 
	previewDatasetOperationRequest := *openapiclient.NewPreviewDatasetOperationRequest() // PreviewDatasetOperationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDatasetsPreviewCreate(context.Background(), datasetId, operationType).PreviewDatasetOperationRequest(previewDatasetOperationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDatasetsPreviewCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDatasetsPreviewCreate`: PreviewDatasetOperationResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDatasetsPreviewCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**operationType** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDatasetsPreviewCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **previewDatasetOperationRequest** | [**PreviewDatasetOperationRequest**](PreviewDatasetOperationRequest.md) |  | 

### Return type

[**PreviewDatasetOperationResponse**](PreviewDatasetOperationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDeleteEvalTemplateCreate

> ModelHubStringResultResponse ModelHubDeleteEvalTemplateCreate(ctx).DeleteEvalTemplate(deleteEvalTemplate).Execute()





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
	deleteEvalTemplate := *openapiclient.NewDeleteEvalTemplate("EvalTemplateId_example") // DeleteEvalTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDeleteEvalTemplateCreate(context.Background()).DeleteEvalTemplate(deleteEvalTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDeleteEvalTemplateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDeleteEvalTemplateCreate`: ModelHubStringResultResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDeleteEvalTemplateCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDeleteEvalTemplateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deleteEvalTemplate** | [**DeleteEvalTemplate**](DeleteEvalTemplate.md) |  | 

### Return type

[**ModelHubStringResultResponse**](ModelHubStringResultResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddAsNewCreate

> DatasetCopyResponse ModelHubDevelopsAddAsNewCreate(ctx).AddAsNewDatasetRequest(addAsNewDatasetRequest).Execute()





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
	addAsNewDatasetRequest := *openapiclient.NewAddAsNewDatasetRequest("DatasetId_example") // AddAsNewDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddAsNewCreate(context.Background()).AddAsNewDatasetRequest(addAsNewDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddAsNewCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddAsNewCreate`: DatasetCopyResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddAsNewCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddAsNewCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addAsNewDatasetRequest** | [**AddAsNewDatasetRequest**](AddAsNewDatasetRequest.md) |  | 

### Return type

[**DatasetCopyResponse**](DatasetCopyResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddEmptyColumnsCreate

> DatasetColumnsMutationResponse ModelHubDevelopsAddEmptyColumnsCreate(ctx, datasetId).DatasetAddEmptyColumnsRequest(datasetAddEmptyColumnsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetAddEmptyColumnsRequest := *openapiclient.NewDatasetAddEmptyColumnsRequest() // DatasetAddEmptyColumnsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddEmptyColumnsCreate(context.Background(), datasetId).DatasetAddEmptyColumnsRequest(datasetAddEmptyColumnsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddEmptyColumnsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddEmptyColumnsCreate`: DatasetColumnsMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddEmptyColumnsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddEmptyColumnsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetAddEmptyColumnsRequest** | [**DatasetAddEmptyColumnsRequest**](DatasetAddEmptyColumnsRequest.md) |  | 

### Return type

[**DatasetColumnsMutationResponse**](DatasetColumnsMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddEmptyRowsCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddEmptyRowsCreate(ctx, datasetId).DatasetAddEmptyRowsRequest(datasetAddEmptyRowsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetAddEmptyRowsRequest := *openapiclient.NewDatasetAddEmptyRowsRequest() // DatasetAddEmptyRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddEmptyRowsCreate(context.Background(), datasetId).DatasetAddEmptyRowsRequest(datasetAddEmptyRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddEmptyRowsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddEmptyRowsCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddEmptyRowsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddEmptyRowsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetAddEmptyRowsRequest** | [**DatasetAddEmptyRowsRequest**](DatasetAddEmptyRowsRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddMultipleStaticColumnsCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddMultipleStaticColumnsCreate(ctx, datasetId).DatasetMultipleStaticColumnsRequest(datasetMultipleStaticColumnsRequest).Execute()

Add multiple static columns to a dataset at once.



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
	datasetId := "datasetId_example" // string | 
	datasetMultipleStaticColumnsRequest := *openapiclient.NewDatasetMultipleStaticColumnsRequest([]map[string]interface{}{map[string]interface{}{"key": interface{}(123)}}) // DatasetMultipleStaticColumnsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddMultipleStaticColumnsCreate(context.Background(), datasetId).DatasetMultipleStaticColumnsRequest(datasetMultipleStaticColumnsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddMultipleStaticColumnsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddMultipleStaticColumnsCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddMultipleStaticColumnsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddMultipleStaticColumnsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetMultipleStaticColumnsRequest** | [**DatasetMultipleStaticColumnsRequest**](DatasetMultipleStaticColumnsRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddRowsFromExistingDatasetCreate

> DatasetRowsImportedResponse ModelHubDevelopsAddRowsFromExistingDatasetCreate(ctx, datasetId).DatasetAddRowsFromExistingRequest(datasetAddRowsFromExistingRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetAddRowsFromExistingRequest := *openapiclient.NewDatasetAddRowsFromExistingRequest("SourceDatasetId_example", map[string]string{"key": "Inner_example"}) // DatasetAddRowsFromExistingRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddRowsFromExistingDatasetCreate(context.Background(), datasetId).DatasetAddRowsFromExistingRequest(datasetAddRowsFromExistingRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddRowsFromExistingDatasetCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddRowsFromExistingDatasetCreate`: DatasetRowsImportedResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddRowsFromExistingDatasetCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddRowsFromExistingDatasetCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetAddRowsFromExistingRequest** | [**DatasetAddRowsFromExistingRequest**](DatasetAddRowsFromExistingRequest.md) |  | 

### Return type

[**DatasetRowsImportedResponse**](DatasetRowsImportedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddRowsFromFileCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddRowsFromFileCreate(ctx).AddRowsFromFileRequest(addRowsFromFileRequest).Execute()





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
	addRowsFromFileRequest := *openapiclient.NewAddRowsFromFileRequest("DatasetId_example") // AddRowsFromFileRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddRowsFromFileCreate(context.Background()).AddRowsFromFileRequest(addRowsFromFileRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddRowsFromFileCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddRowsFromFileCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddRowsFromFileCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddRowsFromFileCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addRowsFromFileRequest** | [**AddRowsFromFileRequest**](AddRowsFromFileRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddRowsFromHuggingfaceCreate

> DatasetRowsImportMessageResponse ModelHubDevelopsAddRowsFromHuggingfaceCreate(ctx, datasetId).HuggingFaceAddRowsRequest(huggingFaceAddRowsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	huggingFaceAddRowsRequest := *openapiclient.NewHuggingFaceAddRowsRequest("HuggingfaceDatasetName_example", "HuggingfaceDatasetConfig_example", "HuggingfaceDatasetSplit_example") // HuggingFaceAddRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddRowsFromHuggingfaceCreate(context.Background(), datasetId).HuggingFaceAddRowsRequest(huggingFaceAddRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddRowsFromHuggingfaceCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddRowsFromHuggingfaceCreate`: DatasetRowsImportMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddRowsFromHuggingfaceCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddRowsFromHuggingfaceCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **huggingFaceAddRowsRequest** | [**HuggingFaceAddRowsRequest**](HuggingFaceAddRowsRequest.md) |  | 

### Return type

[**DatasetRowsImportMessageResponse**](DatasetRowsImportMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddRowsSdkCreate

> DatasetSdkRowsResponse ModelHubDevelopsAddRowsSdkCreate(ctx).DatasetSdkRowsRequest(datasetSdkRowsRequest).Execute()





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
	datasetSdkRowsRequest := *openapiclient.NewDatasetSdkRowsRequest() // DatasetSdkRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddRowsSdkCreate(context.Background()).DatasetSdkRowsRequest(datasetSdkRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddRowsSdkCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddRowsSdkCreate`: DatasetSdkRowsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddRowsSdkCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddRowsSdkCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **datasetSdkRowsRequest** | [**DatasetSdkRowsRequest**](DatasetSdkRowsRequest.md) |  | 

### Return type

[**DatasetSdkRowsResponse**](DatasetSdkRowsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddRunPromptColumnCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddRunPromptColumnCreate(ctx).AddRunPrompt(addRunPrompt).Execute()





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
	addRunPrompt := *openapiclient.NewAddRunPrompt("DatasetId_example", "Name_example") // AddRunPrompt | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddRunPromptColumnCreate(context.Background()).AddRunPrompt(addRunPrompt).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddRunPromptColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddRunPromptColumnCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddRunPromptColumnCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddRunPromptColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addRunPrompt** | [**AddRunPrompt**](AddRunPrompt.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddStaticColumnCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddStaticColumnCreate(ctx, datasetId).DatasetStaticColumnRequest(datasetStaticColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetStaticColumnRequest := *openapiclient.NewDatasetStaticColumnRequest("NewColumnName_example", "ColumnType_example") // DatasetStaticColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddStaticColumnCreate(context.Background(), datasetId).DatasetStaticColumnRequest(datasetStaticColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddStaticColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddStaticColumnCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddStaticColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddStaticColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetStaticColumnRequest** | [**DatasetStaticColumnRequest**](DatasetStaticColumnRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddSyntheticDataCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddSyntheticDataCreate(ctx, datasetId).SyntheticData(syntheticData).Execute()





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
	datasetId := "datasetId_example" // string | 
	syntheticData := *openapiclient.NewSyntheticData(int32(123), []*string{nil}, map[string]interface{}{"key": interface{}(123)}) // SyntheticData | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddSyntheticDataCreate(context.Background(), datasetId).SyntheticData(syntheticData).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddSyntheticDataCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddSyntheticDataCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddSyntheticDataCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddSyntheticDataCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **syntheticData** | [**SyntheticData**](SyntheticData.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsAddUserEvalCreate

> DevelopDatasetMessageResponse ModelHubDevelopsAddUserEvalCreate(ctx, datasetId).UserEvalMutationRequest(userEvalMutationRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	userEvalMutationRequest := *openapiclient.NewUserEvalMutationRequest("Name_example", "TemplateId_example", map[string]interface{}{"key": interface{}(123)}) // UserEvalMutationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsAddUserEvalCreate(context.Background(), datasetId).UserEvalMutationRequest(userEvalMutationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsAddUserEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsAddUserEvalCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsAddUserEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsAddUserEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **userEvalMutationRequest** | [**UserEvalMutationRequest**](UserEvalMutationRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsCloneDatasetCreate

> DatasetCopyResponse ModelHubDevelopsCloneDatasetCreate(ctx, datasetId).CloneDatasetRequest(cloneDatasetRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	cloneDatasetRequest := *openapiclient.NewCloneDatasetRequest() // CloneDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsCloneDatasetCreate(context.Background(), datasetId).CloneDatasetRequest(cloneDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsCloneDatasetCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsCloneDatasetCreate`: DatasetCopyResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsCloneDatasetCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsCloneDatasetCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **cloneDatasetRequest** | [**CloneDatasetRequest**](CloneDatasetRequest.md) |  | 

### Return type

[**DatasetCopyResponse**](DatasetCopyResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsCreateDatasetCreate

> DevelopDatasetMessageResponse ModelHubDevelopsCreateDatasetCreate(ctx, expDatasetId).CreateDatasetFromExperimentRequest(createDatasetFromExperimentRequest).Execute()





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
	expDatasetId := "expDatasetId_example" // string | 
	createDatasetFromExperimentRequest := *openapiclient.NewCreateDatasetFromExperimentRequest() // CreateDatasetFromExperimentRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsCreateDatasetCreate(context.Background(), expDatasetId).CreateDatasetFromExperimentRequest(createDatasetFromExperimentRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsCreateDatasetCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsCreateDatasetCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsCreateDatasetCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**expDatasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsCreateDatasetCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **createDatasetFromExperimentRequest** | [**CreateDatasetFromExperimentRequest**](CreateDatasetFromExperimentRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsCreateDatasetFromHuggingfaceCreate

> DatasetCreateStartedResponse ModelHubDevelopsCreateDatasetFromHuggingfaceCreate(ctx).HuggingFaceDatasetCreateRequest(huggingFaceDatasetCreateRequest).Execute()





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
	huggingFaceDatasetCreateRequest := *openapiclient.NewHuggingFaceDatasetCreateRequest("HuggingfaceDatasetName_example", "HuggingfaceDatasetSplit_example") // HuggingFaceDatasetCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsCreateDatasetFromHuggingfaceCreate(context.Background()).HuggingFaceDatasetCreateRequest(huggingFaceDatasetCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsCreateDatasetFromHuggingfaceCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsCreateDatasetFromHuggingfaceCreate`: DatasetCreateStartedResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsCreateDatasetFromHuggingfaceCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsCreateDatasetFromHuggingfaceCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **huggingFaceDatasetCreateRequest** | [**HuggingFaceDatasetCreateRequest**](HuggingFaceDatasetCreateRequest.md) |  | 

### Return type

[**DatasetCreateStartedResponse**](DatasetCreateStartedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsCreateSyntheticDatasetCreate

> SyntheticDatasetCreateStartedResponse ModelHubDevelopsCreateSyntheticDatasetCreate(ctx).SyntheticDatasetCreation(syntheticDatasetCreation).Execute()





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
	syntheticDatasetCreation := *openapiclient.NewSyntheticDatasetCreation(int32(123), []*string{nil}, map[string]interface{}{"key": interface{}(123)}) // SyntheticDatasetCreation | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsCreateSyntheticDatasetCreate(context.Background()).SyntheticDatasetCreation(syntheticDatasetCreation).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsCreateSyntheticDatasetCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsCreateSyntheticDatasetCreate`: SyntheticDatasetCreateStartedResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsCreateSyntheticDatasetCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsCreateSyntheticDatasetCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **syntheticDatasetCreation** | [**SyntheticDatasetCreation**](SyntheticDatasetCreation.md) |  | 

### Return type

[**SyntheticDatasetCreateStartedResponse**](SyntheticDatasetCreateStartedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsDatasetCreationProgressRead

> DatasetCreationProgressResponse ModelHubDevelopsDatasetCreationProgressRead(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsDatasetCreationProgressRead(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsDatasetCreationProgressRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsDatasetCreationProgressRead`: DatasetCreationProgressResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsDatasetCreationProgressRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsDatasetCreationProgressReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetCreationProgressResponse**](DatasetCreationProgressResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsDeleteDatasetDelete

> ModelHubDevelopsDeleteDatasetDelete(ctx).Execute()





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
	r, err := apiClient.ModelHubAPI.ModelHubDevelopsDeleteDatasetDelete(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsDeleteDatasetDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsDeleteDatasetDeleteRequest struct via the builder pattern


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


## ModelHubDevelopsDeleteTemplateEvalDelete

> ModelHubDevelopsDeleteTemplateEvalDelete(ctx, datasetId, evalId).Execute()





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
	datasetId := "datasetId_example" // string | 
	evalId := "evalId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubDevelopsDeleteTemplateEvalDelete(context.Background(), datasetId, evalId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsDeleteTemplateEvalDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsDeleteTemplateEvalDeleteRequest struct via the builder pattern


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


## ModelHubDevelopsDeleteUserEvalDelete

> ModelHubDevelopsDeleteUserEvalDelete(ctx, datasetId, evalId).Execute()





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
	datasetId := "datasetId_example" // string | 
	evalId := "evalId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubDevelopsDeleteUserEvalDelete(context.Background(), datasetId, evalId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsDeleteUserEvalDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsDeleteUserEvalDeleteRequest struct via the builder pattern


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


## ModelHubDevelopsEditAndRunUserEvalCreate

> DevelopDatasetMessageResponse ModelHubDevelopsEditAndRunUserEvalCreate(ctx, datasetId, evalId).UserEvalUpdateRequest(userEvalUpdateRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	evalId := "evalId_example" // string | 
	userEvalUpdateRequest := *openapiclient.NewUserEvalUpdateRequest(map[string]interface{}{"key": interface{}(123)}) // UserEvalUpdateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsEditAndRunUserEvalCreate(context.Background(), datasetId, evalId).UserEvalUpdateRequest(userEvalUpdateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsEditAndRunUserEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsEditAndRunUserEvalCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsEditAndRunUserEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsEditAndRunUserEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **userEvalUpdateRequest** | [**UserEvalUpdateRequest**](UserEvalUpdateRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsEditDatasetBehaviorUpdate

> DevelopDatasetMessageResponse ModelHubDevelopsEditDatasetBehaviorUpdate(ctx, datasetId).DatasetBehaviorRequest(datasetBehaviorRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetBehaviorRequest := *openapiclient.NewDatasetBehaviorRequest() // DatasetBehaviorRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsEditDatasetBehaviorUpdate(context.Background(), datasetId).DatasetBehaviorRequest(datasetBehaviorRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsEditDatasetBehaviorUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsEditDatasetBehaviorUpdate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsEditDatasetBehaviorUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsEditDatasetBehaviorUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetBehaviorRequest** | [**DatasetBehaviorRequest**](DatasetBehaviorRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsEditRunPromptColumnCreate

> DevelopDatasetMessageResponse ModelHubDevelopsEditRunPromptColumnCreate(ctx).EditRunPromptColumn(editRunPromptColumn).Execute()





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
	editRunPromptColumn := *openapiclient.NewEditRunPromptColumn("DatasetId_example", "ColumnId_example") // EditRunPromptColumn | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsEditRunPromptColumnCreate(context.Background()).EditRunPromptColumn(editRunPromptColumn).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsEditRunPromptColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsEditRunPromptColumnCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsEditRunPromptColumnCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsEditRunPromptColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **editRunPromptColumn** | [**EditRunPromptColumn**](EditRunPromptColumn.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsExtractJsonColumnCreate

> DynamicColumnCreateResponse ModelHubDevelopsExtractJsonColumnCreate(ctx, datasetId).ExtractJsonColumnRequest(extractJsonColumnRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	extractJsonColumnRequest := *openapiclient.NewExtractJsonColumnRequest("ColumnId_example", "JsonKey_example") // ExtractJsonColumnRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsExtractJsonColumnCreate(context.Background(), datasetId).ExtractJsonColumnRequest(extractJsonColumnRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsExtractJsonColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsExtractJsonColumnCreate`: DynamicColumnCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsExtractJsonColumnCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsExtractJsonColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **extractJsonColumnRequest** | [**ExtractJsonColumnRequest**](ExtractJsonColumnRequest.md) |  | 

### Return type

[**DynamicColumnCreateResponse**](DynamicColumnCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetCellDataCreate

> DatasetCellDataResponse ModelHubDevelopsGetCellDataCreate(ctx).DatasetCellDataRequest(datasetCellDataRequest).Execute()





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
	datasetCellDataRequest := *openapiclient.NewDatasetCellDataRequest([]string{"RowIds_example"}, []string{"ColumnIds_example"}) // DatasetCellDataRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetCellDataCreate(context.Background()).DatasetCellDataRequest(datasetCellDataRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetCellDataCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetCellDataCreate`: DatasetCellDataResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetCellDataCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetCellDataCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **datasetCellDataRequest** | [**DatasetCellDataRequest**](DatasetCellDataRequest.md) |  | 

### Return type

[**DatasetCellDataResponse**](DatasetCellDataResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetDerivedDatasetsRead

> DatasetExplanationSummaryResponse ModelHubDevelopsGetDerivedDatasetsRead(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetDerivedDatasetsRead(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetDerivedDatasetsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetDerivedDatasetsRead`: DatasetExplanationSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetDerivedDatasetsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetDerivedDatasetsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetExplanationSummaryResponse**](DatasetExplanationSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetEvalStructureRead

> EvalStructureResponse ModelHubDevelopsGetEvalStructureRead(ctx, datasetId, evalId).EvalType(evalType).Execute()





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
	datasetId := "datasetId_example" // string | 
	evalId := "evalId_example" // string | 
	evalType := "evalType_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetEvalStructureRead(context.Background(), datasetId, evalId).EvalType(evalType).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetEvalStructureRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetEvalStructureRead`: EvalStructureResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetEvalStructureRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetEvalStructureReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **evalType** | **string** |  | 

### Return type

[**EvalStructureResponse**](EvalStructureResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetEvalsListList

> EvalListResponse ModelHubDevelopsGetEvalsListList(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetEvalsListList(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetEvalsListList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetEvalsListList`: EvalListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetEvalsListList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetEvalsListListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalListResponse**](EvalListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetExperimentDatasetTableList

> DatasetTableResponse ModelHubDevelopsGetExperimentDatasetTableList(ctx, experimentDatasetId).Execute()





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
	experimentDatasetId := "experimentDatasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetExperimentDatasetTableList(context.Background(), experimentDatasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetExperimentDatasetTableList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetExperimentDatasetTableList`: DatasetTableResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetExperimentDatasetTableList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentDatasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetExperimentDatasetTableListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetTableResponse**](DatasetTableResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetFunctionListList

> EvalFunctionListResponse ModelHubDevelopsGetFunctionListList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetFunctionListList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetFunctionListList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetFunctionListList`: EvalFunctionListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetFunctionListList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetFunctionListListRequest struct via the builder pattern


### Return type

[**EvalFunctionListResponse**](EvalFunctionListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetHuggingfaceDatasetConfigCreate

> HuggingFaceDatasetConfigResponse ModelHubDevelopsGetHuggingfaceDatasetConfigCreate(ctx).HuggingFaceDatasetConfigRequest(huggingFaceDatasetConfigRequest).Execute()





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
	huggingFaceDatasetConfigRequest := *openapiclient.NewHuggingFaceDatasetConfigRequest("DatasetPath_example") // HuggingFaceDatasetConfigRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetHuggingfaceDatasetConfigCreate(context.Background()).HuggingFaceDatasetConfigRequest(huggingFaceDatasetConfigRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetHuggingfaceDatasetConfigCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetHuggingfaceDatasetConfigCreate`: HuggingFaceDatasetConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetHuggingfaceDatasetConfigCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetHuggingfaceDatasetConfigCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **huggingFaceDatasetConfigRequest** | [**HuggingFaceDatasetConfigRequest**](HuggingFaceDatasetConfigRequest.md) |  | 

### Return type

[**HuggingFaceDatasetConfigResponse**](HuggingFaceDatasetConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsGetRowDiffCreate

> ExperimentRowDiffResponse ModelHubDevelopsGetRowDiffCreate(ctx).DatasetRowDiffRequest(datasetRowDiffRequest).Execute()





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
	datasetRowDiffRequest := *openapiclient.NewDatasetRowDiffRequest("ExperimentId_example", []string{"ColumnIds_example"}, []string{"RowIds_example"}, []string{"CompareColumnIds_example"}) // DatasetRowDiffRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsGetRowDiffCreate(context.Background()).DatasetRowDiffRequest(datasetRowDiffRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsGetRowDiffCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsGetRowDiffCreate`: ExperimentRowDiffResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsGetRowDiffCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsGetRowDiffCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **datasetRowDiffRequest** | [**DatasetRowDiffRequest**](DatasetRowDiffRequest.md) |  | 

### Return type

[**ExperimentRowDiffResponse**](ExperimentRowDiffResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsPreviewRunEvalCreate

> EvalPreviewResponse ModelHubDevelopsPreviewRunEvalCreate(ctx, datasetId).PreviewRunEvalRequest(previewRunEvalRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	previewRunEvalRequest := *openapiclient.NewPreviewRunEvalRequest(map[string]interface{}{"key": interface{}(123)}, "TemplateId_example") // PreviewRunEvalRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsPreviewRunEvalCreate(context.Background(), datasetId).PreviewRunEvalRequest(previewRunEvalRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsPreviewRunEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsPreviewRunEvalCreate`: EvalPreviewResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsPreviewRunEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsPreviewRunEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **previewRunEvalRequest** | [**PreviewRunEvalRequest**](PreviewRunEvalRequest.md) |  | 

### Return type

[**EvalPreviewResponse**](EvalPreviewResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsPreviewRunPromptColumnCreate

> RunPromptColumnPreviewResponse ModelHubDevelopsPreviewRunPromptColumnCreate(ctx).PreviewRunPrompt(previewRunPrompt).Execute()





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
	previewRunPrompt := *openapiclient.NewPreviewRunPrompt("DatasetId_example", "Name_example") // PreviewRunPrompt | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsPreviewRunPromptColumnCreate(context.Background()).PreviewRunPrompt(previewRunPrompt).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsPreviewRunPromptColumnCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsPreviewRunPromptColumnCreate`: RunPromptColumnPreviewResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsPreviewRunPromptColumnCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsPreviewRunPromptColumnCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **previewRunPrompt** | [**PreviewRunPrompt**](PreviewRunPrompt.md) |  | 

### Return type

[**RunPromptColumnPreviewResponse**](RunPromptColumnPreviewResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsProviderStatusList

> ProviderStatusResponse ModelHubDevelopsProviderStatusList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsProviderStatusList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsProviderStatusList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsProviderStatusList`: ProviderStatusResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsProviderStatusList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsProviderStatusListRequest struct via the builder pattern


### Return type

[**ProviderStatusResponse**](ProviderStatusResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsRetrieveRunPromptColumnConfigList

> RunPromptColumnConfigResponse ModelHubDevelopsRetrieveRunPromptColumnConfigList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsRetrieveRunPromptColumnConfigList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsRetrieveRunPromptColumnConfigList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsRetrieveRunPromptColumnConfigList`: RunPromptColumnConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsRetrieveRunPromptColumnConfigList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsRetrieveRunPromptColumnConfigListRequest struct via the builder pattern


### Return type

[**RunPromptColumnConfigResponse**](RunPromptColumnConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsRetrieveRunPromptOptionsList

> RunPromptOptionsResponse ModelHubDevelopsRetrieveRunPromptOptionsList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsRetrieveRunPromptOptionsList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsRetrieveRunPromptOptionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsRetrieveRunPromptOptionsList`: RunPromptOptionsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsRetrieveRunPromptOptionsList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsRetrieveRunPromptOptionsListRequest struct via the builder pattern


### Return type

[**RunPromptOptionsResponse**](RunPromptOptionsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsStartEvalsProcessCreate

> DevelopDatasetMessageResponse ModelHubDevelopsStartEvalsProcessCreate(ctx, datasetId).StartEvalsProcessRequest(startEvalsProcessRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	startEvalsProcessRequest := *openapiclient.NewStartEvalsProcessRequest([]string{"UserEvalIds_example"}) // StartEvalsProcessRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsStartEvalsProcessCreate(context.Background(), datasetId).StartEvalsProcessRequest(startEvalsProcessRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsStartEvalsProcessCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsStartEvalsProcessCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsStartEvalsProcessCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsStartEvalsProcessCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **startEvalsProcessRequest** | [**StartEvalsProcessRequest**](StartEvalsProcessRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsStopUserEvalCreate

> DevelopDatasetMessageResponse ModelHubDevelopsStopUserEvalCreate(ctx, datasetId, evalId).StopUserEvalRequest(stopUserEvalRequest).Execute()

POST /develops/<dataset_id>/stop_user_eval/<eval_id>/ Stops a running evaluation by setting its status to Completed.



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
	datasetId := "datasetId_example" // string | 
	evalId := "evalId_example" // string | 
	stopUserEvalRequest := *openapiclient.NewStopUserEvalRequest() // StopUserEvalRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsStopUserEvalCreate(context.Background(), datasetId, evalId).StopUserEvalRequest(stopUserEvalRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsStopUserEvalCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsStopUserEvalCreate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsStopUserEvalCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**evalId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsStopUserEvalCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **stopUserEvalRequest** | [**StopUserEvalRequest**](StopUserEvalRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsSyntheticConfigList

> SyntheticDatasetConfigResponse ModelHubDevelopsSyntheticConfigList(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsSyntheticConfigList(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsSyntheticConfigList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsSyntheticConfigList`: SyntheticDatasetConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsSyntheticConfigList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsSyntheticConfigListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**SyntheticDatasetConfigResponse**](SyntheticDatasetConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsUpdateColumnNameUpdate

> DevelopDatasetMessageResponse ModelHubDevelopsUpdateColumnNameUpdate(ctx, datasetId, columnId).DatasetUpdateColumnNameRequest(datasetUpdateColumnNameRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	columnId := "columnId_example" // string | 
	datasetUpdateColumnNameRequest := *openapiclient.NewDatasetUpdateColumnNameRequest("NewColumnName_example") // DatasetUpdateColumnNameRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsUpdateColumnNameUpdate(context.Background(), datasetId, columnId).DatasetUpdateColumnNameRequest(datasetUpdateColumnNameRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsUpdateColumnNameUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsUpdateColumnNameUpdate`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsUpdateColumnNameUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**columnId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsUpdateColumnNameUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **datasetUpdateColumnNameRequest** | [**DatasetUpdateColumnNameRequest**](DatasetUpdateColumnNameRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsUpdateColumnTypeUpdate

> ColumnTypeConversionResponse ModelHubDevelopsUpdateColumnTypeUpdate(ctx, datasetId, columnId).DatasetUpdateColumnTypeRequest(datasetUpdateColumnTypeRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	columnId := "columnId_example" // string | 
	datasetUpdateColumnTypeRequest := *openapiclient.NewDatasetUpdateColumnTypeRequest("NewColumnType_example") // DatasetUpdateColumnTypeRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsUpdateColumnTypeUpdate(context.Background(), datasetId, columnId).DatasetUpdateColumnTypeRequest(datasetUpdateColumnTypeRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsUpdateColumnTypeUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsUpdateColumnTypeUpdate`: ColumnTypeConversionResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsUpdateColumnTypeUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**columnId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsUpdateColumnTypeUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **datasetUpdateColumnTypeRequest** | [**DatasetUpdateColumnTypeRequest**](DatasetUpdateColumnTypeRequest.md) |  | 

### Return type

[**ColumnTypeConversionResponse**](ColumnTypeConversionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubDevelopsUpdateSyntheticConfigUpdate

> SyntheticDatasetUpdateResponse ModelHubDevelopsUpdateSyntheticConfigUpdate(ctx, datasetId).SyntheticDatasetConfig(syntheticDatasetConfig).Execute()





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
	datasetId := "datasetId_example" // string | 
	syntheticDatasetConfig := *openapiclient.NewSyntheticDatasetConfig(int32(123), []*string{nil}, map[string]interface{}{"key": interface{}(123)}) // SyntheticDatasetConfig | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubDevelopsUpdateSyntheticConfigUpdate(context.Background(), datasetId).SyntheticDatasetConfig(syntheticDatasetConfig).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubDevelopsUpdateSyntheticConfigUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubDevelopsUpdateSyntheticConfigUpdate`: SyntheticDatasetUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubDevelopsUpdateSyntheticConfigUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubDevelopsUpdateSyntheticConfigUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **syntheticDatasetConfig** | [**SyntheticDatasetConfig**](SyntheticDatasetConfig.md) |  | 

### Return type

[**SyntheticDatasetUpdateResponse**](SyntheticDatasetUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesBulkDeleteCreate

> EvalTemplateBulkDeleteResponse ModelHubEvalTemplatesBulkDeleteCreate(ctx).EvalTemplateBulkDeleteRequest(evalTemplateBulkDeleteRequest).Execute()

POST /model-hub/eval-templates/bulk-delete/



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
	evalTemplateBulkDeleteRequest := *openapiclient.NewEvalTemplateBulkDeleteRequest([]string{"TemplateIds_example"}) // EvalTemplateBulkDeleteRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesBulkDeleteCreate(context.Background()).EvalTemplateBulkDeleteRequest(evalTemplateBulkDeleteRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesBulkDeleteCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesBulkDeleteCreate`: EvalTemplateBulkDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesBulkDeleteCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesBulkDeleteCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **evalTemplateBulkDeleteRequest** | [**EvalTemplateBulkDeleteRequest**](EvalTemplateBulkDeleteRequest.md) |  | 

### Return type

[**EvalTemplateBulkDeleteResponse**](EvalTemplateBulkDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCompositeExecuteAdhocCreate

> CompositeEvalExecuteResponse ModelHubEvalTemplatesCompositeExecuteAdhocCreate(ctx).CompositeEvalAdhocExecuteRequest(compositeEvalAdhocExecuteRequest).Execute()

POST /model-hub/eval-templates/composite/execute-adhoc/



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
	compositeEvalAdhocExecuteRequest := *openapiclient.NewCompositeEvalAdhocExecuteRequest(map[string]interface{}{"key": interface{}(123)}, []string{"ChildTemplateIds_example"}) // CompositeEvalAdhocExecuteRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteAdhocCreate(context.Background()).CompositeEvalAdhocExecuteRequest(compositeEvalAdhocExecuteRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteAdhocCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCompositeExecuteAdhocCreate`: CompositeEvalExecuteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteAdhocCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCompositeExecuteAdhocCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **compositeEvalAdhocExecuteRequest** | [**CompositeEvalAdhocExecuteRequest**](CompositeEvalAdhocExecuteRequest.md) |  | 

### Return type

[**CompositeEvalExecuteResponse**](CompositeEvalExecuteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCompositeExecuteCreate

> CompositeEvalExecuteResponse ModelHubEvalTemplatesCompositeExecuteCreate(ctx, templateId).CompositeEvalExecuteRequest(compositeEvalExecuteRequest).Execute()

POST /model-hub/eval-templates/<template_id>/composite/execute/



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
	templateId := "templateId_example" // string | 
	compositeEvalExecuteRequest := *openapiclient.NewCompositeEvalExecuteRequest(map[string]interface{}{"key": interface{}(123)}) // CompositeEvalExecuteRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteCreate(context.Background(), templateId).CompositeEvalExecuteRequest(compositeEvalExecuteRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCompositeExecuteCreate`: CompositeEvalExecuteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCompositeExecuteCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCompositeExecuteCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compositeEvalExecuteRequest** | [**CompositeEvalExecuteRequest**](CompositeEvalExecuteRequest.md) |  | 

### Return type

[**CompositeEvalExecuteResponse**](CompositeEvalExecuteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCompositeList

> CompositeEvalDetailResponse ModelHubEvalTemplatesCompositeList(ctx, templateId).Execute()

GET /model-hub/eval-templates/<id>/composite/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCompositeList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCompositeList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCompositeList`: CompositeEvalDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCompositeList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCompositeListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CompositeEvalDetailResponse**](CompositeEvalDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCompositePartialUpdate

> CompositeEvalDetailResponse ModelHubEvalTemplatesCompositePartialUpdate(ctx, templateId).CompositeEvalUpdateRequest(compositeEvalUpdateRequest).Execute()

PATCH — partial update of a composite eval.



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
	templateId := "templateId_example" // string | 
	compositeEvalUpdateRequest := *openapiclient.NewCompositeEvalUpdateRequest() // CompositeEvalUpdateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCompositePartialUpdate(context.Background(), templateId).CompositeEvalUpdateRequest(compositeEvalUpdateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCompositePartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCompositePartialUpdate`: CompositeEvalDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCompositePartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCompositePartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **compositeEvalUpdateRequest** | [**CompositeEvalUpdateRequest**](CompositeEvalUpdateRequest.md) |  | 

### Return type

[**CompositeEvalDetailResponse**](CompositeEvalDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCreateCompositeCreate

> CompositeEvalCreateResponse ModelHubEvalTemplatesCreateCompositeCreate(ctx).CompositeEvalCreateRequest(compositeEvalCreateRequest).Execute()

POST /model-hub/eval-templates/create-composite/



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
	compositeEvalCreateRequest := *openapiclient.NewCompositeEvalCreateRequest("Name_example", []string{"ChildTemplateIds_example"}) // CompositeEvalCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCreateCompositeCreate(context.Background()).CompositeEvalCreateRequest(compositeEvalCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCreateCompositeCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCreateCompositeCreate`: CompositeEvalCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCreateCompositeCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCreateCompositeCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **compositeEvalCreateRequest** | [**CompositeEvalCreateRequest**](CompositeEvalCreateRequest.md) |  | 

### Return type

[**CompositeEvalCreateResponse**](CompositeEvalCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesCreateV2Create

> EvalTemplateCreateResponse ModelHubEvalTemplatesCreateV2Create(ctx).EvalTemplateCreateV2Request(evalTemplateCreateV2Request).Execute()

POST /model-hub/eval-templates/create-v2/



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
	evalTemplateCreateV2Request := *openapiclient.NewEvalTemplateCreateV2Request() // EvalTemplateCreateV2Request | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesCreateV2Create(context.Background()).EvalTemplateCreateV2Request(evalTemplateCreateV2Request).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesCreateV2Create``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesCreateV2Create`: EvalTemplateCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesCreateV2Create`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesCreateV2CreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **evalTemplateCreateV2Request** | [**EvalTemplateCreateV2Request**](EvalTemplateCreateV2Request.md) |  | 

### Return type

[**EvalTemplateCreateResponse**](EvalTemplateCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesDetailList

> EvalTemplateDetailResponse ModelHubEvalTemplatesDetailList(ctx, templateId).Execute()

GET /model-hub/eval-templates/<id>/detail/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesDetailList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesDetailList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesDetailList`: EvalTemplateDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesDetailList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesDetailListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalTemplateDetailResponse**](EvalTemplateDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesFeedbackListList

> EvalFeedbackListResponse ModelHubEvalTemplatesFeedbackListList(ctx, templateId).Execute()

GET /model-hub/eval-templates/<id>/feedback-list/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesFeedbackListList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesFeedbackListList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesFeedbackListList`: EvalFeedbackListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesFeedbackListList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesFeedbackListListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalFeedbackListResponse**](EvalFeedbackListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesGroundTruthConfigList

> GroundTruthConfigResponse ModelHubEvalTemplatesGroundTruthConfigList(ctx, templateId).Execute()

GET/PUT /model-hub/eval-templates/<id>/ground-truth-config/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesGroundTruthConfigList`: GroundTruthConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesGroundTruthConfigListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**GroundTruthConfigResponse**](GroundTruthConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesGroundTruthConfigUpdate

> GroundTruthConfigResponse ModelHubEvalTemplatesGroundTruthConfigUpdate(ctx, templateId).GroundTruthConfigRequest(groundTruthConfigRequest).Execute()

GET/PUT /model-hub/eval-templates/<id>/ground-truth-config/



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
	templateId := "templateId_example" // string | 
	groundTruthConfigRequest := *openapiclient.NewGroundTruthConfigRequest() // GroundTruthConfigRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigUpdate(context.Background(), templateId).GroundTruthConfigRequest(groundTruthConfigRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesGroundTruthConfigUpdate`: GroundTruthConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesGroundTruthConfigUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesGroundTruthConfigUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **groundTruthConfigRequest** | [**GroundTruthConfigRequest**](GroundTruthConfigRequest.md) |  | 

### Return type

[**GroundTruthConfigResponse**](GroundTruthConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesGroundTruthList

> GroundTruthListResponse ModelHubEvalTemplatesGroundTruthList(ctx, templateId).Execute()





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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesGroundTruthList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesGroundTruthList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesGroundTruthList`: GroundTruthListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesGroundTruthList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesGroundTruthListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**GroundTruthListResponse**](GroundTruthListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesGroundTruthUploadCreate

> GroundTruthUploadResponse ModelHubEvalTemplatesGroundTruthUploadCreate(ctx, templateId).GroundTruthUploadRequest(groundTruthUploadRequest).Execute()

POST /model-hub/eval-templates/<id>/ground-truth/upload/



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
	templateId := "templateId_example" // string | 
	groundTruthUploadRequest := *openapiclient.NewGroundTruthUploadRequest() // GroundTruthUploadRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesGroundTruthUploadCreate(context.Background(), templateId).GroundTruthUploadRequest(groundTruthUploadRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesGroundTruthUploadCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesGroundTruthUploadCreate`: GroundTruthUploadResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesGroundTruthUploadCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesGroundTruthUploadCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **groundTruthUploadRequest** | [**GroundTruthUploadRequest**](GroundTruthUploadRequest.md) |  | 

### Return type

[**GroundTruthUploadResponse**](GroundTruthUploadResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesListChartsCreate

> EvalTemplateListChartsResponse ModelHubEvalTemplatesListChartsCreate(ctx).EvalTemplateListChartsRequest(evalTemplateListChartsRequest).Execute()

POST /model-hub/eval-templates/list-charts/



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
	evalTemplateListChartsRequest := *openapiclient.NewEvalTemplateListChartsRequest([]string{"TemplateIds_example"}) // EvalTemplateListChartsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesListChartsCreate(context.Background()).EvalTemplateListChartsRequest(evalTemplateListChartsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesListChartsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesListChartsCreate`: EvalTemplateListChartsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesListChartsCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesListChartsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **evalTemplateListChartsRequest** | [**EvalTemplateListChartsRequest**](EvalTemplateListChartsRequest.md) |  | 

### Return type

[**EvalTemplateListChartsResponse**](EvalTemplateListChartsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesListCreate

> EvalTemplateListResponse ModelHubEvalTemplatesListCreate(ctx).EvalListRequest(evalListRequest).Execute()

POST /model-hub/eval-templates/list/



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
	evalListRequest := *openapiclient.NewEvalListRequest() // EvalListRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesListCreate(context.Background()).EvalListRequest(evalListRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesListCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesListCreate`: EvalTemplateListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesListCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesListCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **evalListRequest** | [**EvalListRequest**](EvalListRequest.md) |  | 

### Return type

[**EvalTemplateListResponse**](EvalTemplateListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesUpdateUpdate

> EvalTemplateUpdateResponse ModelHubEvalTemplatesUpdateUpdate(ctx, templateId).EvalTemplateUpdateV2Request(evalTemplateUpdateV2Request).Execute()

PUT /model-hub/eval-templates/<id>/update/



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
	templateId := "templateId_example" // string | 
	evalTemplateUpdateV2Request := *openapiclient.NewEvalTemplateUpdateV2Request() // EvalTemplateUpdateV2Request | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesUpdateUpdate(context.Background(), templateId).EvalTemplateUpdateV2Request(evalTemplateUpdateV2Request).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesUpdateUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesUpdateUpdate`: EvalTemplateUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesUpdateUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesUpdateUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **evalTemplateUpdateV2Request** | [**EvalTemplateUpdateV2Request**](EvalTemplateUpdateV2Request.md) |  | 

### Return type

[**EvalTemplateUpdateResponse**](EvalTemplateUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesUsageList

> EvalUsageStatsResponse ModelHubEvalTemplatesUsageList(ctx, templateId).Execute()

GET /model-hub/eval-templates/<id>/usage/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesUsageList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesUsageList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesUsageList`: EvalUsageStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesUsageList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesUsageListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalUsageStatsResponse**](EvalUsageStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesVersionsCreateCreate

> EvalTemplateVersionResponse ModelHubEvalTemplatesVersionsCreateCreate(ctx, templateId).EvalTemplateVersionCreateRequest(evalTemplateVersionCreateRequest).Execute()

POST /model-hub/eval-templates/<id>/versions/create/



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
	templateId := "templateId_example" // string | 
	evalTemplateVersionCreateRequest := *openapiclient.NewEvalTemplateVersionCreateRequest() // EvalTemplateVersionCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesVersionsCreateCreate(context.Background(), templateId).EvalTemplateVersionCreateRequest(evalTemplateVersionCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesVersionsCreateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesVersionsCreateCreate`: EvalTemplateVersionResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesVersionsCreateCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesVersionsCreateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **evalTemplateVersionCreateRequest** | [**EvalTemplateVersionCreateRequest**](EvalTemplateVersionCreateRequest.md) |  | 

### Return type

[**EvalTemplateVersionResponse**](EvalTemplateVersionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesVersionsList

> EvalTemplateVersionListResponse ModelHubEvalTemplatesVersionsList(ctx, templateId).Execute()

GET /model-hub/eval-templates/<id>/versions/



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
	templateId := "templateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesVersionsList(context.Background(), templateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesVersionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesVersionsList`: EvalTemplateVersionListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesVersionsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesVersionsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalTemplateVersionListResponse**](EvalTemplateVersionListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesVersionsRestoreCreate

> EvalTemplateVersionRestoreResponse ModelHubEvalTemplatesVersionsRestoreCreate(ctx, templateId, versionId).Body(body).Execute()

POST /model-hub/eval-templates/<id>/versions/<version_id>/restore/



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
	templateId := "templateId_example" // string | 
	versionId := "versionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesVersionsRestoreCreate(context.Background(), templateId, versionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesVersionsRestoreCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesVersionsRestoreCreate`: EvalTemplateVersionRestoreResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesVersionsRestoreCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesVersionsRestoreCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**EvalTemplateVersionRestoreResponse**](EvalTemplateVersionRestoreResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubEvalTemplatesVersionsSetDefaultUpdate

> EvalTemplateVersionResponse ModelHubEvalTemplatesVersionsSetDefaultUpdate(ctx, templateId, versionId).Body(body).Execute()

PUT /model-hub/eval-templates/<id>/versions/<version_id>/set-default/



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
	templateId := "templateId_example" // string | 
	versionId := "versionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubEvalTemplatesVersionsSetDefaultUpdate(context.Background(), templateId, versionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubEvalTemplatesVersionsSetDefaultUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubEvalTemplatesVersionsSetDefaultUpdate`: EvalTemplateVersionResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubEvalTemplatesVersionsSetDefaultUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubEvalTemplatesVersionsSetDefaultUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**EvalTemplateVersionResponse**](EvalTemplateVersionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2DerivedVariablesList

> ExperimentDerivedVariablesResponse ModelHubExperimentsV2DerivedVariablesList(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2DerivedVariablesList(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2DerivedVariablesList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2DerivedVariablesList`: ExperimentDerivedVariablesResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2DerivedVariablesList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2DerivedVariablesListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentDerivedVariablesResponse**](ExperimentDerivedVariablesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2EvaluationsStatsList

> ExperimentEvaluationStatsResponse ModelHubExperimentsV2EvaluationsStatsList(ctx, experimentId, evaluationId).Execute()





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
	experimentId := "experimentId_example" // string | 
	evaluationId := "evaluationId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2EvaluationsStatsList(context.Background(), experimentId, evaluationId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2EvaluationsStatsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2EvaluationsStatsList`: ExperimentEvaluationStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2EvaluationsStatsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 
**evaluationId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2EvaluationsStatsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**ExperimentEvaluationStatsResponse**](ExperimentEvaluationStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2FeedbackCreate

> ExperimentFeedbackCreateResponse ModelHubExperimentsV2FeedbackCreate(ctx, experimentId).Feedback(feedback).Execute()





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
	experimentId := "experimentId_example" // string | 
	feedback := *openapiclient.NewFeedback("SourceId_example", "Source_example", "Value_example") // Feedback | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2FeedbackCreate(context.Background(), experimentId).Feedback(feedback).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2FeedbackCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2FeedbackCreate`: ExperimentFeedbackCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2FeedbackCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2FeedbackCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **feedback** | [**Feedback**](Feedback.md) |  | 

### Return type

[**ExperimentFeedbackCreateResponse**](ExperimentFeedbackCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2FeedbackGetFeedbackDetailsList

> ExperimentFeedbackDetailsResponse ModelHubExperimentsV2FeedbackGetFeedbackDetailsList(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2FeedbackGetFeedbackDetailsList(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2FeedbackGetFeedbackDetailsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2FeedbackGetFeedbackDetailsList`: ExperimentFeedbackDetailsResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2FeedbackGetFeedbackDetailsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2FeedbackGetFeedbackDetailsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentFeedbackDetailsResponse**](ExperimentFeedbackDetailsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2FeedbackGetTemplateList

> ExperimentFeedbackTemplateResponse ModelHubExperimentsV2FeedbackGetTemplateList(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2FeedbackGetTemplateList(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2FeedbackGetTemplateList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2FeedbackGetTemplateList`: ExperimentFeedbackTemplateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2FeedbackGetTemplateList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2FeedbackGetTemplateListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentFeedbackTemplateResponse**](ExperimentFeedbackTemplateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2FeedbackSubmitFeedbackCreate

> ExperimentFeedbackSubmitResponse ModelHubExperimentsV2FeedbackSubmitFeedbackCreate(ctx, experimentId).ExperimentFeedbackSubmitRequest(experimentFeedbackSubmitRequest).Execute()





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
	experimentId := "experimentId_example" // string | 
	experimentFeedbackSubmitRequest := *openapiclient.NewExperimentFeedbackSubmitRequest("ActionType_example", "FeedbackId_example", "UserEvalMetricId_example") // ExperimentFeedbackSubmitRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2FeedbackSubmitFeedbackCreate(context.Background(), experimentId).ExperimentFeedbackSubmitRequest(experimentFeedbackSubmitRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2FeedbackSubmitFeedbackCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2FeedbackSubmitFeedbackCreate`: ExperimentFeedbackSubmitResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2FeedbackSubmitFeedbackCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2FeedbackSubmitFeedbackCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **experimentFeedbackSubmitRequest** | [**ExperimentFeedbackSubmitRequest**](ExperimentFeedbackSubmitRequest.md) |  | 

### Return type

[**ExperimentFeedbackSubmitResponse**](ExperimentFeedbackSubmitResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2RerunCellsCreate

> ExperimentWorkflowResponse ModelHubExperimentsV2RerunCellsCreate(ctx, experimentId).ExperimentRerunCells(experimentRerunCells).Execute()

Rerun specific cells or columns in a V2 experiment.



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
	experimentId := "experimentId_example" // string | 
	experimentRerunCells := *openapiclient.NewExperimentRerunCells() // ExperimentRerunCells | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2RerunCellsCreate(context.Background(), experimentId).ExperimentRerunCells(experimentRerunCells).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2RerunCellsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2RerunCellsCreate`: ExperimentWorkflowResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2RerunCellsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2RerunCellsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **experimentRerunCells** | [**ExperimentRerunCells**](ExperimentRerunCells.md) |  | 

### Return type

[**ExperimentWorkflowResponse**](ExperimentWorkflowResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2RowDiffCreate

> ExperimentRowDiffResponse ModelHubExperimentsV2RowDiffCreate(ctx).DatasetRowDiffRequest(datasetRowDiffRequest).Execute()





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
	datasetRowDiffRequest := *openapiclient.NewDatasetRowDiffRequest("ExperimentId_example", []string{"ColumnIds_example"}, []string{"RowIds_example"}, []string{"CompareColumnIds_example"}) // DatasetRowDiffRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2RowDiffCreate(context.Background()).DatasetRowDiffRequest(datasetRowDiffRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2RowDiffCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2RowDiffCreate`: ExperimentRowDiffResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2RowDiffCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2RowDiffCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **datasetRowDiffRequest** | [**DatasetRowDiffRequest**](DatasetRowDiffRequest.md) |  | 

### Return type

[**ExperimentRowDiffResponse**](ExperimentRowDiffResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2SuggestNameRead

> ExperimentNameSuggestionResponse ModelHubExperimentsV2SuggestNameRead(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2SuggestNameRead(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2SuggestNameRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2SuggestNameRead`: ExperimentNameSuggestionResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2SuggestNameRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2SuggestNameReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentNameSuggestionResponse**](ExperimentNameSuggestionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubExperimentsV2ValidateNameList

> ExperimentNameValidationResponse ModelHubExperimentsV2ValidateNameList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubExperimentsV2ValidateNameList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubExperimentsV2ValidateNameList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubExperimentsV2ValidateNameList`: ExperimentNameValidationResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubExperimentsV2ValidateNameList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubExperimentsV2ValidateNameListRequest struct via the builder pattern


### Return type

[**ExperimentNameValidationResponse**](ExperimentNameValidationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBaseCreate

> LegacyKnowledgeBaseCreateResponse ModelHubKnowledgeBaseCreate(ctx).LegacyKnowledgeBaseMutationRequest(legacyKnowledgeBaseMutationRequest).Execute()





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
	legacyKnowledgeBaseMutationRequest := *openapiclient.NewLegacyKnowledgeBaseMutationRequest() // LegacyKnowledgeBaseMutationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseCreate(context.Background()).LegacyKnowledgeBaseMutationRequest(legacyKnowledgeBaseMutationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBaseCreate`: LegacyKnowledgeBaseCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBaseCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **legacyKnowledgeBaseMutationRequest** | [**LegacyKnowledgeBaseMutationRequest**](LegacyKnowledgeBaseMutationRequest.md) |  | 

### Return type

[**LegacyKnowledgeBaseCreateResponse**](LegacyKnowledgeBaseCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBaseDelete

> ModelHubKnowledgeBaseDelete(ctx).Execute()





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
	r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseDelete(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseDeleteRequest struct via the builder pattern


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


## ModelHubKnowledgeBaseFilesCreate

> LegacyKnowledgeBaseFilesResponse ModelHubKnowledgeBaseFilesCreate(ctx).LegacyKnowledgeBaseFilesRequest(legacyKnowledgeBaseFilesRequest).Execute()





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
	legacyKnowledgeBaseFilesRequest := *openapiclient.NewLegacyKnowledgeBaseFilesRequest("KbId_example") // LegacyKnowledgeBaseFilesRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseFilesCreate(context.Background()).LegacyKnowledgeBaseFilesRequest(legacyKnowledgeBaseFilesRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseFilesCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBaseFilesCreate`: LegacyKnowledgeBaseFilesResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBaseFilesCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseFilesCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **legacyKnowledgeBaseFilesRequest** | [**LegacyKnowledgeBaseFilesRequest**](LegacyKnowledgeBaseFilesRequest.md) |  | 

### Return type

[**LegacyKnowledgeBaseFilesResponse**](LegacyKnowledgeBaseFilesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBaseFilesDelete

> ModelHubKnowledgeBaseFilesDelete(ctx).Execute()





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
	r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseFilesDelete(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseFilesDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseFilesDeleteRequest struct via the builder pattern


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


## ModelHubKnowledgeBaseGetList

> LegacyKnowledgeBaseTableResponse ModelHubKnowledgeBaseGetList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseGetList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseGetList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBaseGetList`: LegacyKnowledgeBaseTableResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBaseGetList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseGetListRequest struct via the builder pattern


### Return type

[**LegacyKnowledgeBaseTableResponse**](LegacyKnowledgeBaseTableResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBaseList

> LegacyKnowledgeBaseSdkCodeResponse ModelHubKnowledgeBaseList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBaseList`: LegacyKnowledgeBaseSdkCodeResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBaseList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseListRequest struct via the builder pattern


### Return type

[**LegacyKnowledgeBaseSdkCodeResponse**](LegacyKnowledgeBaseSdkCodeResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBaseListList

> LegacyKnowledgeBaseListResponse ModelHubKnowledgeBaseListList(ctx).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBaseListList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBaseListList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBaseListList`: LegacyKnowledgeBaseListResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBaseListList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBaseListListRequest struct via the builder pattern


### Return type

[**LegacyKnowledgeBaseListResponse**](LegacyKnowledgeBaseListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubKnowledgeBasePartialUpdate

> LegacyKnowledgeBaseMutationResponse ModelHubKnowledgeBasePartialUpdate(ctx).LegacyKnowledgeBaseMutationRequest(legacyKnowledgeBaseMutationRequest).Execute()





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
	legacyKnowledgeBaseMutationRequest := *openapiclient.NewLegacyKnowledgeBaseMutationRequest() // LegacyKnowledgeBaseMutationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubKnowledgeBasePartialUpdate(context.Background()).LegacyKnowledgeBaseMutationRequest(legacyKnowledgeBaseMutationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubKnowledgeBasePartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubKnowledgeBasePartialUpdate`: LegacyKnowledgeBaseMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubKnowledgeBasePartialUpdate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubKnowledgeBasePartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **legacyKnowledgeBaseMutationRequest** | [**LegacyKnowledgeBaseMutationRequest**](LegacyKnowledgeBaseMutationRequest.md) |  | 

### Return type

[**LegacyKnowledgeBaseMutationResponse**](LegacyKnowledgeBaseMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptHistoryExecutionsGetExecutionDetails

> ModelHubPromptHistoryExecutionsList200Response ModelHubPromptHistoryExecutionsGetExecutionDetails(ctx, executionId).TemplateName(templateName).TemplateVersion(templateVersion).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()





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
	executionId := "executionId_example" // string | 
	templateName := "templateName_example" // string |  (optional)
	templateVersion := "templateVersion_example" // string |  (optional)
	createdAt := "createdAt_example" // string |  (optional)
	search := "search_example" // string | A search term. (optional)
	ordering := "ordering_example" // string | Which field to use when ordering the results. (optional)
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptHistoryExecutionsGetExecutionDetails(context.Background(), executionId).TemplateName(templateName).TemplateVersion(templateVersion).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptHistoryExecutionsGetExecutionDetails``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptHistoryExecutionsGetExecutionDetails`: ModelHubPromptHistoryExecutionsList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptHistoryExecutionsGetExecutionDetails`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**executionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptHistoryExecutionsGetExecutionDetailsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **templateName** | **string** |  | 
 **templateVersion** | **string** |  | 
 **createdAt** | **string** |  | 
 **search** | **string** | A search term. | 
 **ordering** | **string** | Which field to use when ordering the results. | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptHistoryExecutionsList200Response**](ModelHubPromptHistoryExecutionsList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptHistoryExecutionsList

> ModelHubPromptHistoryExecutionsList200Response ModelHubPromptHistoryExecutionsList(ctx).TemplateName(templateName).TemplateVersion(templateVersion).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()





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
	templateName := "templateName_example" // string |  (optional)
	templateVersion := "templateVersion_example" // string |  (optional)
	createdAt := "createdAt_example" // string |  (optional)
	search := "search_example" // string | A search term. (optional)
	ordering := "ordering_example" // string | Which field to use when ordering the results. (optional)
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptHistoryExecutionsList(context.Background()).TemplateName(templateName).TemplateVersion(templateVersion).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptHistoryExecutionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptHistoryExecutionsList`: ModelHubPromptHistoryExecutionsList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptHistoryExecutionsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptHistoryExecutionsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **templateName** | **string** |  | 
 **templateVersion** | **string** |  | 
 **createdAt** | **string** |  | 
 **search** | **string** | A search term. | 
 **ordering** | **string** | Which field to use when ordering the results. | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptHistoryExecutionsList200Response**](ModelHubPromptHistoryExecutionsList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptHistoryExecutionsRead

> PromptHistoryExecution ModelHubPromptHistoryExecutionsRead(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt version.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptHistoryExecutionsRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptHistoryExecutionsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptHistoryExecutionsRead`: PromptHistoryExecution
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptHistoryExecutionsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt version. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptHistoryExecutionsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptHistoryExecution**](PromptHistoryExecution.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsAssignLabelById

> PromptLabel ModelHubPromptLabelsAssignLabelById(ctx, templateId, labelId).PromptLabel(promptLabel).Execute()





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
	templateId := "templateId_example" // string | 
	labelId := "labelId_example" // string | 
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsAssignLabelById(context.Background(), templateId, labelId).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsAssignLabelById``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsAssignLabelById`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsAssignLabelById`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**templateId** | **string** |  | 
**labelId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsAssignLabelByIdRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsAssignMultipleLabels

> PromptLabel ModelHubPromptLabelsAssignMultipleLabels(ctx).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsAssignMultipleLabels(context.Background()).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsAssignMultipleLabels``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsAssignMultipleLabels`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsAssignMultipleLabels`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsAssignMultipleLabelsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsCreate

> PromptLabel ModelHubPromptLabelsCreate(ctx).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsCreate(context.Background()).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsCreate`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsCreateSystemLabels

> PromptLabel ModelHubPromptLabelsCreateSystemLabels(ctx).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsCreateSystemLabels(context.Background()).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsCreateSystemLabels``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsCreateSystemLabels`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsCreateSystemLabels`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsCreateSystemLabelsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsDelete

> ModelHubPromptLabelsDelete(ctx, id).Execute()





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
	r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsDelete``: %v\n", err)
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

Other parameters are passed through a pointer to a apiModelHubPromptLabelsDeleteRequest struct via the builder pattern


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


## ModelHubPromptLabelsGetByName

> ModelHubPromptLabelsList200Response ModelHubPromptLabelsGetByName(ctx).Page(page).Limit(limit).Execute()

Fetch a prompt version by template name and either explicit version or label.



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
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsGetByName(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsGetByName``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsGetByName`: ModelHubPromptLabelsList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsGetByName`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsGetByNameRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptLabelsList200Response**](ModelHubPromptLabelsList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsList

> ModelHubPromptLabelsList200Response ModelHubPromptLabelsList(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsList(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsList`: ModelHubPromptLabelsList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptLabelsList200Response**](ModelHubPromptLabelsList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsPartialUpdate

> PromptLabel ModelHubPromptLabelsPartialUpdate(ctx, id).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsPartialUpdate(context.Background(), id).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsPartialUpdate`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsRead

> PromptLabel ModelHubPromptLabelsRead(ctx, id).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsRead`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsRemoveLabelFromVersion

> PromptLabel ModelHubPromptLabelsRemoveLabelFromVersion(ctx).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsRemoveLabelFromVersion(context.Background()).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsRemoveLabelFromVersion``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsRemoveLabelFromVersion`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsRemoveLabelFromVersion`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsRemoveLabelFromVersionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsSetDefault

> PromptLabel ModelHubPromptLabelsSetDefault(ctx).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsSetDefault(context.Background()).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsSetDefault``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsSetDefault`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsSetDefault`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsSetDefaultRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsTemplateLabels

> ModelHubPromptLabelsList200Response ModelHubPromptLabelsTemplateLabels(ctx).Page(page).Limit(limit).Execute()





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
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsTemplateLabels(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsTemplateLabels``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsTemplateLabels`: ModelHubPromptLabelsList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsTemplateLabels`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsTemplateLabelsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptLabelsList200Response**](ModelHubPromptLabelsList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptLabelsUpdate

> PromptLabel ModelHubPromptLabelsUpdate(ctx, id).PromptLabel(promptLabel).Execute()





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
	promptLabel := *openapiclient.NewPromptLabel("Name_example", "Type_example") // PromptLabel | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptLabelsUpdate(context.Background(), id).PromptLabel(promptLabel).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptLabelsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptLabelsUpdate`: PromptLabel
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptLabelsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptLabelsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptLabel** | [**PromptLabel**](PromptLabel.md) |  | 

### Return type

[**PromptLabel**](PromptLabel.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesAddNewDraft

> PromptTemplate ModelHubPromptTemplatesAddNewDraft(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesAddNewDraft(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesAddNewDraft``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesAddNewDraft`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesAddNewDraft`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesAddNewDraftRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesAnalyzePrompt

> PromptTemplate ModelHubPromptTemplatesAnalyzePrompt(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesAnalyzePrompt(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesAnalyzePrompt``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesAnalyzePrompt`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesAnalyzePrompt`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesAnalyzePromptRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesBulkDelete

> PromptTemplate ModelHubPromptTemplatesBulkDelete(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesBulkDelete(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesBulkDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesBulkDelete`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesBulkDelete`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesBulkDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesCommit

> PromptTemplate ModelHubPromptTemplatesCommit(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesCommit(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesCommit``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesCommit`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesCommit`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesCommitRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesCompareVersions

> PromptTemplate ModelHubPromptTemplatesCompareVersions(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesCompareVersions(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesCompareVersions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesCompareVersions`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesCompareVersions`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesCompareVersionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesCreate

> PromptTemplate ModelHubPromptTemplatesCreate(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesCreate(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesCreate`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesCreateDraft

> PromptTemplate ModelHubPromptTemplatesCreateDraft(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesCreateDraft(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesCreateDraft``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesCreateDraft`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesCreateDraft`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesCreateDraftRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesDelete

> ModelHubPromptTemplatesDelete(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDeleteRequest struct via the builder pattern


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


## ModelHubPromptTemplatesDeleteEvaluationConfig

> ModelHubPromptTemplatesDeleteEvaluationConfig(ctx, id).Execute()

Delete an evaluation configuration by name from a PromptTemplate.



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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDeleteEvaluationConfig(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDeleteEvaluationConfig``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDeleteEvaluationConfigRequest struct via the builder pattern


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


## ModelHubPromptTemplatesDerivedVariablesExtractCreate

> DerivedVariableDetailResponse ModelHubPromptTemplatesDerivedVariablesExtractCreate(ctx, promptId).DerivedVariableExtractRequest(derivedVariableExtractRequest).Execute()

Manually trigger extraction of derived variables from outputs.



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
	promptId := "promptId_example" // string | 
	derivedVariableExtractRequest := *openapiclient.NewDerivedVariableExtractRequest("Version_example") // DerivedVariableExtractRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesExtractCreate(context.Background(), promptId).DerivedVariableExtractRequest(derivedVariableExtractRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesExtractCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesDerivedVariablesExtractCreate`: DerivedVariableDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesExtractCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDerivedVariablesExtractCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **derivedVariableExtractRequest** | [**DerivedVariableExtractRequest**](DerivedVariableExtractRequest.md) |  | 

### Return type

[**DerivedVariableDetailResponse**](DerivedVariableDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesDerivedVariablesList

> PromptDerivedVariablesResponse ModelHubPromptTemplatesDerivedVariablesList(ctx, promptId).Execute()

Get all derived variables for a prompt template.



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
	promptId := "promptId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesList(context.Background(), promptId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesDerivedVariablesList`: PromptDerivedVariablesResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDerivedVariablesListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptDerivedVariablesResponse**](PromptDerivedVariablesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesDerivedVariablesPreviewCreate

> DerivedVariableDetailResponse ModelHubPromptTemplatesDerivedVariablesPreviewCreate(ctx).DerivedVariablePreviewRequest(derivedVariablePreviewRequest).Execute()

Preview derived variables from JSON content without saving.



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
	derivedVariablePreviewRequest := *openapiclient.NewDerivedVariablePreviewRequest(map[string]interface{}{"key": interface{}(123)}) // DerivedVariablePreviewRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesPreviewCreate(context.Background()).DerivedVariablePreviewRequest(derivedVariablePreviewRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesPreviewCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesDerivedVariablesPreviewCreate`: DerivedVariableDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesPreviewCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDerivedVariablesPreviewCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **derivedVariablePreviewRequest** | [**DerivedVariablePreviewRequest**](DerivedVariablePreviewRequest.md) |  | 

### Return type

[**DerivedVariableDetailResponse**](DerivedVariableDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesDerivedVariablesSchemaList

> DerivedVariableDetailResponse ModelHubPromptTemplatesDerivedVariablesSchemaList(ctx, promptId, columnName).Execute()

Get the schema for derived variables of a specific column.



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
	promptId := "promptId_example" // string | 
	columnName := "columnName_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesSchemaList(context.Background(), promptId, columnName).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesSchemaList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesDerivedVariablesSchemaList`: DerivedVariableDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesDerivedVariablesSchemaList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptId** | **string** |  | 
**columnName** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesDerivedVariablesSchemaListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**DerivedVariableDetailResponse**](DerivedVariableDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGeneratePrompt

> PromptTemplate ModelHubPromptTemplatesGeneratePrompt(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGeneratePrompt(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGeneratePrompt``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGeneratePrompt`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGeneratePrompt`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGeneratePromptRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGenerateVariables

> PromptTemplate ModelHubPromptTemplatesGenerateVariables(ctx).PromptTemplate(promptTemplate).Execute()

Generate synthetic data for prompt variables using the SyntheticDataAgent.



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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGenerateVariables(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGenerateVariables``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGenerateVariables`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGenerateVariables`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGenerateVariablesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetAllVariables

> PromptTemplate ModelHubPromptTemplatesGetAllVariables(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetAllVariables(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetAllVariables``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetAllVariables`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetAllVariables`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetAllVariablesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetEvaluationConfigs

> PromptTemplate ModelHubPromptTemplatesGetEvaluationConfigs(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetEvaluationConfigs(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetEvaluationConfigs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetEvaluationConfigs`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetEvaluationConfigs`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetEvaluationConfigsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetNextVersion

> PromptTemplate ModelHubPromptTemplatesGetNextVersion(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetNextVersion(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetNextVersion``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetNextVersion`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetNextVersion`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetNextVersionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetRunStatus

> PromptTemplate ModelHubPromptTemplatesGetRunStatus(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetRunStatus(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetRunStatus``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetRunStatus`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetRunStatus`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetRunStatusRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetSdkCode

> PromptTemplate ModelHubPromptTemplatesGetSdkCode(ctx, id, language).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	language := "language_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetSdkCode(context.Background(), id, language).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetSdkCode``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetSdkCode`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetSdkCode`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 
**language** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetSdkCodeRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesGetTemplateByName

> ModelHubPromptTemplatesList200Response ModelHubPromptTemplatesGetTemplateByName(ctx).Name(name).Version(version).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()





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
	name := "name_example" // string |  (optional)
	version := "version_example" // string |  (optional)
	createdAt := "createdAt_example" // string |  (optional)
	search := "search_example" // string | A search term. (optional)
	ordering := "ordering_example" // string | Which field to use when ordering the results. (optional)
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesGetTemplateByName(context.Background()).Name(name).Version(version).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesGetTemplateByName``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesGetTemplateByName`: ModelHubPromptTemplatesList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesGetTemplateByName`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesGetTemplateByNameRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **string** |  | 
 **version** | **string** |  | 
 **createdAt** | **string** |  | 
 **search** | **string** | A search term. | 
 **ordering** | **string** | Which field to use when ordering the results. | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptTemplatesList200Response**](ModelHubPromptTemplatesList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesImprovePrompt

> PromptTemplate ModelHubPromptTemplatesImprovePrompt(ctx).PromptTemplate(promptTemplate).Execute()





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
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesImprovePrompt(context.Background()).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesImprovePrompt``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesImprovePrompt`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesImprovePrompt`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesImprovePromptRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesList

> ModelHubPromptTemplatesList200Response ModelHubPromptTemplatesList(ctx).Name(name).Version(version).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()





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
	name := "name_example" // string |  (optional)
	version := "version_example" // string |  (optional)
	createdAt := "createdAt_example" // string |  (optional)
	search := "search_example" // string | A search term. (optional)
	ordering := "ordering_example" // string | Which field to use when ordering the results. (optional)
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesList(context.Background()).Name(name).Version(version).CreatedAt(createdAt).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesList`: ModelHubPromptTemplatesList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **string** |  | 
 **version** | **string** |  | 
 **createdAt** | **string** |  | 
 **search** | **string** | A search term. | 
 **ordering** | **string** | Which field to use when ordering the results. | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ModelHubPromptTemplatesList200Response**](ModelHubPromptTemplatesList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesPartialUpdate

> PromptTemplate ModelHubPromptTemplatesPartialUpdate(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesPartialUpdate(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesPartialUpdate`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesRead

> PromptTemplate ModelHubPromptTemplatesRead(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesRead`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesRetrieveEvaluations

> PromptTemplate ModelHubPromptTemplatesRetrieveEvaluations(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesRetrieveEvaluations(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesRetrieveEvaluations``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesRetrieveEvaluations`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesRetrieveEvaluations`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesRetrieveEvaluationsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesRunEvalsOnMultipleVersions

> PromptTemplate ModelHubPromptTemplatesRunEvalsOnMultipleVersions(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesRunEvalsOnMultipleVersions(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesRunEvalsOnMultipleVersions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesRunEvalsOnMultipleVersions`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesRunEvalsOnMultipleVersions`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesRunEvalsOnMultipleVersionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesRunTemplate

> PromptTemplate ModelHubPromptTemplatesRunTemplate(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesRunTemplate(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesRunTemplate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesRunTemplate`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesRunTemplate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesRunTemplateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesSaveName

> PromptTemplate ModelHubPromptTemplatesSaveName(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesSaveName(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesSaveName``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesSaveName`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesSaveName`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesSaveNameRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesSavePromptFolder

> PromptTemplate ModelHubPromptTemplatesSavePromptFolder(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesSavePromptFolder(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesSavePromptFolder``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesSavePromptFolder`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesSavePromptFolder`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesSavePromptFolderRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesSetDefault

> PromptTemplate ModelHubPromptTemplatesSetDefault(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesSetDefault(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesSetDefault``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesSetDefault`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesSetDefault`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesSetDefaultRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesStopStreaming

> PromptTemplate ModelHubPromptTemplatesStopStreaming(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesStopStreaming(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesStopStreaming``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesStopStreaming`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesStopStreaming`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesStopStreamingRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesUpdate

> PromptTemplate ModelHubPromptTemplatesUpdate(ctx, id).PromptTemplate(promptTemplate).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesUpdate(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesUpdate`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesUpdateEvaluationConfigs

> PromptTemplate ModelHubPromptTemplatesUpdateEvaluationConfigs(ctx, id).PromptTemplate(promptTemplate).Execute()

Add or update evaluation configurations for a PromptTemplate.



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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.
	promptTemplate := *openapiclient.NewPromptTemplate("Name_example") // PromptTemplate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesUpdateEvaluationConfigs(context.Background(), id).PromptTemplate(promptTemplate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesUpdateEvaluationConfigs``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesUpdateEvaluationConfigs`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesUpdateEvaluationConfigs`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesUpdateEvaluationConfigsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **promptTemplate** | [**PromptTemplate**](PromptTemplate.md) |  | 

### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubPromptTemplatesVersions

> PromptTemplate ModelHubPromptTemplatesVersions(ctx, id).Execute()





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
	id := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | A UUID string identifying this prompt template.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubPromptTemplatesVersions(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubPromptTemplatesVersions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubPromptTemplatesVersions`: PromptTemplate
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubPromptTemplatesVersions`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** | A UUID string identifying this prompt template. | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubPromptTemplatesVersionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptTemplate**](PromptTemplate.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresBulkCreate

> BulkCreateScoresResponse ModelHubScoresBulkCreate(ctx).BulkCreateScores(bulkCreateScores).Execute()





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
	bulkCreateScores := *openapiclient.NewBulkCreateScores("SourceType_example", "SourceId_example", []openapiclient.BulkCreateScoreItem{*openapiclient.NewBulkCreateScoreItem("LabelId_example", map[string]interface{}{"key": interface{}(123)})}) // BulkCreateScores | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresBulkCreate(context.Background()).BulkCreateScores(bulkCreateScores).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresBulkCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresBulkCreate`: BulkCreateScoresResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresBulkCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresBulkCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bulkCreateScores** | [**BulkCreateScores**](BulkCreateScores.md) |  | 

### Return type

[**BulkCreateScoresResponse**](BulkCreateScoresResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresCreate

> ScoreResponse ModelHubScoresCreate(ctx).CreateScore(createScore).Execute()





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
	createScore := *openapiclient.NewCreateScore("SourceType_example", "SourceId_example", "LabelId_example", map[string]interface{}{"key": interface{}(123)}) // CreateScore | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresCreate(context.Background()).CreateScore(createScore).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresCreate`: ScoreResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createScore** | [**CreateScore**](CreateScore.md) |  | 

### Return type

[**ScoreResponse**](ScoreResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresDelete

> ScoreDeleteResponse ModelHubScoresDelete(ctx, id).Execute()

Soft-delete a score.



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
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresDelete(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresDelete`: ScoreDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ScoreDeleteResponse**](ScoreDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresForSource

> ScoreForSourceResponse ModelHubScoresForSource(ctx).SourceType(sourceType).SourceId(sourceId).Page(page).Limit(limit).Execute()





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
	sourceType := "sourceType_example" // string | 
	sourceId := "sourceId_example" // string | 
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresForSource(context.Background()).SourceType(sourceType).SourceId(sourceId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresForSource``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresForSource`: ScoreForSourceResponse
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresForSource`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresForSourceRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sourceType** | **string** |  | 
 **sourceId** | **string** |  | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ScoreForSourceResponse**](ScoreForSourceResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresList

> ModelHubScoresList200Response ModelHubScoresList(ctx).Page(page).Limit(limit).SourceType(sourceType).SourceId(sourceId).LabelId(labelId).AnnotatorId(annotatorId).Execute()

Universal Score CRUD.



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
	sourceType := "sourceType_example" // string |  (optional)
	sourceId := "sourceId_example" // string |  (optional)
	labelId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	annotatorId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresList(context.Background()).Page(page).Limit(limit).SourceType(sourceType).SourceId(sourceId).LabelId(labelId).AnnotatorId(annotatorId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresList`: ModelHubScoresList200Response
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 
 **sourceType** | **string** |  | 
 **sourceId** | **string** |  | 
 **labelId** | **string** |  | 
 **annotatorId** | **string** |  | 

### Return type

[**ModelHubScoresList200Response**](ModelHubScoresList200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresPartialUpdate

> Score ModelHubScoresPartialUpdate(ctx, id).Score(score).Execute()

Universal Score CRUD.



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
	score := *openapiclient.NewScore("SourceType_example", map[string]interface{}{"key": interface{}(123)}) // Score | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresPartialUpdate(context.Background(), id).Score(score).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresPartialUpdate`: Score
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **score** | [**Score**](Score.md) |  | 

### Return type

[**Score**](Score.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresRead

> Score ModelHubScoresRead(ctx, id).Execute()

Universal Score CRUD.



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
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresRead(context.Background(), id).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresRead`: Score
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**Score**](Score.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ModelHubScoresUpdate

> Score ModelHubScoresUpdate(ctx, id).Score(score).Execute()

Universal Score CRUD.



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
	score := *openapiclient.NewScore("SourceType_example", map[string]interface{}{"key": interface{}(123)}) // Score | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ModelHubAPI.ModelHubScoresUpdate(context.Background(), id).Score(score).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ModelHubAPI.ModelHubScoresUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ModelHubScoresUpdate`: Score
	fmt.Fprintf(os.Stdout, "Response from `ModelHubAPI.ModelHubScoresUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiModelHubScoresUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **score** | [**Score**](Score.md) |  | 

### Return type

[**Score**](Score.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

