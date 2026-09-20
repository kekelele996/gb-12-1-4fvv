import React, { useState, useEffect } from 'react';
import {
  Card,
  Timeline,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Tag,
  Typography,
  Space,
  Checkbox,
  message,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  CheckCircleOutlined,
  UndoOutlined,
  CalendarOutlined,
  FileTextOutlined,
  CheckSquareOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { timelineAPI, applicationAPI } from '../api';
import { TimelineEvent, ApplicationProject } from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const eventTypeIconMap: { [key: string]: React.ReactNode } = {
  exam: <CalendarOutlined style={{ color: '#1890ff' }} />,
  document: <FileTextOutlined style={{ color: '#52c41a' }} />,
  application: <CheckSquareOutlined style={{ color: '#faad14' }} />,
  interview: <ClockCircleOutlined style={{ color: '#722ed1' }} />,
  decision: <TrophyOutlined style={{ color: '#eb2f96' }} />,
  custom: <CalendarOutlined style={{ color: '#13c2c2' }} />,
};

const eventTypeMap: { [key: string]: string } = {
  exam: '语言考试',
  document: '文书截止',
  application: '网申截止',
  interview: '面试',
  decision: '预计出结果',
  custom: '自定义',
};

const TimelinePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [applications, setApplications] = useState<ApplicationProject[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<TimelineEvent[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchEvents();
    fetchApplications();
    fetchUpcomingEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await timelineAPI.getEvents();
      setEvents(response.data.results || response.data);
    } catch (error) {
      console.error('获取时间线事件失败:', error);
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

  const fetchUpcomingEvents = async () => {
    try {
      const response = await timelineAPI.getUpcoming(7);
      setUpcomingEvents(response.data.results || response.data);
    } catch (error) {
      console.error('获取即将到来的事件失败:', error);
    }
  };

  const handleCreate = () => {
    form.resetFields();
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        event_date: values.event_date.toISOString(),
        deadline_date: values.deadline_date?.toISOString(),
      };
      await timelineAPI.createEvent(data);
      message.success('事件创建成功');
      setModalVisible(false);
      fetchEvents();
      fetchUpcomingEvents();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleMarkComplete = async (event: TimelineEvent) => {
    try {
      if (event.is_completed) {
        await timelineAPI.markIncomplete(event.id);
      } else {
        await timelineAPI.markComplete(event.id);
      }
      message.success('状态更新成功');
      fetchEvents();
      fetchUpcomingEvents();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const sortedEvents = [...events].sort((a, b) => 
    new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
  );

  return (
    <div>
      <Title level={2} className="page-header">
        时间线管理
      </Title>

      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建事件
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>
        <Card title="申请时间线">
          {sortedEvents.length === 0 ? (
            <Empty description="暂无时间线事件" />
          ) : (
            <Timeline
              mode="left"
              items={sortedEvents.map((event) => ({
                color: event.is_completed ? 'green' : 'blue',
                dot: eventTypeIconMap[event.event_type],
                children: (
                  <Card
                    size="small"
                    style={{ marginBottom: 8 }}
                    extra={
                      <Tag color={event.is_completed ? 'green' : 'blue'}>
                        {event.is_completed ? '已完成' : '进行中'}
                      </Tag>
                    }
                  >
                    <Card.Meta
                      title={
                        <Space>
                          <span>{event.title}</span>
                          <Tag>{eventTypeMap[event.event_type]}</Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <p>{event.description || '暂无描述'}</p>
                          <p style={{ color: '#666', marginBottom: 8 }}>
                            <CalendarOutlined style={{ marginRight: 4 }} />
                            {new Date(event.event_date).toLocaleString()}
                          </p>
                          {event.deadline_date && (
                            <p style={{ color: '#ff4d4f', marginBottom: 8 }}>
                              截止日期: {new Date(event.deadline_date).toLocaleString()}
                            </p>
                          )}
                          <Button
                            type="link"
                            size="small"
                            icon={event.is_completed ? <UndoOutlined /> : <CheckCircleOutlined />}
                            onClick={() => handleMarkComplete(event)}
                          >
                            {event.is_completed ? '标记为未完成' : '标记为完成'}
                          </Button>
                        </div>
                      }
                    />
                  </Card>
                ),
              }))}
            />
          )}
        </Card>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card title="即将到来 (7天内)">
            {upcomingEvents.length === 0 ? (
              <Empty description="暂无即将到来的事件" />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {upcomingEvents.map((event) => (
                  <Card
                    key={event.id}
                    size="small"
                    hoverable
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {eventTypeIconMap[event.event_type]}
                      <div>
                        <div style={{ fontWeight: 500 }}>{event.title}</div>
                        <div style={{ fontSize: 12, color: '#666' }}>
                          {new Date(event.event_date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      <Modal
        title="新建时间线事件"
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
            name="event_type"
            label="事件类型"
            rules={[{ required: true, message: '请选择事件类型' }]}
          >
            <Select placeholder="请选择">
              <Option value="exam">语言考试</Option>
              <Option value="document">文书截止</Option>
              <Option value="application">网申截止</Option>
              <Option value="interview">面试</Option>
              <Option value="decision">预计出结果</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="title"
            label="事件标题"
            rules={[{ required: true, message: '请输入事件标题' }]}
          >
            <Input placeholder="请输入事件标题" />
          </Form.Item>

          <Form.Item name="description" label="事件描述">
            <TextArea rows={3} placeholder="请输入事件描述（选填）" />
          </Form.Item>

          <Form.Item
            name="event_date"
            label="事件日期"
            rules={[{ required: true, message: '请选择事件日期' }]}
          >
            <DatePicker
              showTime
              style={{ width: '100%' }}
              placeholder="请选择事件日期"
            />
          </Form.Item>

          <Form.Item name="deadline_date" label="截止日期">
            <DatePicker
              showTime
              style={{ width: '100%' }}
              placeholder="请选择截止日期（选填）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TimelinePage;
