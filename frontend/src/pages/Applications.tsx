import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Modal,
  Form,
  Select,
  Input,
  DatePicker,
  Progress,
  Tag,
  Space,
  Typography,
  message,
  Descriptions,
} from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { applicationAPI, universityAPI } from '../api';
import { ApplicationProject, University, Program } from '../types';

const { Title } = Typography;
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
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState<ApplicationProject[]>([]);
  const [universities, setUniversities] = useState<University[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<ApplicationProject | null>(null);
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

  const handleUniversityChange = async (universityId: number) => {
    try {
      const response = await universityAPI.getPrograms({ university: universityId });
      setPrograms(response.data.results || response.data);
      form.setFieldValue('program', undefined);
    } catch (error) {
      console.error('获取专业列表失败:', error);
    }
  };

  const handleCreate = () => {
    form.resetFields();
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
      setDetailVisible(true);
    } catch (error) {
      message.error('获取详情失败');
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
      width: 150,
      render: (status: string, record: ApplicationProject) => (
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
      width: 180,
      render: (_: any, record: ApplicationProject) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
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
            <Select placeholder="请选择专业">
              {programs.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.name}
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
        title="申请项目详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={700}
        footer={null}
      >
        {selectedApplication && (
          <div>
            <Descriptions bordered column={2}>
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
              </Descriptions.Item>
              <Descriptions.Item label="材料进度">
                <Progress percent={selectedApplication.materials_progress} size="small" />
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
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Applications;
