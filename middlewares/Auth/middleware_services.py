from focus_power.application.roles.services import UserRolesAppServices


class MiddlewareServices:

    def check_user_is_success_manager(self, user_id) -> bool:
        """This method check is logging-in user is success manager or not"""
        user_roles_app_service = UserRolesAppServices()
        user_role = user_roles_app_service.get_user_role_by_user_id(user_id=user_id)
        if user_role and user_role.is_success_manager:
            return True
        return False
