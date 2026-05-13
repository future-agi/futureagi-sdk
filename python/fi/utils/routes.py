from enum import Enum


class Routes(str, Enum):
    healthcheck = "healthcheck"

    # logging
    log_model = "sdk/api/v1/log/model/"

    # evaluation
    evaluate = "sdk/api/v1/eval/"
    evaluatev2 = "sdk/api/v1/new-eval/"
    evaluate_template = "sdk/api/v1/eval/{eval_id}/"
    get_eval_templates = "sdk/api/v1/get-evals/"
    get_eval_result = "sdk/api/v1/new-eval/"
    evaluate_pipeline = "sdk/api/v1/evaluate-pipeline/"

    # eval template management (revamp, Phases 1–7)
    eval_template_list = "model-hub/eval-templates/list/"
    eval_template_create_v2 = "model-hub/eval-templates/create-v2/"
    eval_template_detail = "model-hub/eval-templates/{template_id}/detail/"
    eval_template_update_v2 = "model-hub/eval-templates/{template_id}/update/"
    eval_template_delete = "model-hub/delete-eval-template/"
    eval_template_bulk_delete = "model-hub/eval-templates/bulk-delete/"
    eval_template_version_list = "model-hub/eval-templates/{template_id}/versions/"
    eval_template_version_create = (
        "model-hub/eval-templates/{template_id}/versions/create/"
    )
    eval_template_version_set_default = (
        "model-hub/eval-templates/{template_id}/versions/{version_id}/set-default/"
    )
    eval_template_version_restore = (
        "model-hub/eval-templates/{template_id}/versions/{version_id}/restore/"
    )
    composite_eval_create = "model-hub/eval-templates/create-composite/"
    composite_eval_detail = "model-hub/eval-templates/{template_id}/composite/"
    composite_eval_execute = (
        "model-hub/eval-templates/{template_id}/composite/execute/"
    )

    # dataset
    dataset = "model-hub/develops"
    dataset_names = "model-hub/develops/get-datasets-names/"
    dataset_empty = "model-hub/develops/create-empty-dataset/"
    dataset_local = "model-hub/develops/create-dataset-from-local-file/"
    dataset_huggingface = "model-hub/develops/create-dataset-from-huggingface/"
    dataset_table = "model-hub/develops/{dataset_id}/get-dataset-table/"
    dataset_delete = "model-hub/develops/delete_dataset/"
    dataset_add_rows = "model-hub/develops/{dataset_id}/add_rows/"
    dataset_add_columns = "model-hub/develops/{dataset_id}/add_columns/"
    dataset_eval_stats = "model-hub/dataset/{dataset_id}/eval-stats/"

    # prompt
    generate_prompt = "model-hub/prompt-templates/generate-prompt/"
    improve_prompt = "model-hub/prompt-templates/improve-prompt/"
    run_template = "model-hub/prompt-templates/{template_id}/run_template/"
    create_template = "model-hub/prompt-templates/create-draft/"
    delete_template = "model-hub/prompt-templates/{template_id}/"
    get_template_by_id = "model-hub/prompt-templates/{template_id}/"
    get_template_id_by_name = "model-hub/prompt-templates/"
    list_templates = "model-hub/prompt-templates/"
    get_template_by_name = "model-hub/prompt-templates/get-template-by-name/"
    add_new_draft = "model-hub/prompt-templates/{template_id}/add-new-draft/"
    get_template_version_history = "model-hub/prompt-history-executions/"
    get_model_details = "model-hub/api/models_list/"
    get_run_status = "model-hub/prompt-templates/{template_id}/get-run-status/"
    commit_template = "model-hub/prompt-templates/{template_id}/commit/"

    # prompt labels
    prompt_labels = "model-hub/prompt-labels/"
    prompt_label_get_by_name = "model-hub/prompt-labels/get-by-name/"
    prompt_label_remove = "model-hub/prompt-labels/remove/"

    prompt_label_assign_by_id = "model-hub/prompt-labels/{template_id}/{label_id}/assign-label-by-id/"
    prompt_label_set_default = "model-hub/prompt-labels/set-default/"
    prompt_label_template_labels = "model-hub/prompt-labels/template-labels/"

    # model provider
    model_hub_api_keys = "model-hub/api-keys/"
    model_hub_default_provider = "model-hub/default-provider/"

    dataset_add_run_prompt_column = "model-hub/develops/add_run_prompt_column/"
    dataset_add_evaluation = "model-hub/develops/{dataset_id}/add_user_eval/"
    dataset_optimization_create = "model-hub/optimisation/create/"

    knowledge_base = "model-hub/knowledge-base/"
    knowledge_base_list = "model-hub/knowledge-base/list/"
    knowledge_base_files = "model-hub/knowledge-base/files/"

    # configure evaluations
    configure_evaluations = "sdk/api/v1/configure-evaluations/"

    # annotations
    bulk_annotation = "tracer/bulk-annotation/"
    get_annotation_labels = "tracer/get-annotation-labels/"
    list_projects = "tracer/project/list_projects/"

    # annotation labels (CRUD)
    annotations_labels = "model-hub/annotations-labels/"
    annotations_labels_detail = "model-hub/annotations-labels/{label_id}/"

    # annotation queues
    annotation_queues = "model-hub/annotation-queues/"
    annotation_queue_detail = "model-hub/annotation-queues/{queue_id}/"
    annotation_queue_status = "model-hub/annotation-queues/{queue_id}/update-status/"
    annotation_queue_progress = "model-hub/annotation-queues/{queue_id}/progress/"
    annotation_queue_analytics = "model-hub/annotation-queues/{queue_id}/analytics/"
    annotation_queue_agreement = "model-hub/annotation-queues/{queue_id}/agreement/"
    annotation_queue_export = "model-hub/annotation-queues/{queue_id}/export/"
    annotation_queue_export_to_dataset = "model-hub/annotation-queues/{queue_id}/export-to-dataset/"
    annotation_queue_add_label = "model-hub/annotation-queues/{queue_id}/add-label/"
    annotation_queue_remove_label = "model-hub/annotation-queues/{queue_id}/remove-label/"

    # queue items
    queue_items = "model-hub/annotation-queues/{queue_id}/items/"
    queue_items_add = "model-hub/annotation-queues/{queue_id}/items/add-items/"
    queue_items_bulk_remove = "model-hub/annotation-queues/{queue_id}/items/bulk-remove/"
    queue_items_assign = "model-hub/annotation-queues/{queue_id}/items/assign/"
    queue_item_annotations_submit = "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/submit/"
    queue_item_annotations_import = "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/import/"
    queue_item_annotations_list = "model-hub/annotation-queues/{queue_id}/items/{item_id}/annotations/"
    queue_item_complete = "model-hub/annotation-queues/{queue_id}/items/{item_id}/complete/"
    queue_item_skip = "model-hub/annotation-queues/{queue_id}/items/{item_id}/skip/"

    # scores (unified annotations)
    scores = "model-hub/scores/"
    scores_bulk = "model-hub/scores/bulk/"
    scores_for_source = "model-hub/scores/for-source/"
