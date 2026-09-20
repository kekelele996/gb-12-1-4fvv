from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import CustomUser, StudentProfile
from universities.models import University, Program, ApplicationDeadline
from documents.models import Document, DocumentVersion, DocumentComment
from materials.models import MaterialItem
from .models import ApplicationProject, SubmissionSnapshot, StatusChangeHistory


class SubmissionLockTestCase(TestCase):
    """申请递交锁定：阻塞校验、快照固化、锁定约束、回退、幂等。"""

    def setUp(self):
        self.student = CustomUser.objects.create_user(
            username='student1', password='pass1234', role='student'
        )
        self.consultant = CustomUser.objects.create_user(
            username='consultant1', password='pass1234', role='consultant'
        )
        self.admin = CustomUser.objects.create_user(
            username='admin1', password='pass1234', role='admin'
        )
        StudentProfile.objects.create(user=self.student, consultant=self.consultant)

        self.university = University.objects.create(
            name='测试大学', country='美国', city='波士顿'
        )
        self.program = Program.objects.create(
            university=self.university, name='计算机科学', degree_level='master'
        )
        self.deadline = ApplicationDeadline.objects.create(
            program=self.program,
            round_name='round_1',
            deadline_date=timezone.localdate() + timedelta(days=30),
        )
        self.application = ApplicationProject.objects.create(
            student=self.student,
            university=self.university,
            program=self.program,
            application_round=self.deadline,
            status=ApplicationProject.STATUS_PREPARING,
        )
        self.material = MaterialItem.objects.create(
            application=self.application,
            name='本科成绩单',
            material_type='transcript',
            is_required=True,
            is_completed=True,
        )
        self.ps_document = Document.objects.create(
            application=self.application,
            document_type='ps',
            title='个人陈述',
            created_by=self.student,
        )
        self.ps_version = DocumentVersion.objects.create(
            document=self.ps_document,
            content='这是个人陈述第一版。',
            created_by=self.student,
        )
        self.ps_document.current_version = self.ps_version
        self.ps_document.save()

        self.client = APIClient()

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def submit(self, user):
        self.authenticate(user)
        return self.client.post(f'/api/applications/projects/{self.application.id}/submit/')

    def rollback(self, user, reason='回退原因说明'):
        self.authenticate(user)
        return self.client.post(
            f'/api/applications/projects/{self.application.id}/rollback_submission/',
            {'reason': reason},
        )

    # ---------- 阻塞项校验 ----------

    def test_submit_blocked_by_incomplete_required_material(self):
        self.material.is_completed = False
        self.material.save()

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 400)
        blockers = response.data['blocking_items']
        self.assertTrue(any('本科成绩单' in b['message'] for b in blockers))
        self.assertEqual(SubmissionSnapshot.objects.count(), 0)
        self.application.refresh_from_db()
        self.assertNotEqual(self.application.status, ApplicationProject.STATUS_SUBMITTED)

    def test_submit_blocked_by_unresolved_comment_on_current_version(self):
        DocumentComment.objects.create(
            document=self.ps_document,
            version=self.ps_version,
            author=self.consultant,
            content='这里需要修改',
            is_resolved=False,
        )

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 400)
        blockers = response.data['blocking_items']
        self.assertTrue(any('未解决批注' in b['message'] for b in blockers))

    def test_resolved_comment_does_not_block(self):
        DocumentComment.objects.create(
            document=self.ps_document,
            version=self.ps_version,
            author=self.consultant,
            content='已处理的意见',
            is_resolved=True,
        )

        response = self.submit(self.consultant)
        self.assertEqual(response.status_code, 201)

    def test_submit_blocked_without_ps_version(self):
        self.ps_document.current_version = None
        self.ps_document.save()
        self.ps_version.delete()

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            any(b['type'] == 'ps' for b in response.data['blocking_items'])
        )

    def test_submit_blocked_by_past_deadline(self):
        self.deadline.deadline_date = timezone.localdate() - timedelta(days=1)
        self.deadline.save()

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            any('截止' in b['message'] for b in response.data['blocking_items'])
        )

    def test_submit_blocked_without_application_round(self):
        self.application.application_round = None
        self.application.save()

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            any(b['type'] == 'round' for b in response.data['blocking_items'])
        )

    def test_submission_check_lists_blockers(self):
        self.material.is_completed = False
        self.material.save()
        self.authenticate(self.consultant)

        response = self.client.get(
            f'/api/applications/projects/{self.application.id}/submission_check/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['can_submit'])
        self.assertEqual(len(response.data['blocking_items']), 1)

    # ---------- 成功递交与快照固化 ----------

    def test_submit_success_locks_and_snapshots(self):
        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 201)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationProject.STATUS_SUBMITTED)
        self.assertTrue(self.application.submission_locked)
        self.assertIsNotNone(self.application.submitted_at)
        self.assertIsNotNone(self.application.current_snapshot)

        snapshot = self.application.current_snapshot
        self.assertEqual(snapshot.snapshot_no, 1)
        self.assertEqual(snapshot.status, SubmissionSnapshot.STATUS_ACTIVE)
        self.assertEqual(snapshot.submitted_by, self.consultant)
        self.assertEqual(snapshot.previous_status, ApplicationProject.STATUS_PREPARING)
        # 批次信息固化
        self.assertEqual(snapshot.application_round, self.deadline)
        self.assertEqual(snapshot.application_round_deadline, self.deadline.deadline_date)
        # PS 版本固化
        self.assertEqual(snapshot.ps_version, self.ps_version)
        self.assertEqual(snapshot.ps_version_number, self.ps_version.version_number)
        self.assertEqual(snapshot.ps_content, '这是个人陈述第一版。')
        # 材料固化
        self.assertEqual(len(snapshot.materials_snapshot), 1)
        self.assertEqual(snapshot.materials_snapshot[0]['name'], '本科成绩单')
        # 材料被锁定
        self.material.refresh_from_db()
        self.assertTrue(self.material.is_locked)
        # 状态历史
        self.assertTrue(
            StatusChangeHistory.objects.filter(
                application=self.application,
                to_status=ApplicationProject.STATUS_SUBMITTED,
            ).exists()
        )

    def test_snapshot_not_changed_by_new_material_or_version(self):
        self.submit(self.consultant)
        snapshot = SubmissionSnapshot.objects.get()

        # 递交后新增材料与新版本
        MaterialItem.objects.create(
            application=self.application, name='新增材料', is_required=False
        )
        new_version = DocumentVersion.objects.create(
            document=self.ps_document, content='第二版内容', created_by=self.student
        )
        self.ps_document.current_version = new_version
        self.ps_document.save()
        self.material.name = '改名后的成绩单'
        self.material.save()

        snapshot.refresh_from_db()
        self.assertEqual(len(snapshot.materials_snapshot), 1)
        self.assertEqual(snapshot.materials_snapshot[0]['name'], '本科成绩单')
        self.assertEqual(snapshot.ps_version_number, self.ps_version.version_number)
        self.assertEqual(snapshot.ps_content, '这是个人陈述第一版。')

    # ---------- 锁定约束 ----------

    def test_locked_material_cannot_be_modified_or_removed(self):
        self.submit(self.consultant)
        self.authenticate(self.consultant)

        response = self.client.patch(
            f'/api/materials/items/{self.material.id}/', {'name': '新名字'}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.delete(f'/api/materials/items/{self.material.id}/')
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            f'/api/materials/items/{self.material.id}/mark_incomplete/'
        )
        self.assertEqual(response.status_code, 400)

        self.material.refresh_from_db()
        self.assertEqual(self.material.name, '本科成绩单')
        self.assertTrue(self.material.is_completed)

    def test_locked_application_round_cannot_be_changed_or_removed(self):
        self.submit(self.consultant)
        other_round = ApplicationDeadline.objects.create(
            program=self.program,
            round_name='round_2',
            deadline_date=timezone.localdate() + timedelta(days=60),
        )
        self.authenticate(self.consultant)

        response = self.client.patch(
            f'/api/applications/projects/{self.application.id}/',
            {'application_round': other_round.id},
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f'/api/applications/projects/{self.application.id}/',
            {'application_round': None},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

        self.application.refresh_from_db()
        self.assertEqual(self.application.application_round, self.deadline)

    # ---------- 幂等与并发 ----------

    def test_duplicate_submit_creates_only_one_snapshot(self):
        first = self.submit(self.consultant)
        second = self.submit(self.consultant)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(SubmissionSnapshot.objects.count(), 1)
        self.assertEqual(
            first.data['snapshot']['id'], second.data['snapshot']['id']
        )

    def test_student_cannot_submit(self):
        response = self.submit(self.student)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SubmissionSnapshot.objects.count(), 0)

    # ---------- 回退 ----------

    def test_rollback_requires_admin_and_reason(self):
        self.submit(self.consultant)

        response = self.rollback(self.consultant)
        self.assertEqual(response.status_code, 403)

        response = self.rollback(self.admin, reason='')
        self.assertEqual(response.status_code, 400)

    def test_rollback_restores_and_keeps_old_snapshot(self):
        self.submit(self.consultant)
        snapshot = SubmissionSnapshot.objects.get()

        response = self.rollback(self.admin, reason='学生要求更换批次')

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationProject.STATUS_PREPARING)
        self.assertFalse(self.application.submission_locked)
        self.assertIsNone(self.application.current_snapshot)
        self.assertIsNone(self.application.submitted_at)

        self.material.refresh_from_db()
        self.assertFalse(self.material.is_locked)

        # 旧快照保留可查
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.status, SubmissionSnapshot.STATUS_ROLLED_BACK)
        self.assertEqual(snapshot.rolled_back_by, self.admin)
        self.assertEqual(snapshot.rollback_reason, '学生要求更换批次')
        self.assertIsNotNone(snapshot.rolled_back_at)

        self.authenticate(self.consultant)
        response = self.client.get(
            f'/api/applications/projects/{self.application.id}/snapshots/'
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], SubmissionSnapshot.STATUS_ROLLED_BACK)

    def test_resubmit_after_rollback_creates_new_snapshot(self):
        self.submit(self.consultant)
        self.rollback(self.admin)

        response = self.submit(self.consultant)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(SubmissionSnapshot.objects.count(), 2)
        active = SubmissionSnapshot.objects.get(status=SubmissionSnapshot.STATUS_ACTIVE)
        self.assertEqual(active.snapshot_no, 2)
        self.application.refresh_from_db()
        self.assertEqual(self.application.current_snapshot, active)
