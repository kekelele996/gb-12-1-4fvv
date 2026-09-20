import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Collapse,
  Descriptions,
  Empty,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Timeline,
  Typography,
  message,
} from 'antd';
import {
  LockOutlined,
  UnlockOutlined,
  SendOutlined,
  RollbackOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import { applicationAPI } from '../api';
import {
  ApplicationProject,
  SubmissionBlocker,
  SubmissionSnapshot,
} from '../types';

const { Text, Paragraph } = Typography;

const BLOCKER_CODE_LABEL: Record<string, string> = {
  required_material_incomplete: '必交材料未完成',
  ps_missing: '缺少个人陈述',
  ps_version_missing: '个人陈述无版本',
  ps_unresolved_comment: '个人陈述有未解决批注',
  application_round_missing: '未选择申请批次',
  application_round_closed: '申请批次已截止',
};

interface RollbackResult {
  reason: string;
  snapshot: SubmissionSnapshot;
}

interface Props {
  application: ApplicationProject;
  role: 'student' | 'consultant' | 'admin';
  onApplicationChanged: () => void;
}

const SubmissionPanel: React.FC<Props> = ({ application, role, onApplicationChanged }) => {
  const [snapshots, setSnapshots] = useState<SubmissionSnapshot[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [blockers, setBlockers] = useState<SubmissionBlocker[]>(
    application.submission_blockers || []
  );
  const [rollbackTarget, setRollbackTarget] = useState<SubmissionSnapshot | null>(null);
  const [rollbackReason, setRollbackReason] = useState('');
  const [rollingBack, setRollingBack] = useState(false);
  const [rollbackResult, setRollbackResult] = useState<RollbackResult | null>(null);

  const locked = application.is_submission_locked;
  const activeSnapshot = application.active_snapshot || null;
  const canSubmit = role === 'consultant' || role === 'admin';

  const fetchSnapshots = async () => {
    try {
      const res = await applicationAPI.getSubmissionSnapshots(application.id);
      setSnapshots(res.data);
    } catch (error) {
      console.error('获取递交快照失败:', error);
    }
  };

  const refresh = async () => {
    try {
      const res = await applicationAPI.getSubmissionBlockers(application.id);
      setBlockers(res.data.blockers || []);
    } catch (error) {
      console.error('获取递交阻塞项失败:', error);
    }
    fetchSnapshots();
  };

  useEffect(() => {
    setBlockers(application.submission_blockers || []);
    setRollbackResult(null);
    fetchSnapshots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application.id, application.is_submission_locked]);

  const renderBlockerDetail = (blocker: SubmissionBlocker) => {
    if (blocker.code === 'required_material_incomplete' && blocker.materials?.length) {
      return (
        <span>
          {blocker.message}：
          {blocker.materials.map((m) => (
            <Tag key={m.id} color="red" style={{ marginTop: 4 }}>
              {m.name}
            </Tag>
          ))}
        </span>
      );
    }
    if (blocker.code === 'ps_unresolved_comment') {
      return (
        <span>
          {blocker.message}（当前版本 v{blocker.ps_version?.version_number}，
          未解决批注 {blocker.unresolved_count} 条）
        </span>
      );
    }
    if (blocker.code === 'application_round_closed' && blocker.application_round) {
      return (
        <span>
          {blocker.message}（{blocker.application_round.round_name}，
          截止 {blocker.application_round.deadline_date}）
        </span>
      );
    }
    return <span>{blocker.message}</span>;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await applicationAPI.submit(application.id);
      message.success(res.data.detail || '申请递交成功');
      setBlockers([]);
      onApplicationChanged();
      fetchSnapshots();
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        const data = error.response.data;
        setBlockers(data.blockers || []);
        message.error('递交被阻止，请先处理以下阻塞项');
      } else {
        message.error(error.response?.data?.detail || error.response?.data?.error || '递交失败');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const openRollback = () => {
    setRollbackReason('');
    setRollbackTarget(activeSnapshot);
  };

  const confirmRollback = async () => {
    if (!rollbackReason.trim()) {
      message.warning('请填写回退原因');
      return;
    }
    setRollingBack(true);
    try {
      const res = await applicationAPI.rollback(application.id, rollbackReason.trim());
      message.success('递交已回退，材料与申请批次已解锁');
      setRollbackResult({ reason: rollbackReason.trim(), snapshot: res.data.snapshot });
      setRollbackTarget(null);
      onApplicationChanged();
      fetchSnapshots();
    } catch (error: any) {
      message.error(error.response?.data?.error || '回退失败');
    } finally {
      setRollingBack(false);
    }
  };

  const materialColumns = [
    { title: '材料', dataIndex: 'name', key: 'name' },
    {
      title: '类型',
      dataIndex: 'material_type_display',
      key: 'material_type_display',
      width: 130,
    },
    {
      title: '必需',
      dataIndex: 'is_required',
      key: 'is_required',
      width: 70,
      render: (v: boolean) => (v ? <Tag color="orange">必交</Tag> : '可选'),
    },
    {
      title: '递交时状态',
      dataIndex: 'is_completed',
      key: 'is_completed',
      width: 100,
      render: (v: boolean) => (v ? <Tag color="green">已完成</Tag> : <Tag>未完成</Tag>),
    },
    {
      title: '文件',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 140,
      render: (name: string, row: SubmissionSnapshot['materials'][number]) =>
        row.file_url ? (
          <a href={row.file_url} target="_blank" rel="noreferrer">
            {name}
          </a>
        ) : (
          name || '-'
        ),
    },
  ];

  const renderSnapshotBody = (snapshot: SubmissionSnapshot) => (
    <div>
      <Descriptions size="small" column={2} bordered style={{ marginBottom: 12 }}>
        <Descriptions.Item label="个人陈述">
          {snapshot.ps_title}
          {snapshot.ps_version_number ? (
            <Tag color="blue" style={{ marginLeft: 8 }}>
              v{snapshot.ps_version_number}
            </Tag>
          ) : (
            <Tag style={{ marginLeft: 8 }}>无版本</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="字数">{snapshot.ps_word_count}</Descriptions.Item>
        <Descriptions.Item label="申请批次">
          {snapshot.application_round_name || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="批次截止日期">
          {snapshot.application_round_deadline || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="递交人">{snapshot.submitted_by_name}</Descriptions.Item>
        <Descriptions.Item label="递交时间">
          {new Date(snapshot.submitted_at).toLocaleString()}
        </Descriptions.Item>
      </Descriptions>
      <Table
        size="small"
        rowKey="id"
        columns={materialColumns}
        dataSource={snapshot.materials}
        pagination={false}
      />
      {snapshot.ps_content && (
        <Collapse
          ghost
          style={{ marginTop: 8 }}
          items={[
            {
              key: 'ps',
              label: '查看固化的个人陈述正文',
              children: (
                <Paragraph
                  style={{ whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}
                >
                  {snapshot.ps_content}
                </Paragraph>
              ),
            },
          ]}
        />
      )}
    </div>
  );

  const rolledBackSnapshots = snapshots.filter((s) => !s.is_active);

  return (
    <div>
      {/* —— 锁定状态 —— */}
      {locked ? (
        <Alert
          type="success"
          showIcon
          icon={<LockOutlined />}
          style={{ marginBottom: 12 }}
          message={
            <Space wrap>
              <Text strong>申请已递交并锁定</Text>
              <Tag color="green">已提交</Tag>
              {application.submitted_at && (
                <Text type="secondary">
                  递交时间：{new Date(application.submitted_at).toLocaleString()}
                </Text>
              )}
            </Space>
          }
          description="材料与申请批次已固化，不能移除或更换；新增材料和文书新版本不影响快照。"
        />
      ) : blockers.length === 0 ? (
        <Alert
          type="success"
          showIcon
          icon={<UnlockOutlined />}
          style={{ marginBottom: 12 }}
          message="所有递交条件已满足，可以递交"
          description={
            canSubmit
              ? '递交后状态将一次转为“已提交”，并固化材料清单与个人陈述版本快照。'
              : '递交操作由顾问或管理员执行。'
          }
        />
      ) : (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 12 }}
          message={`暂不可递交（${blockers.length} 项阻塞）`}
          description={
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {blockers.map((blocker) => (
                <li key={blocker.code} style={{ marginBottom: 6 }}>
                  <Text strong>[{BLOCKER_CODE_LABEL[blocker.code] || blocker.code}] </Text>
                  {renderBlockerDetail(blocker)}
                </li>
              ))}
            </ul>
          }
        />
      )}

      {/* —— 操作按钮 —— */}
      <Space style={{ marginBottom: 12 }}>
        {!locked && canSubmit && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            loading={submitting}
            onClick={handleSubmit}
          >
            递交申请
          </Button>
        )}
        {locked && role === 'admin' && (
          <Button danger icon={<RollbackOutlined />} onClick={openRollback}>
            管理员回退
          </Button>
        )}
        <Button icon={<HistoryOutlined />} onClick={refresh}>
          刷新
        </Button>
      </Space>

      {/* —— 回退结果 —— */}
      {rollbackResult && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message="回退结果：递交已撤销，申请已解锁"
          description={
            <Space direction="vertical" size={2}>
              <span>回退原因：{rollbackResult.reason}</span>
              <span>
                回退操作人：{rollbackResult.snapshot.rolled_back_by_name}，时间：
                {rollbackResult.snapshot.rolled_back_at &&
                  new Date(rollbackResult.snapshot.rolled_back_at).toLocaleString()}
              </span>
              <span>旧快照 #{rollbackResult.snapshot.id} 已保留，可在下方历史中查阅。</span>
            </Space>
          }
        />
      )}

      {/* —— 生效快照 —— */}
      {activeSnapshot ? (
        <div style={{ marginBottom: 16 }}>
          <Text strong>
            <LockOutlined /> 当前固化快照（#{activeSnapshot.id}）
          </Text>
          <div style={{ marginTop: 8 }}>{renderSnapshotBody(activeSnapshot)}</div>
        </div>
      ) : (
        !locked && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="尚未递交，暂无快照"
            style={{ margin: '8px 0' }}
          />
        )
      )}

      {/* —— 历史快照（含已回退） —— */}
      {rolledBackSnapshots.length > 0 && (
        <div>
          <Text strong>历史快照（{rolledBackSnapshots.length}）</Text>
          <Timeline style={{ marginTop: 12 }}
            items={rolledBackSnapshots.map((snapshot) => ({
              color: 'gray',
              children: (
                <Collapse
                  key={snapshot.id}
                  items={[
                    {
                      key: String(snapshot.id),
                      label: (
                        <Space wrap>
                          <Tag color="default">已回退</Tag>
                          <Text>快照 #{snapshot.id}</Text>
                          <Text type="secondary">
                            递交于 {new Date(snapshot.submitted_at).toLocaleString()}
                          </Text>
                          {snapshot.rolled_back_at && (
                            <Text type="secondary">
                              回退于 {new Date(snapshot.rolled_back_at).toLocaleString()}
                            </Text>
                          )}
                        </Space>
                      ),
                      children: (
                        <div>
                          <Alert
                            type="warning"
                            showIcon
                            style={{ marginBottom: 12 }}
                            message={`回退原因：${snapshot.rollback_reason || '（未填写）'}`}
                            description={
                              <>
                                操作人：{snapshot.rolled_back_by_name || '-'}，
                                回退后状态：{snapshot.restored_status || '-'}
                              </>
                            }
                          />
                          {renderSnapshotBody(snapshot)}
                        </div>
                      ),
                    },
                  ]}
                />
              ),
            }))}
          />
        </div>
      )}

      {/* —— 回退原因输入 —— */}
      <Modal
        title="管理员回退递交"
        open={rollbackTarget !== null}
        onCancel={() => setRollbackTarget(null)}
        onOk={confirmRollback}
        confirmLoading={rollingBack}
        okText="确认回退"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message="回退后申请将解锁，材料与申请批次可重新编辑；旧快照仍会保留可查。"
        />
        <Text strong>回退原因（必填）：</Text>
        <Input.TextArea
          rows={4}
          style={{ marginTop: 8 }}
          value={rollbackReason}
          onChange={(e) => setRollbackReason(e.target.value)}
          placeholder="请说明回退该次递交的原因…"
          maxLength={500}
          showCount
        />
      </Modal>
    </div>
  );
};

export default SubmissionPanel;
