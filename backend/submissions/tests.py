from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from applications.models import ApplicationProject, StatusChangeHistory
from documents.models import Document, DocumentComment, DocumentVersion
from materials.models import MaterialItem
from submissions.models import SubmissionSnapshot
from submissions.services import (
    SubmissionBlocked, evaluate_blockers, rollback_submission, submit_application,
)
from universities.models import ApplicationDeadline, Program, University
from users.models import CustomUser, StudentProfile


class SubmissionFlowTestBase(APITestCase):
    def setUp(self):
        self.student = CustomUser.objects.create_user('stu', password='x', role='student')
        self.consultant = CustomUser.objects.create_user('con', password='x', role='consultant')
        self.admin = CustomUser.objects.create_superuser('adm', password='x', role='admin')
        StudentProfile.objects.create(user=self.student, consultant=self.consultant)

        self.university = University.objects.create(name='MIT', country='美国', city='Boston')
        self.program = Program.objects.create(
            university=self.university, name='CS', degree_level='master'
        )
        self.open_round = ApplicationDeadline.objects.create(
            program=self.program, round_name='round_2',
            deadline_date=date.today().replace(year=date.today().year + 1),
        )
        self.closed_round = ApplicationDeadline.objects.create(
            program=self.program, round_name='round_1',
            deadline_date=date(2000, 1, 1),
        )

        self.application = ApplicationProject.objects.create(
            student=self.student,
            university=self.university,
            program=self.program,
            application_round=self.open_round,
            status=ApplicationProject.STATUS_PREPARING,
        )
        # 一份必交材料
        self.required_material = MaterialItem.objects.create(
            application=self.application, name='成绩单',
            material_type='transcript', is_required=True,
        )

    def _complete_required(self):
        self.required_material.is_completed = True
        self.required_material.uploaded_at = timezone.now()
        self.required_material.uploaded_by = self.consultant
        self.required_material.save()

    def _create_ps(self, with_version=True, with_unresolved_comment=False):
        ps = Document.objects.create(
            application=self.application, document_type=Document.TYPE_PS,
            title='PS', created_by=self.student,
        )
        version = None
        if with_version:
            version = DocumentVersion.objects.create(
                document=ps, content='hello world', created_by=self.student
            )
            ps.current_version = version
            ps.save()
        if with_unresolved_comment:
            DocumentComment.objects.create(
                document=ps, version=version,
                author=self.consultant, content='这里需要改',
            )
        return ps, version


class EvaluateBlockersTests(SubmissionFlowTestBase):
    def test_all_three_categories_block(self):
        # 无材料完成 + 无 PS + 批次开放（前置不完整材料、PS 缺失）
        blockers = evaluate_blockers(self.application)
        codes = {b['code'] for b in blockers}
        self.assertIn('required_material_incomplete', codes)
        self.assertIn('ps_missing', codes)
        self.assertNotIn('application_round_closed', codes)

    def test_required_material_blocker_payload(self):
        blockers = evaluate_blockers(self.application)
        blocker = next(
            b for b in blockers if b['code'] == 'required_material_incomplete'
        )
        self.assertEqual(blocker['materials'][0]['name'], '成绩单')

    def test_round_missing(self):
        self.application.application_round = None
        self.application.save()
        codes = {b['code'] for b in evaluate_blockers(self.application)}
        self.assertIn('application_round_missing', codes)

    def test_round_closed(self):
        self.application.application_round = self.closed_round
        self.application.save()
        codes = {b['code'] for b in evaluate_blockers(self.application)}
        self.assertIn('application_round_closed', codes)

    def test_ps_version_missing(self):
        self._create_ps(with_version=False)
        codes = {b['code'] for b in evaluate_blockers(self.application)}
        self.assertIn('ps_version_missing', codes)

    def test_unresolved_comment_blocks(self):
        self._complete_required()
        self._create_ps(with_unresolved_comment=True)
        codes = {b['code'] for b in evaluate_blockers(self.application)}
        self.assertIn('ps_unresolved_comment', codes)

    def test_resolved_comment_passes(self):
        _, version = self._create_ps()
        comment = DocumentComment.objects.create(
            document=version.document, version=version,
            author=self.consultant, content='ok',
        )
        comment.is_resolved = True
        comment.save()
        self._complete_required()
        self.assertEqual(evaluate_blockers(self.application), [])

    def test_unresolved_comment_on_old_version_does_not_block(self):
        _, v1 = self._create_ps()
        # v1 上留一条未解决批注，随后 v2 成为当前版本
        DocumentComment.objects.create(
            document=v1.document, version=v1,
            author=self.consultant, content='旧版本意见',
        )
        v2 = DocumentVersion.objects.create(
            document=v1.document, content='revised', created_by=self.student
        )
        v1.document.current_version = v2
        v1.document.save()
        self._complete_required()
        self.assertEqual(evaluate_blockers(self.application), [])

    def test_unresolved_document_level_comment_blocks(self):
        _, version = self._create_ps()
        DocumentComment.objects.create(
            document=version.document, version=None,
            author=self.consultant, content='文档级意见',
        )
        self._complete_required()
        codes = {b['code'] for b in evaluate_blockers(self.application)}
        self.assertIn('ps_unresolved_comment', codes)

    def test_today_deadline_is_still_open(self):
        # 截止日期 == 今天，不应判定为已截止
        self.open_round.deadline_date = timezone.localdate()
        self.open_round.save()
        self._complete_required()
        self._create_ps()
        self.assertEqual(evaluate_blockers(self.application), [])


class SubmitServiceTests(SubmissionFlowTestBase):
    def _ready(self):
        self._complete_required()
        self._create_ps()

    def test_submit_raises_when_blocked(self):
        with self.assertRaises(SubmissionBlocked) as ctx:
            submit_application(self.application, self.consultant)
        self.assertTrue(ctx.exception.blockers)

    def test_successful_submit_solidifies_everything(self):
        self._ready()
        snapshot, created = submit_application(self.application, self.consultant)
        self.assertTrue(created)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'submitted')
        self.assertTrue(self.application.is_submission_locked)
        self.assertIsNotNone(self.application.submitted_at)

        # 材料锁定
        self.required_material.refresh_from_db()
        self.assertTrue(self.required_material.is_locked)

        # 快照明细
        self.assertEqual(snapshot.materials.count(), 1)
        snap_material = snapshot.materials.first()
        self.assertEqual(snap_material.name, '成绩单')
        self.assertTrue(snap_material.is_completed)
        self.assertEqual(snapshot.ps_title, 'PS')
        self.assertEqual(snapshot.ps_version_number, 1)
        self.assertEqual(snapshot.ps_content, 'hello world')
        self.assertEqual(snapshot.application_round_name, self.open_round.get_round_name_display())
        self.assertEqual(snapshot.submitted_by, self.consultant)
        self.assertTrue(snapshot.is_active)

        # 状态历史
        history = StatusChangeHistory.objects.filter(application=self.application).first()
        self.assertEqual(history.to_status, 'submitted')

    def test_new_material_and_version_after_submit_do_not_change_snapshot(self):
        self._ready()
        snapshot, _ = submit_application(self.application, self.consultant)

        # 新增材料
        new_material = MaterialItem.objects.create(
            application=self.application, name='新增补充材料',
            material_type='other', is_required=False,
        )
        # PS 新版本（与 API 行为一致：新版本成为当前版本）
        ps = Document.objects.get(document_type=Document.TYPE_PS)
        v2 = DocumentVersion.objects.create(
            document=ps, content='changed body', created_by=self.student
        )
        ps.current_version = v2
        ps.save()
        self.assertEqual(ps.current_version.version_number, 2)

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.materials.count(), 1)
        self.assertEqual(snapshot.ps_version_number, 1)
        self.assertEqual(snapshot.ps_content, 'hello world')
        # 新增材料不被锁定
        self.assertFalse(new_material.is_locked)

    def test_duplicate_submit_returns_same_snapshot(self):
        self._ready()
        first, created1 = submit_application(self.application, self.consultant)
        second, created2 = submit_application(self.application, self.admin)
        self.assertEqual(first.pk, second.pk)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(SubmissionSnapshot.objects.filter(application=self.application).count(), 1)

    def test_concurrent_submit_creates_only_one_snapshot(self):
        from django.db import connection
        if connection.vendor == 'sqlite':
            self.skipTest('SQLite 使用数据库级写锁，无法模拟行级并发（PostgreSQL 上验证）')

        self._ready()

        def attempt():
            # 每个线程使用独立连接
            from django.db import connections
            try:
                connections.close_all()
                submit_application(self.application, self.consultant)
            except IntegrityError:
                pass
            finally:
                connections.close_all()

        import threading
        threads = [threading.Thread(target=attempt) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(
            SubmissionSnapshot.objects.filter(
                application=self.application, rolled_back_at__isnull=True
            ).count(),
            1,
        )
        self.assertEqual(
            SubmissionSnapshot.objects.filter(application=self.application).count(),
            1,
        )

    def test_only_one_active_snapshot_enforced_by_db_constraint(self):
        """数据库层部分唯一约束：同一申请不允许两个未回退快照（并发兜底）。"""
        self._ready()
        first, _ = submit_application(self.application, self.consultant)

        duplicate = SubmissionSnapshot(
            application=self.application,
            from_status='preparing',
            to_status='submitted',
            submitted_by=self.admin,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                duplicate.save()

        # 回退后允许再次生成生效快照
        rollback_submission(self.application, self.admin, '原因')
        duplicate.save()
        self.assertEqual(
            SubmissionSnapshot.objects.filter(
                application=self.application, rolled_back_at__isnull=True
            ).count(),
            1,
        )

    def test_rollback_clears_lock_and_keeps_snapshot(self):
        self._ready()
        snapshot, _ = submit_application(self.application, self.consultant)

        with self.assertRaises(ValueError):
            rollback_submission(self.application, self.admin, '  ')

        rolled = rollback_submission(self.application, self.admin, '材料传错，需要重传')
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationProject.STATUS_PREPARING)
        self.assertFalse(self.application.is_submission_locked)
        self.assertIsNone(self.application.submitted_at)
        self.required_material.refresh_from_db()
        self.assertFalse(self.required_material.is_locked)

        rolled.refresh_from_db()
        self.assertFalse(rolled.is_active)
        self.assertEqual(rolled.rollback_reason, '材料传错，需要重传')
        self.assertEqual(rolled.rolled_back_by, self.admin)
        # 旧快照材料仍在
        self.assertEqual(rolled.materials.count(), 1)

        # 回退状态历史：submitted -> preparing
        rollback_hist = StatusChangeHistory.objects.filter(
            application=self.application, change_reason__contains='回退'
        ).first()
        self.assertIsNotNone(rollback_hist)
        self.assertEqual(rollback_hist.from_status, 'submitted')
        self.assertEqual(rollback_hist.to_status, ApplicationProject.STATUS_PREPARING)

    def test_rollback_without_active_snapshot_fails(self):
        with self.assertRaises(ValueError):
            rollback_submission(self.application, self.admin, 'test')

    def test_resubmit_after_rollback_creates_new_snapshot_old_kept(self):
        self._ready()
        first, _ = submit_application(self.application, self.consultant)
        rollback_submission(self.application, self.admin, '回退重来')

        # 回退后原先阻塞仍满足，可重新递交
        second, created = submit_application(self.application, self.consultant)
        self.assertTrue(created)
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(SubmissionSnapshot.objects.filter(application=self.application).count(), 2)
        self.assertEqual(
            SubmissionSnapshot.objects.filter(
                application=self.application, rolled_back_at__isnull=True
            ).count(),
            1,
        )
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)


class SubmitAPITests(SubmissionFlowTestBase):
    url = '/api/applications/projects/'

    def _detail_url(self, action):
        return f'{self.url}{self.application.id}/{action}'

    def test_student_cannot_submit(self):
        self.client.force_authenticate(self.student)
        resp = self.client.post(self._detail_url('submission/submit/'))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_submit_blocked_lists_blockers(self):
        self.client.force_authenticate(self.consultant)
        resp = self.client.post(self._detail_url('submission/submit/'))
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(resp.data['blocked'])
        codes = {b['code'] for b in resp.data['blockers']}
        self.assertIn('required_material_incomplete', codes)
        self.assertIn('ps_missing', codes)

    def test_submit_success_then_duplicate_is_idempotent(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)

        resp = self.client.post(self._detail_url('submission/submit/'))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data['created'])
        snapshot_id = resp.data['snapshot']['id']

        again = self.client.post(self._detail_url('submission/submit/'))
        self.assertEqual(again.status_code, status.HTTP_200_OK)
        self.assertFalse(again.data['created'])
        self.assertEqual(again.data['snapshot']['id'], snapshot_id)

    def test_blockers_endpoint_reports_and_clears(self):
        self.client.force_authenticate(self.consultant)
        resp = self.client.get(self._detail_url('submission/blockers/'))
        self.assertTrue(resp.data['blocked'])
        self.assertEqual(len(resp.data['blockers']), 2)

        self._complete_required()
        self._create_ps()
        resp2 = self.client.get(self._detail_url('submission/blockers/'))
        self.assertFalse(resp2.data['blocked'])
        self.assertEqual(resp2.data['blockers'], [])

    def test_locked_material_cannot_be_removed_or_replaced(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))

        mat_url = f'/api/materials/items/{self.required_material.id}/'
        delete_resp = self.client.delete(mat_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_409_CONFLICT)

        put_resp = self.client.patch(mat_url, {'name': '改名'})
        self.assertEqual(put_resp.status_code, status.HTTP_409_CONFLICT)

        self.required_material.refresh_from_db()
        self.assertEqual(self.required_material.name, '成绩单')

    def test_new_material_after_lock_can_be_deleted(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))

        new_mat = MaterialItem.objects.create(
            application=self.application, name='后加的', material_type='other'
        )
        resp = self.client.delete(f'/api/materials/items/{new_mat.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_locked_round_cannot_be_changed(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))

        another = ApplicationDeadline.objects.create(
            program=self.program, round_name='round_3',
            deadline_date=date.today().replace(year=date.today().year + 2),
        )
        resp = self.client.patch(
            f'{self.url}{self.application.id}/',
            {'application_round': another.id},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.application.refresh_from_db()
        self.assertEqual(self.application.application_round_id, self.open_round.id)

    def test_change_status_cannot_directly_set_submitted(self):
        self.client.force_authenticate(self.consultant)
        resp = self.client.post(
            self._detail_url('change_status/'), {'status': 'submitted'}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_locked_application_cannot_go_back_via_change_status(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))

        resp = self.client.post(
            self._detail_url('change_status/'), {'status': 'preparing'}
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

        # 向后流转允许
        resp_ok = self.client.post(
            self._detail_url('change_status/'), {'status': 'waiting'}
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)

    def test_locked_application_patch_round_rejected_forward_status_allowed(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))
        base = f'{self.url}{self.application.id}/'

        backward = self.client.patch(base, {'status': 'preparing'})
        self.assertEqual(backward.status_code, status.HTTP_400_BAD_REQUEST)

        direct_submit = self.client.patch(base, {'status': 'submitted'})
        self.assertEqual(direct_submit.status_code, status.HTTP_400_BAD_REQUEST)

        forward = self.client.patch(base, {'status': 'waiting'})
        self.assertEqual(forward.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'waiting')

    def test_locked_application_cannot_be_deleted(self):
        self._complete_required()
        self._create_ps()
        self.client.force_authenticate(self.consultant)
        self.client.post(self._detail_url('submission/submit/'))
        resp = self.client.delete(f'{self.url}{self.application.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ApplicationProject.objects.filter(pk=self.application.pk).exists())


class RollbackAPITests(SubmissionFlowTestBase):
    def setUp(self):
        super().setUp()
        self._complete_required()
        self._create_ps()
        submit_application(self.application, self.consultant)

    def test_consultant_cannot_rollback(self):
        self.client.force_authenticate(self.consultant)
        resp = self.client.post(
            f'/api/applications/projects/{self.application.id}/submission/rollback/',
            {'reason': 'x'},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_rollback_requires_reason(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/applications/projects/{self.application.id}/submission/rollback/',
            {'reason': '   '},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_rollback_success_and_snapshot_queryable(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/applications/projects/{self.application.id}/submission/rollback/',
            {'reason': '顾问误递交'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['application']['is_submission_locked'])

        # 旧快照仍可查（application 维度 + 全局维度）
        old = self.client.get(
            f'/api/applications/projects/{self.application.id}/submission/snapshots/'
        )
        self.assertEqual(len(old.data), 1)
        self.assertFalse(old.data[0]['is_active'])
        self.assertEqual(old.data[0]['rollback_reason'], '顾问误递交')
        self.assertEqual(len(old.data[0]['materials']), 1)

        listing = self.client.get(
            f'/api/submissions/snapshots/?application={self.application.id}'
        )
        self.assertEqual(len(listing.data.get('results', listing.data)), 1)

        # 回退后可再次递交
        resp2 = self.client.post(
            f'/api/applications/projects/{self.application.id}/submission/submit/'
        )
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

        # 现在能查到新老两份
        old2 = self.client.get(
            f'/api/applications/projects/{self.application.id}/submission/snapshots/'
        )
        self.assertEqual(len(old2.data), 2)

    def test_student_cannot_see_other_students_snapshots(self):
        other_student = CustomUser.objects.create_user('stu2', password='x', role='student')
        self.client.force_authenticate(other_student)
        resp = self.client.get(
            f'/api/submissions/snapshots/?application={self.application.id}'
        )
        results = resp.data.get('results', resp.data)
        self.assertEqual(len(results), 0)

    def test_detail_serializer_exposes_lock_fields(self):
        self.client.force_authenticate(self.consultant)
        resp = self.client.get(f'/api/applications/projects/{self.application.id}/')
        self.assertTrue(resp.data['is_submission_locked'])
        self.assertIsNotNone(resp.data['active_snapshot'])
        self.assertEqual(resp.data['submission_blockers'], [])
        self.assertEqual(resp.data['application_round_name'], '第二轮')
