
// API route constants for the FutureAGI SDK

export const Routes = {
    // Healthcheck
    healthcheck: "healthcheck",

    // Logging
    log_model: "sdk/api/v1/log/model/",

    // Evaluation
    evaluate: "sdk/api/v1/eval/",
    evaluatev2: "sdk/api/v1/new-eval/",
    evaluate_template: "sdk/api/v1/eval/{eval_id}/",
    get_eval_templates: "sdk/api/v1/get-evals/",
    get_eval_result: "sdk/api/v1/new-eval/",
    evaluate_pipeline: "sdk/api/v1/evaluate-pipeline/",

    // Dataset
    dataset: "model-hub/develops",
    dataset_names: "model-hub/develops/get-datasets-names/",
    dataset_empty: "model-hub/develops/create-empty-dataset/",
    dataset_local: "model-hub/develops/create-dataset-from-local-file/",
    dataset_huggingface: "model-hub/develops/create-dataset-from-huggingface/",
    dataset_table: "model-hub/develops/{dataset_id}/get-dataset-table/",
    dataset_delete: "model-hub/develops/delete_dataset/",
    dataset_add_rows: "model-hub/develops/{dataset_id}/add_rows/",
    dataset_add_columns: "model-hub/develops/{dataset_id}/add_columns/",
    dataset_eval_stats: "model-hub/dataset/{dataset_id}/eval-stats/",

    // Prompt
    generate_prompt: "model-hub/prompt-templates/generate-prompt/",
    improve_prompt: "model-hub/prompt-templates/improve-prompt/",
    run_template: "model-hub/prompt-templates/{template_id}/run_template/",
    create_template: "model-hub/prompt-templates/create-draft/",
    delete_template: "model-hub/prompt-templates/{template_id}",
    get_template_by_id: "model-hub/prompt-templates/{template_id}",
    get_template_id_by_name: "model-hub/prompt-templates/",
    list_templates: "model-hub/prompt-templates/",
    get_template_by_name: "model-hub/prompt-templates/get-template-by-name/",
    add_new_draft: "model-hub/prompt-templates/{template_id}/add-new-draft/",
    get_template_version_history: "model-hub/prompt-history-executions/",
    get_model_details: "model-hub/model-providers/get-model-details/",
    get_run_status: "model-hub/prompt-templates/{template_id}/get-run-status/",
    commit_template: "model-hub/prompt-templates/{template_id}/commit/",

    // Prompt labels
    prompt_labels: "model-hub/prompt-labels/",
    prompt_label_get_by_name: "model-hub/prompt-labels/get-by-name/",
    prompt_label_remove: "model-hub/prompt-labels/remove/",
    prompt_label_assign_by_id: "model-hub/prompt-labels/{template_id}/{label_id}/assign-label-by-id/",
    prompt_label_set_default: "model-hub/prompt-labels/set-default/",
    prompt_label_template_labels: "model-hub/prompt-labels/template-labels/",

    // Model provider
    model_hub_api_keys: "model-hub/api-keys/",
    model_hub_default_provider: "model-hub/default-provider/",

    // Dataset operations
    dataset_add_run_prompt_column: "model-hub/develops/add_run_prompt_column/",
    dataset_add_evaluation: "model-hub/develops/{dataset_id}/add_user_eval/",
    dataset_optimization_create: "model-hub/optimisation/create/",

    // Knowledge base
    knowledge_base: "model-hub/knowledge-base/",
    knowledge_base_list: "model-hub/knowledge-base/list/",
    knowledge_base_files: "model-hub/knowledge-base/files/",

    // Configure evaluations
    configure_evaluations: "sdk/api/v1/configure-evaluations/",

    // Annotations
    BULK_ANNOTATION: "tracer/bulk-annotation/",
    GET_ANNOTATION_LABELS: "tracer/get-annotation-labels/",
    LIST_PROJECTS: "tracer/project/list_projects/",

    // Annotation labels (CRUD)
    ANNOTATIONS_LABELS: "model-hub/annotations-labels/",
    ANNOTATIONS_LABELS_DETAIL: "model-hub/annotations-labels/{label_id}/",

    // Annotation queues
    ANNOTATION_QUEUES: "model-hub/annotation-queues/",
    ANNOTATION_QUEUE_DETAIL: "model-hub/annotation-queues/{queue_id}/",
    ANNOTATION_QUEUE_STATUS: "model-hub/annotation-queues/{queue_id}/update-status/",
    ANNOTATION_QUEUE_PROGRESS: "model-hub/annotation-queues/{queue_id}/progress/",
    ANNOTATION_QUEUE_ANALYTICS: "model-hub/annotation-queues/{queue_id}/analytics/",
    ANNOTATION_QUEUE_AGREEMENT: "model-hub/annotation-queues/{queue_id}/agreement/",
    ANNOTATION_QUEUE_EXPORT: "model-hub/annotation-queues/{queue_id}/export/",
    ANNOTATION_QUEUE_EXPORT_TO_DATASET: "model-hub/annotation-queues/{queue_id}/export-to-dataset/",
    ANNOTATION_QUEUE_ADD_LABEL: "model-hub/annotation-queues/{queue_id}/add-label/",
    ANNOTATION_QUEUE_REMOVE_LABEL: "model-hub/annotation-queues/{queue_id}/remove-label/",

    // Queue items
    QUEUE_ITEMS: "model-hub/annotation-queues/{queue_id}/items/",
    QUEUE_ITEMS_ADD: "model-hub/annotation-queues/{queue_id}/items/add-items/",
    QUEUE_ITEMS_BULK_REMOVE: "model-hub/annotation-queues/{queue_id}/items/bulk-remove/",
    QUEUE_ITEMS_ASSIGN: "model-hub/annotation-queues/{queue_id}/items/assign/",
    QUEUE_ITEM_ANNOTATIONS_SUBMIT: "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/submit/",
    QUEUE_ITEM_ANNOTATIONS_IMPORT: "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/import/",
    QUEUE_ITEM_ANNOTATIONS_LIST: "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/",
    QUEUE_ITEM_COMPLETE: "model-hub/annotation-queues/{queue_id}/items/{item_id}/complete/",
    QUEUE_ITEM_SKIP: "model-hub/annotation-queues/{queue_id}/items/{item_id}/skip/",

    // Scores (unified annotations)
    SCORES: "model-hub/scores/",
    SCORES_BULK: "model-hub/scores/bulk/",
    SCORES_FOR_SOURCE: "model-hub/scores/for-source/",
} as const;
