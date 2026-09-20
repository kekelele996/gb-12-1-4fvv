import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Avatar,
  Row,
  Col,
  Descriptions,
  Tag,
  message,
} from 'antd';
import {
  UserOutlined,
  SaveOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { authAPI } from '../api';
import { useAuthStore } from '../store/useAuthStore';
import { User } from '../types';

const { Title } = Typography;

const roleMap: { [key: string]: string } = {
  student: '学生',
  consultant: '顾问',
  admin: '管理员',
};

const roleColorMap: { [key: string]: string } = {
  student: 'blue',
  consultant: 'green',
  admin: 'purple',
};

const Profile: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const { user: currentUser } = useAuthStore();
  const [form] = Form.useForm();

  useEffect(() => {
    if (currentUser) {
      setUser(currentUser);
      form.setFieldsValue({
        first_name: currentUser.first_name || '',
        last_name: currentUser.last_name || '',
        phone: currentUser.phone || '',
        bio: currentUser.student_profile?.bio || currentUser.consultant_profile?.bio || '',
      });
    }
  }, [currentUser]);

  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);
      await authAPI.updateCurrentUser(values);
      message.success('个人信息更新成功');
    } catch (error) {
      message.error('更新失败');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div>
      <Title level={2} className="page-header">
        个人中心
      </Title>

      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Avatar
                size={120}
                icon={<UserOutlined />}
                style={{ marginBottom: 16 }}
              />
              <Title level={4} style={{ marginBottom: 8 }}>
                {user.get_full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username}
              </Title>
              <Tag color={roleColorMap[user.role]}>
                {roleMap[user.role]}
              </Tag>
            </div>

            <div style={{ marginTop: 24 }}>
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="用户名">
                  {user.username}
                </Descriptions.Item>
                <Descriptions.Item label="邮箱">
                  {user.email || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="手机">
                  {user.phone || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="注册时间">
                  {user.date_joined
                    ? new Date(user.date_joined).toLocaleDateString()
                    : '-'}
                </Descriptions.Item>
              </Descriptions>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={16}>
          <Card
            title={
              <span>
                <EditOutlined style={{ marginRight: 8 }} />
                编辑个人信息
              </span>
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              style={{ maxWidth: 600 }}
            >
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item label="名" name="first_name">
                    <Input placeholder="请输入名" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item label="姓" name="last_name">
                    <Input placeholder="请输入姓" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="手机号码" name="phone">
                <Input placeholder="请输入手机号码" />
              </Form.Item>

              {user.role === 'student' && (
                <>
                  <Form.Item label="目标国家" name="target_country">
                    <Input placeholder="请输入目标国家（选填）" />
                  </Form.Item>
                  <Form.Item label="目标学位" name="target_degree">
                    <Input placeholder="请输入目标学位（选填）" />
                  </Form.Item>
                </>
              )}

              {user.role === 'consultant' && (
                <>
                  <Form.Item label="专长领域" name="specialty">
                    <Input placeholder="请输入专长领域（选填）" />
                  </Form.Item>
                </>
              )}

              <Form.Item label="个人简介" name="bio">
                <Input.TextArea
                  rows={4}
                  placeholder="请输入个人简介（选填）"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<SaveOutlined />}
                >
                  保存修改
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Profile;
