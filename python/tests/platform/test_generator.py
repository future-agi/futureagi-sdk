"""Generator tests retain their public node IDs while sharing bounded case modules."""

from ._generator_surface_cases import (
    test_committed_outputs_are_up_to_date,
    test_scaffolds_are_owned_by_hand,
    test_resources_can_be_swapped_and_extended,
    test_generated_methods_cannot_shadow_the_hand_written_client,
    test_typescript_mirrors_the_python_client,
    test_surfaces_ship_independently,
    test_mcp_names_keep_existing_tools_or_follow_the_id,
    test_catalog_mistakes_fail_the_build,
    test_pagination_needs_first_page_and_items,
    test_body_params_on_a_paginated_op_fail_the_build,
    test_sdk_only_parity_ops_do_not_reach_mcp,
    test_request_fixes_replace_what_the_contract_gets_wrong,
)

from ._generator_contract_cases import (
    test_patch_bodies_are_partial_unless_the_catalog_says_otherwise,
    test_json_value_inputs_accept_any_json_in_both_languages,
    test_a_field_added_to_a_selected_request_schema_reaches_the_generated_signature,
    test_an_operation_the_catalog_does_not_select_stays_out_of_the_sdk,
    test_a_contract_fix_the_contract_no_longer_needs_fails_the_build,
    test_models_list_their_required_fields_for_strict_mode,
    test_request_fix_mistakes_fail_the_build,
    test_multipart_needs_a_method_that_sends_a_body,
    test_docs_reference_covers_every_sdk_operation_once,
)
