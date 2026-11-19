from enum import Enum


class UsersResultQueryProvenance(str, Enum):
    MATCHING_ACTIVITY_WALK = "matching_activity_walk"
    PHYSICAL_LATEST_USERS = "physical_latest_users"
    SPAN_USER_ROLLUP_END_USERS_CANDIDATE = "span_user_rollup_end_users_candidate"

    def __str__(self) -> str:
        return str(self.value)
