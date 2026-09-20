import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Modal,
  Form,
  Select,
  Input,
  Tag,
  Space,
  Typography,
  message,
  Tabs,
  List,
  Avatar,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  HistoryOutlined,
  MessageOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { documentAPI, applicationAPI } from '../api';
import { Document, DocumentVersion, DocumentComment, ApplicationProject } from '../types';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const documentTypeMap: { [key: string]: string } = {
  ps: '个人陈述 (PS)',
  rl: '推荐信 (RL)',
  cv: '简历 (CV)',
  essay: 'Essay',
  other: '其他',
};

const Documents: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [applications, setApplications] = useState<ApplicationProject[]>([]);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [comments, setComments] = useState<DocumentComment[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editorVisible, setEditorVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [activeTab, setActiveTab] = useState('editor');
  const [editorContent, setEditorContent] = useState('');
  const [changeNote, setChangeNote] = useState('');
  const [newComment, setNewComment] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    fetchDocuments();
    fetchApplications();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await documentAPI.getDocuments();
      setDocuments(response.data.results || response.data);
    } catch (error) {
      console.error('获取文书列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await applicationAPI.getApplications();
      setApplications(response.data.results || response.data);
    } catch (error) {
      console.error('获取申请列表失败:', error);
    }
  };

  const handleCreate = () => {
    form.resetFields();
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      await documentAPI.createDocument(values);
      message.success('文书创建成功');
      setModalVisible(false);
      fetchDocuments();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleEdit = async (document: Document) => {
    setSelectedDocument(document);
    
    if (document.current_version) {
      setEditorContent(document.current_version.content);
    }
    
    try {
      const [versionsRes, commentsRes] = await Promise.all([
        documentAPI.getVersions({ document_id: document.id }),
        documentAPI.getComments({ document_id: document.id }),
      ]);
      setVersions(versionsRes.data.results || versionsRes.data);
      setComments(commentsRes.data.results || commentsRes.data);
    } catch (error) {
      console.error('获取文书详情失败:', error);
    }
    
    setEditorVisible(true);
  };

  const handleSaveVersion = async () => {
    if (!selectedDocument) return;
    
    try {
      await documentAPI.createVersion({
        document: selectedDocument.id,
        content: editorContent,
        change_note: changeNote,
      });
      message.success('版本保存成功');
      setChangeNote('');
      fetchDocuments();
      
      const response = await documentAPI.getVersions({ document_id: selectedDocument.id });
      setVersions(response.data.results || response.data);
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleAddComment = async () => {
    if (!selectedDocument || !newComment.trim()) return;
    
    try {
      await documentAPI.createComment({
        document: selectedDocument.id,
        content: newComment.trim(),
      });
      message.success('评论添加成功');
      setNewComment('');
      
      const response = await documentAPI.getComments({ document_id: selectedDocument.id });
      setComments(response.data.results || response.data);
    } catch (error) {
      message.error('添加评论失败');
    }
  };

  const handleResolveComment = async (commentId: number) => {
    try {
      await documentAPI.resolveComment(commentId);
      message.success('已标记为已解决');
      
      if (selectedDocument) {
        const response = await documentAPI.getComments({ document_id: selectedDocument.id });
        setComments(response.data.results || response.data);
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    {
      title: '文书类型',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 150,
      render: (type: string) => (
        <Tag color="blue">{documentTypeMap[type]}</Tag>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '所属申请',
      key: 'application',
      width: 200,
      render: (_: any, record: Document) => {
        const app = applications.find((a) => a.id === record.application);
        return app ? `${app.university_name} - ${app.program_name}` : '-';
      },
    },
    {
      title: '版本数',
      dataIndex: 'versions_count',
      key: 'versions_count',
      width: 100,
    },
    {
      title: '待解决评论',
      dataIndex: 'comments_count',
      key: 'comments_count',
      width: 120,
      render: (count: number) => (
        count > 0 ? <Tag color="red">{count} 条</Tag> : <Tag color="green">无</Tag>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Document) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: '确定要删除这个文书吗？',
                onOk: async () => {
                  try {
                    await documentAPI.deleteDocument(record.id);
                    message.success('删除成功');
                    fetchDocuments();
                  } catch (error) {
                    message.error('删除失败');
                  }
                },
              });
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const editorTabs = [
    {
      key: 'editor',
      label: '编辑器',
      icon: <FileTextOutlined />,
      children: (
        <div>
          <TextArea
            value={editorContent}
            onChange={(e) => setEditorContent(e.target.value)}
            rows={15}
            placeholder="在此输入文书内容..."
            className="document-editor"
            style={{ marginBottom: 16 }}
          />
          <Input
            placeholder="版本修改说明（选填）"
            value={changeNote}
            onChange={(e) => setChangeNote(e.target.value)}
            style={{ marginBottom: 16 }}
          />
          <Button type="primary" onClick={handleSaveVersion}>
            保存版本
          </Button>
        </div>
      ),
    },
    {
      key: 'history',
      label: `版本历史 (${versions.length})`,
      icon: <HistoryOutlined />,
      children: (
        <List
          itemLayout="vertical"
          dataSource={versions}
          renderItem={(version) => (
            <List.Item key={version.id}>
              <List.Item.Meta
                title={`版本 ${version.version_number}`}
                description={`
                  字数: ${version.word_count} | 
                  修改人: ${version.created_by_name || '未知'} | 
                  ${new Date(version.created_at).toLocaleString()}
                `}
              />
              {version.change_note && (
                <p style={{ color: '#666', fontStyle: 'italic' }}>
                  修改说明: {version.change_note}
                </p>
              )}
            </List.Item>
          )}
        />
      ),
    },
    {
      key: 'comments',
      label: `评论 (${comments.length})`,
      icon: <MessageOutlined />,
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <TextArea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
              placeholder="添加评论或批注..."
            />
            <Button
              type="primary"
              onClick={handleAddComment}
              style={{ marginTop: 8 }}
              disabled={!newComment.trim()}
            >
              提交评论
            </Button>
          </div>
          
          <List
            dataSource={comments}
            renderItem={(comment) => (
              <List.Item
                key={comment.id}
                actions={[
                  !comment.is_resolved && (
                    <Tooltip title="标记为已解决">
                      <Button
                        type="link"
                        icon={<CheckCircleOutlined />}
                        onClick={() => handleResolveComment(comment.id)}
                      >
                        解决
                      </Button>
                    </Tooltip>
                  ),
                ]}
              >
                <List.Item.Meta
                  avatar={<Avatar>{comment.author_name?.[0]}</Avatar>}
                  title={comment.author_name || '匿名用户'}
                  description={
                    <Space direction="vertical" size={4}>
                      <span>{comment.content}</span>
                      <span style={{ color: '#999', fontSize: 12 }}>
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={2} className="page-header">
        文书管理
      </Title>

      <Card>
        <div style={{ marginBottom: 16, textAlign: 'right' }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建文书
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={documents}
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
        title="新建文书"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="application"
            label="所属申请项目"
            rules={[{ required: true, message: '请选择申请项目' }]}
          >
            <Select placeholder="请选择">
              {applications.map((app) => (
                <Option key={app.id} value={app.id}>
                  {app.university_name} - {app.program_name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="document_type"
            label="文书类型"
            rules={[{ required: true, message: '请选择文书类型' }]}
          >
            <Select placeholder="请选择">
              <Option value="ps">个人陈述 (PS)</Option>
              <Option value="rl">推荐信 (RL)</Option>
              <Option value="cv">简历 (CV)</Option>
              <Option value="essay">Essay</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入文书标题" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="文书描述（选填）" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`编辑: ${selectedDocument?.title}`}
        open={editorVisible}
        onCancel={() => setEditorVisible(false)}
        width={900}
        footer={null}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={editorTabs}
        />
      </Modal>
    </div>
  );
};

export default Documents;
