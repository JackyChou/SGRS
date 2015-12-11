#coding:utf-8

from django.test import TestCase

from GeneralReport.models import SGRSUser, SGRSRole, SGRSUserAssignment
from GeneralReport.models import ReportType, ReportPermission
from GeneralReport.models import ReportPermissionCombination
from GeneralReport.forms import UserCreationForm

class ReportTypeAndReportPermissionModelTest(TestCase):

    def test_saving_and_retrieving_reportpermission(self):
        report_type = ReportType(name='first_report_type')
        report_type.save()

        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            report_type = report_type,
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()
        second_perm = ReportPermission(
            name = 'second-perm',
            description = 'second perm',
            report_type = report_type,
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        second_perm.save()

        saved_report_type = ReportType.objects.first()
        self.assertEqual(saved_report_type, report_type)

        saved_report_perms = ReportPermission.objects.all().order_by('id')
        self.assertEqual(saved_report_perms.count(), 2)

        first_saved_report_perm = saved_report_perms[0]
        second_saved_report_perm = saved_report_perms[1]
        self.assertEqual(first_saved_report_perm, first_perm)
        self.assertEqual(first_saved_report_perm.report_type, report_type)
        self.assertEqual(second_saved_report_perm, second_perm)
        self.assertEqual(second_saved_report_perm.report_type, report_type)

class ReportPermissionCombinationModelTest(TestCase):

    def test_saving_and_retrieving_perm_combination(self):
        report_type = ReportType(name='first_report_type')
        report_type.save()

        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            report_type = report_type,
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()
        second_perm = ReportPermission(
            name = 'second-perm',
            description = 'second perm',
            report_type = report_type,
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        second_perm.save()

        perm_comb = ReportPermissionCombination(
            name = 'first_perm_comb',
            description = 'first perm comb',
        )
        perm_comb.save()
        perm_comb.report_permissions = [first_perm, second_perm]
        perm_comb.save()

        saved_perm_comb = ReportPermissionCombination.objects.get(
            name='first_perm_comb')
        self.assertEqual(saved_perm_comb, perm_comb)
        self.assertEqual(
            len(saved_perm_comb.report_permissions.all()),
            len(perm_comb.report_permissions.all())
        )
        sort_key_function = lambda x:x.id
        self.assertEqual(
            sorted(saved_perm_comb.report_permissions.all(),
                key=sort_key_function),
            sorted(perm_comb.report_permissions.all(),
                key=sort_key_function)
        )

class SGRSUserAndSGRSRoleModelTest(TestCase):

    def test_saving_and_retrieving_user(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        second_user = UserCreationForm(
            data = dict(
                username = 'second_user',
                password1 = '654321',
                password2 = '654321',
            )
        ).save()

        saved_users = SGRSUser.objects.all().order_by('id')
        self.assertEqual(saved_users.count(), 2)

        first_saved_user = saved_users[0]
        second_saved_user = saved_users[1]

        self.assertEqual(first_saved_user, first_user)
        self.assertEqual(second_saved_user, second_user)

    def test_saving_and_retrieving_role(self):
        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        second_role = SGRSRole(
            name = 'second_role',
            description = 'second role for test',
            can_download = True,
        )
        second_role.save()

        saved_roles = SGRSRole.objects.all().order_by('id')
        self.assertEqual(saved_roles.count(), 2)

        first_saved_role = saved_roles[0]
        second_saved_role = saved_roles[1]

        self.assertEqual(first_saved_role, first_role)
        self.assertEqual(second_saved_role, second_role)

class SGRSRoleAndPermissionModelTest(TestCase):

    def test_saving_and_retrieving_role_perm_relation(self):
        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()

        perm_comb = ReportPermissionCombination(
            name = 'first_perm_comb',
            description = 'first perm comb',
        )
        perm_comb.save()
        perm_comb.report_permissions = [first_perm,]
        perm_comb.save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()
        first_role.report_permissions = [first_perm,]
        first_role.report_permission_combinations = [perm_comb,]
        first_role.save()

        saved_role = SGRSRole.objects.get(name='first_role')
        self.assertEqual(
            saved_role.report_permissions,
            first_role.report_permissions
        )
        self.assertEqual(len(saved_role.report_permissions.all()), 1)
        self.assertEqual(
            saved_role.report_permission_combinations,
            first_role.report_permission_combinations
        )
        self.assertEqual(
            len(saved_role.report_permission_combinations.all()), 1)

class SGRSUserAssignmentModelTest(TestCase):

    def test_saving_and_retrieving_user_assignment(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        second_user = UserCreationForm(
            data = dict(
                username = 'second_user',
                password1 = '654321',
                password2 = '654321',
            )
        ).save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        second_role = SGRSRole(
            name = 'second_role',
            description = 'second role for test',
            can_download = True,
        )
        second_role.save()

        first_user_assignment = SGRSUserAssignment(user = first_user)
        first_user_assignment.save()
        first_user_assignment.roles = [first_role, second_role]
        first_user_assignment.save()

        second_user_assignment = SGRSUserAssignment(user = second_user)
        second_user_assignment.save()
        second_user_assignment.roles = [first_role, ]
        second_user_assignment.save()

        saved_first_user_assignment = SGRSUserAssignment.objects.get(
            user = first_user)
        self.assertEqual(len(saved_first_user_assignment.roles.all()), 2)
        self.assertEqual(
            saved_first_user_assignment.roles, first_user_assignment.roles)

        saved_second_user_assignment = SGRSUserAssignment.objects.get(
            user = second_user)
        self.assertEqual(len(saved_second_user_assignment.roles.all()), 1)
        self.assertEqual(
            saved_second_user_assignment.roles, second_user_assignment.roles)

class SGRSUserModelFunctionTest(TestCase):

    def test_function_get_all_roles(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        second_user = UserCreationForm(
            data = dict(
                username = 'second_user',
                password1 = '654321',
                password2 = '654321',
            )
        ).save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        second_role = SGRSRole(
            name = 'second_role',
            description = 'second role for test',
            can_download = True,
        )
        second_role.save()

        first_user_assignment = SGRSUserAssignment(user = first_user)
        first_user_assignment.save()
        first_user_assignment.roles = [second_role, first_role]
        first_user_assignment.save()

        second_user_assignment = SGRSUserAssignment(user = second_user)
        second_user_assignment.save()
        second_user_assignment.roles = [first_role, ]
        second_user_assignment.save()

        sort_key_function = lambda x:x.id
        self.assertEqual(
            sorted(first_user_assignment.roles.all(),key = sort_key_function),
            sorted(first_user.get_all_roles(),key = sort_key_function)
        )
        self.assertEqual(
            sorted(second_user_assignment.roles.all(),key = sort_key_function),
            sorted(second_user.get_all_roles(),key = sort_key_function)
        )

    def test_function_get_all_report_permissions(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()
        first_role.report_permissions = [first_perm,]
        first_role.save()

        second_role = SGRSRole(
            name = 'second_role',
            description = 'second role for test',
            can_download = True,
        )
        second_role.save()

        second_perm = ReportPermission(
            name = 'second-perm',
            description = 'second perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        second_perm.save()
        second_role.report_permissions = [second_perm,]
        second_role.save()

        first_user_assignment = SGRSUserAssignment(user = first_user)
        first_user_assignment.save()
        first_user_assignment.roles = [first_role, second_role]
        first_user_assignment.save()

        sort_key_function = lambda x:x.id
        self.assertEqual(
            sorted(ReportPermission.objects.filter(
                    sgrsrole__in=[first_role, second_role]),
                key=sort_key_function),
            sorted(first_user.get_all_report_permissions(),
                key=sort_key_function)
        )

    def test_function_get_all_report_combination_permissions(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()

        second_perm = ReportPermission(
            name = 'second-perm',
            description = 'second perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        second_perm.save()

        perm_comb = ReportPermissionCombination(
            name = 'first_perm_comb',
            description = 'first perm comb',
        )
        perm_comb.save()
        perm_comb.report_permissions = [first_perm, second_perm]
        perm_comb.save()

        first_role.report_permission_combinations = [perm_comb,]
        first_role.save()

        first_user_assignment = SGRSUserAssignment(user = first_user)
        first_user_assignment.save()
        first_user_assignment.roles = [first_role, ]
        first_user_assignment.save()

        sort_key_function = lambda x:x.id
        self.assertEqual(
            sorted(ReportPermissionCombination.objects.filter(
                    sgrsrole__in=[first_role, ]),
                key=sort_key_function),
            sorted(first_user.get_all_report_combination_permissions(),
                key=sort_key_function)
        )

    def test_function_has_report_perm(self):
        first_user = UserCreationForm(
            data = dict(
                username = 'first_user',
                password1 = '123456',
                password2 = '123456',
            )
        ).save()

        first_role = SGRSRole(
            name = 'first_role',
            description = 'first role for test',
            can_download = True,
        )
        first_role.save()

        first_perm = ReportPermission(
            name = 'first-perm',
            description = 'first perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        first_perm.save()

        second_perm = ReportPermission(
            name = 'second-perm',
            description = 'second perm',
            db_conf = 'default',
            SQL_conf = """
                SELECT count(*) FROM tablename
            """,
            filter_conf = '{}',
        )
        second_perm.save()

        first_role.report_permissions = [first_perm,]
        first_role.save()

        first_user_assignment = SGRSUserAssignment(user = first_user)
        first_user_assignment.save()
        first_user_assignment.roles = [first_role, ]
        first_user_assignment.save()

        self.assertEqual(first_user.has_report_perm(first_perm), True)
        self.assertEqual(first_user.has_report_perm('first-perm'), True)
        self.assertEqual(first_user.has_report_perm(second_perm), False)
        self.assertEqual(first_user.has_report_perm('second-perm'), False)
