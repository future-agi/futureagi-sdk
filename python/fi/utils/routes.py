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