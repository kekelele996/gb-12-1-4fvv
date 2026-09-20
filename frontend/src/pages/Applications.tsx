import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Modal,
  Form,
  Select,
  Input,
  Progress,
  Tag,
  Space,
  Typography,
  message,
  Descriptions,
  Alert,
  List,
  Divider,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  DeleteOutlined,
  SendOutlined,
  LockOutlined,
  UndoOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { applicationAPI, universityAPI } from '../api';
import {
  ApplicationProject,
  University,
  Program,
  ApplicationDeadline,
  SubmissionSnapshot,
  SubmissionCheckResult,
} from '../types';
import { useAuthStore } from '../store/useAuthStore';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const statusColorMap: { [key: string]: string } = {
  planning: 'blue',
  preparing: 'gold',
  submitted: 'cyan',
  waiting: 'purple',
  admitted: 'green',
  rejected: 'red',
  waitlisted: 'orange',
  deferred: 'cyan',
};

const Applications: React.FC = () => {
  const { user } = useAuthStore();
  const canSubmitRole = user?.role === 'consultant' || user?.role === 'admin';
  const isAdmin = user?.role === 'admin';

  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState<ApplicationProject[]>([]);
  const [universities, setUniversities] = useState<University[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [deadlines, setDeadlines] = useState<ApplicationDeadline[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<ApplicationProject | null>(null);
  const [detailDeadlines, setDetailDeadlines] = useState<ApplicationDeadline[]>([]);
  const [roundValue, setRoundValue] = useState<number | undefined>(undefined);
  const [roundSaving, setRoundSaving] = useState(false);
  const [snapshots, setSnapshots] = useState<SubmissionSnapshot[]>([]);
  const [submitModalVisible, setSubmitModalVisible] = useState(false);
  const [submitTarget, setSubmitTarget] = useState<ApplicationProject | null>(null);
  const [submitCheck, setSubmitCheck] = useState<SubmissionCheckResult | null>(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [rollbackModalVisible, setRollbackModalVisible] = useState(false);
  const [rollbackReason, setRollbackReason] = useState('');
  const [rollbackLoading, setRollbackLoading] = useState(false);
  const [rollbackResult, setRollbackResult] = useState<string | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchApplications();
    fetchUniversities();
  }, []);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const response = await applicationAPI.getApplications();
      setApplications(response.data.results || response.data);
    } catch (error) {
      console.error('获取申请列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUniversities = async () => {
    try {
      const response = await universityAPI.getUniversities();
      setUniversities(response.data.results || response.data);
    } catch (error) {
      console.error('获取院校列表失败:', error);
    }
  };

  const fetchSnapshots = async (applicationId: number) => {
    try {
      const response = await applicationAPI.getSnapshots(applicationId);
      setSnapshots(response.data.results || response.data);
    } catch (error) {
      console.error('获取快照历史失败:', error);
    }
  };

  const handleUniversityChange = async (universityId: number) => {
    try {
      const response = await universityAPI.getPrograms({ university: universityId });
      setPrograms(response.data.results || response.data);
      form.setFieldValue('program', undefined);
      form.setFieldValue('application_round', undefined);
      setDeadlines([]);
    } catch (error) {
      console.error('获取专业列表失败:', error);
    }
  };

  const handleProgramChange = async (programId: number) => {
    form.setFieldValue('application_round', undefined);
    try {
      const response = await universityAPI.getProgram(programId);
      setDeadlines(response.data.deadlines || []);
    } catch (error) {
      setDeadlines([]);
    }
  };

  const handleCreate = () => {
    form.resetFields();
    setDeadlines([]);
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      await applicationAPI.createApplication(values);
      message.success('申请项目创建成功');
      setModalVisible(false);
      fetchApplications();
    } catch (error: any) {
      const errors = error.response?.data;
      if (errors) {
        Object.keys(errors).forEach((key) => {
          message.error(`${key}: ${errors[key][0]}`);
        });
      } else {
        message.error('创建失败');
      }
    }
  };

  const handleViewDetail = async (application: ApplicationProject) => {
    try {
      const response = await applicationAPI.getApplication(application.id);
      setSelectedApplication(response.data);
      setRoundValue(response.data.application_round ?? undefined);
      setRollbackResult(null);
      setDetailVisible(true);
      fetchSnapshots(application.id);
      try {
        const programRes = await universityAPI.getProgram(response.data.program);
        setDetailDeadlines(programRes.data.deadlines || []);
      } catch (error) {
        setDetailDeadlines([]);
      }
    } catch (error) {
      message.error('获取详情失败');
    }
  };

  const handleSaveRound = async () => {
    if (!selectedApplication) return;
    setRoundSaving(true);
    try {
      const response = await applicationAPI.patchApplication(selectedApplication.id, {
        application_round: roundValue ?? null,
      });
      setSelectedApplication(response.data);
      message.success('申请批次已更新');
      fetchApplications();
    } catch (error: any) {
      const data = error.response?.data;
      message.error(data?.application_round?.[0] || data?.error || '申请批次更新失败');
    } finally {
      setRoundSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个申请项目吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await applicationAPI.deleteApplication(id);
          message.success('删除成功');
          fetchApplications();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleStatusChange = async (application: ApplicationProject, newStatus: string) => {
    try {
      await applicationAPI.changeStatus(application.id, { status: newStatus });
      message.success('状态更新成功');
      fetchApplications();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const openSubmitModal = async (application: ApplicationProject) => {
    setSubmitTarget(application);
    setSubmitCheck(null);
    setSubmitModalVisible(true);
    setSubmitLoading(true);
    try {
      const response = await applicationAPI.getSubmissionCheck(application.id);
      setSubmitCheck(response.data);
    } catch (error) {
      message.error('获取递交预检失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleSubmitConfirm = async () => {
    if (!submitTarget) return;
    setSubmitLoading(true);
    try {
      const response = await applicationAPI.submitApplication(submitTarget.id);
      message.success(response.data?.detail || '递交成功，申请已锁定');
      setSubmitModalVisible(false);
      fetchApplications();
    } catch (error: any) {
      const data = error.response?.data;
      if (data?.blocking_items) {
        setSubmitCheck({
          can_submit: false,
          already_submitted: false,
          blocking_items: data.blocking_items,
          snapshot: null,
        });
      } else {
        message.error(data?.error || '递交失败');
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!selectedApplication) return;
    if (!rollbackReason.trim()) {
      message.warning('请填写回退原因');
      return;
    }
    setRollbackLoading(true);
    try {
      const response = await applicationAPI.rollbackSubmission(selectedApplication.id, {
        reason: rollbackReason.trim(),
      });
      setRollbackResult(response.data?.detail || '已回退递交');
      setRollbackModalVisible(false);
      setRollbackReason('');
      const detail = await applicationAPI.getApplication(selectedApplication.id);
      setSelectedApplication(detail.data);
      setRoundValue(detail.data.application_round ?? undefined);
      fetchSnapshots(selectedApplication.id);
      fetchApplications();
    } catch (error: any) {
      message.error(error.response?.data?.error || '回退失败');
    } finally {
      setRollbackLoading(false);
    }
  };

  const columns = [
    {
      title: '院校',
      dataIndex: 'university_name',
      key: 'university_name',
    },
    {
      title: '专业',
      dataIndex: 'program_name',
      key: 'program_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 220,
      render: (status: string, record: ApplicationProject) => (
        <Space>
          <Select
            value={status}
            style={{ width: 120 }}
            onChange={(value) => handleStatusChange(record, value)}
          >
            <Option value="planning">规划中</Option>
            <Option value="preparing">准备材料</Option>
            <Option value="submitted">已提交</Option>
            <Option value="waiting">等待结果</Option>
            <Option value="admitted">已录取</Option>
            <Option value="rejected">已拒</Option>
            <Option value="waitlisted">候补</Option>
            <Option value="deferred">延期</Option>
          </Select>
          {record.submission_locked && (
            <Tag icon={<LockOutlined />} color="cyan">
              已锁定
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '材料进度',
      dataIndex: 'materials_progress',
      key: 'materials_progress',
      width: 200,
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 260,
      render: (_: any, record: ApplicationProject) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {canSubmitRole && !record.submission_locked && (
            <Button
              type="link"
              icon={<SendOutlined />}
              onClick={() => openSubmitModal(record)}
            >
              递交
            </Button>
          )}
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const activeSnapshot = selectedApplication?.current_snapshot ?? null;

  return (
    <div>
      <Title level={2} className="page-header">
        申请项目管理
      </Title>

      <Card>
        <div style={{ marginBottom: 16, textAlign: 'right' }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建申请项目
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={applications}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            pageSizeOptions: ['10', '20', '50'],
            defaultPageSize: 10,
          }}
        />
      </Card>

      <Modal
        title="新建申请项目"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="university"
            label="目标院校"
            rules={[{ required: true, message: '请选择目标院校' }]}
          >
            <Select placeholder="请选择院校" onChange={handleUniversityChange}>
              {universities.map((u) => (
                <Option key={u.id} value={u.id}>
                  {u.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="program"
            label="申请专业"
            rules={[{ required: true, message: '请选择申请专业' }]}
          >
            <Select placeholder="请选择专业" onChange={handleProgramChange}>
              {programs.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="application_round" label="申请批次">
            <Select placeholder="请选择申请批次" allowClear>
              {deadlines.map((d) => (
                <Option key={d.id} value={d.id}>
                  {d.round_name_display}（截止 {d.deadline_date}）
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <TextArea rows={4} placeholder="添加备注信息..." />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="递交申请"
        open={submitModalVisible}
        onCancel={() => setSubmitModalVisible(false)}
        width={560}
        footer={[
          <Button key="cancel" onClick={() => setSubmitModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            icon={<SendOutlined />}
            loading={submitLoading}
            disabled={!submitCheck?.can_submit}
            onClick={handleSubmitConfirm}
          >
            确认递交
          </Button>,
        ]}
      >
        {submitLoading && !submitCheck ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        ) : submitCheck?.already_submitted ? (
          <Alert
            type="info"
            showIcon
            message="该申请已递交"
            description={`快照 #${submitCheck.snapshot?.snapshot_no} 已生效，重复递交不会生成新快照。`}
          />
        ) : submitCheck?.can_submit ? (
          <Alert
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
            message="预检通过，可以递交"
            description="必交材料已完成，个人陈述当前版本无未解决批注，申请批次未截止。确认后状态将一次转为「已提交」，并固化材料与个人陈述版本快照；此后锁定材料与申请批次不能移除或更换。"
          />
        ) : (
          submitCheck && (
            <div>
              <Alert
                type="error"
                showIcon
                message="存在阻塞项，无法递交"
                style={{ marginBottom: 12 }}
              />
              <List
                size="small"
                bordered
                dataSource={submitCheck.blocking_items}
                renderItem={(item) => (
                  <List.Item>
                    <Space>
                      <WarningOutlined style={{ color: '#faad14' }} />
                      {item.message}
                    </Space>
                  </List.Item>
                )}
              />
            </div>
          )
        )}
      </Modal>

      <Modal
        title="回退递交"
        open={rollbackModalVisible}
        onCancel={() => setRollbackModalVisible(false)}
        onOk={handleRollback}
        okText="确认回退"
        cancelText="取消"
        okButtonProps={{ danger: true, loading: rollbackLoading }}
      >
        <Alert
          type="warning"
          showIcon
          message="回退将解除递交锁定"
          description="状态将恢复为递交前状态，材料与申请批次解除锁定；当前快照保留为「已回退」历史记录，仍可查看。"
          style={{ marginBottom: 12 }}
        />
        <TextArea
          rows={3}
          placeholder="请填写回退原因（必填）"
          value={rollbackReason}
          onChange={(e) => setRollbackReason(e.target.value)}
        />
      </Modal>

      <Modal
        title="申请项目详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={760}
        footer={null}
      >
        {selectedApplication && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="院校" span={2}>
                {selectedApplication.university_name}
              </Descriptions.Item>
              <Descriptions.Item label="专业" span={2}>
                {selectedApplication.program_name}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusColorMap[selectedApplication.status]}>
                  {selectedApplication.status_display}
                </Tag>
                {selectedApplication.submission_locked && (
                  <Tag icon={<LockOutlined />} color="cyan">
                    已锁定
                  </Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="材料进度">
                <Progress percent={selectedApplication.materials_progress} size="small" />
              </Descriptions.Item>
              <Descriptions.Item label="申请批次" span={2}>
                <Space>
                  <Select
                    style={{ width: 260 }}
                    placeholder="请选择申请批次"
                    value={roundValue}
                    allowClear
                    disabled={selectedApplication.submission_locked}
                    onChange={(value) => setRoundValue(value)}
                  >
                    {detailDeadlines.map((d) => (
                      <Option key={d.id} value={d.id}>
                        {d.round_name_display}（截止 {d.deadline_date}）
                      </Option>
                    ))}
                  </Select>
                  {selectedApplication.submission_locked ? (
                    <Text type="secondary">已锁定，不能移除或更换</Text>
                  ) : (
                    <Button
                      size="small"
                      type="primary"
                      loading={roundSaving}
                      disabled={
                        (roundValue ?? null) === selectedApplication.application_round
                      }
                      onClick={handleSaveRound}
                    >
                      保存批次
                    </Button>
                  )}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="申请费">
                {selectedApplication.application_fee
                  ? `${selectedApplication.application_fee} ${
                      selectedApplication.fee_paid ? '(已缴纳)' : '(未缴纳)'
                    }`
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="提交时间">
                {selectedApplication.submitted_at
                  ? new Date(selectedApplication.submitted_at).toLocaleString()
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedApplication.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>
                {selectedApplication.notes || '无'}
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left">递交锁定</Divider>

            {rollbackResult && (
              <Alert
                type="warning"
                showIcon
                icon={<UndoOutlined />}
                message="回退结果"
                description={rollbackResult}
                closable
                onClose={() => setRollbackResult(null)}
                style={{ marginBottom: 12 }}
              />
            )}

            {selectedApplication.submission_locked && activeSnapshot ? (
              <div>
                <Alert
                  type="success"
                  showIcon
                  icon={<LockOutlined />}
                  message={`已递交锁定（快照 #${activeSnapshot.snapshot_no}）`}
                  description={`递交人：${activeSnapshot.submitted_by_name || '-'} · 递交时间：${new Date(
                    activeSnapshot.submitted_at
                  ).toLocaleString()}`}
                  style={{ marginBottom: 12 }}
                />
                <Descriptions bordered column={2} size="small">
                  <Descriptions.Item label="批次快照">
                    {activeSnapshot.application_round_name || '-'}
                    {activeSnapshot.application_round_deadline
                      ? `（截止 ${activeSnapshot.application_round_deadline}）`
                      : ''}
                  </Descriptions.Item>
                  <Descriptions.Item label="个人陈述快照">
                    {activeSnapshot.ps_document_title || '个人陈述'} v
                    {activeSnapshot.ps_version_number}（
                    {activeSnapshot.ps_word_count} 字）
                  </Descriptions.Item>
                </Descriptions>
                <Table
                  style={{ marginTop: 12 }}
                  size="small"
                  rowKey="id"
                  pagination={false}
                  dataSource={activeSnapshot.materials_snapshot}
                  columns={[
                    { title: '材料名称', dataIndex: 'name', key: 'name' },
                    {
                      title: '类型',
                      dataIndex: 'material_type_display',
                      key: 'material_type_display',
                    },
                    {
                      title: '必交',
                      dataIndex: 'is_required',
                      key: 'is_required',
                      width: 70,
                      render: (v: boolean) => (v ? '是' : '否'),
                    },
                    {
                      title: '状态',
                      dataIndex: 'is_completed',
                      key: 'is_completed',
                      width: 90,
                      render: (v: boolean) =>
                        v ? <Tag color="green">已完成</Tag> : <Tag>未完成</Tag>,
                    },
                  ]}
                />
                {isAdmin && (
                  <div style={{ marginTop: 12, textAlign: 'right' }}>
                    <Button
                      danger
                      icon={<UndoOutlined />}
                      onClick={() => setRollbackModalVisible(true)}
                    >
                      回退递交
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <Alert
                type="info"
                showIcon
                message="未递交"
                description="顾问递交后，申请状态将转为「已提交」，材料清单与个人陈述版本将固化快照并锁定。"
                action={
                  canSubmitRole ? (
                    <Button
                      size="small"
                      type="primary"
                      icon={<SendOutlined />}
                      onClick={() => openSubmitModal(selectedApplication)}
                    >
                      递交
                    </Button>
                  ) : undefined
                }
              />
            )}

            {snapshots.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Divider orientation="left">快照历史</Divider>
                <List
                  size="small"
                  bordered
                  dataSource={snapshots}
                  renderItem={(s) => (
                    <List.Item>
                      <Space direction="vertical" size={2} style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={s.status === 'active' ? 'green' : 'default'}>
                            {s.status_display}
                          </Tag>
                          <Text strong>快照 #{s.snapshot_no}</Text>
                          <Text type="secondary">
                            {s.submitted_by_name || '-'} 递交于{' '}
                            {new Date(s.submitted_at).toLocaleString()}
                          </Text>
                          <Text type="secondary">
                            PS v{s.ps_version_number} · 材料 {s.materials_snapshot.length} 项
                          </Text>
                        </Space>
                        {s.status === 'rolled_back' && (
                          <Text type="warning">
                            已于 {s.rolled_back_at
                              ? new Date(s.rolled_back_at).toLocaleString()
                              : '-'}{' '}
                            被 {s.rolled_back_by_name || '-'} 回退：{s.rollback_reason}
                          </Text>
                        )}
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Applications;
