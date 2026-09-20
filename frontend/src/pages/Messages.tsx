import React, { useState, useEffect } from 'react';
import {
  List,
  Card,
  Input,
  Button,
  Typography,
  Avatar,
  Badge,
  Empty,
  Spin,
  message,
} from 'antd';
import {
  SendOutlined,
  MessageOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { messageAPI } from '../api';
import { Conversation, Message } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const Messages: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await messageAPI.getConversations();
      setConversations(response.data.results || response.data);
    } catch (error) {
      console.error('获取对话列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    try {
      const response = await messageAPI.getConversation(conversation.id);
      setMessages(response.data.messages || []);
    } catch (error) {
      message.error('获取消息失败');
    }
  };

  const handleSendMessage = async () => {
    if (!selectedConversation || !newMessage.trim()) return;

    try {
      await messageAPI.sendMessage(selectedConversation.id, {
        content: newMessage.trim(),
      });
      setNewMessage('');
      
      const response = await messageAPI.getConversation(selectedConversation.id);
      setMessages(response.data.messages || []);
    } catch (error) {
      message.error('发送消息失败');
    }
  };

  return (
    <div>
      <Title level={2} className="page-header">
        消息中心
      </Title>

      <Card
        style={{
          display: 'grid',
          gridTemplateColumns: '300px 1fr',
          minHeight: '600px',
          padding: 0,
        }}
        styles={{ body: { padding: 0, height: '600px', display: 'grid', gridTemplateColumns: '300px 1fr' } }}
      >
        <div
          style={{
            borderRight: '1px solid #f0f0f0',
            overflowY: 'auto',
            height: '100%',
          }}
        >
          <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
            <Title level={5} style={{ margin: 0 }}>
              <MessageOutlined style={{ marginRight: 8 }} />
              对话列表
            </Title>
          </div>
          
          {loading ? (
            <div style={{ padding: 50, textAlign: 'center' }}>
              <Spin />
            </div>
          ) : conversations.length === 0 ? (
            <div style={{ padding: 50 }}>
              <Empty description="暂无对话" />
            </div>
          ) : (
            <List
              dataSource={conversations}
              renderItem={(conversation) => (
                <List.Item
                  key={conversation.id}
                  style={{
                    cursor: 'pointer',
                    padding: 16,
                    background:
                      selectedConversation?.id === conversation.id
                        ? '#e6f7ff'
                        : 'transparent',
                  }}
                  onClick={() => handleSelectConversation(conversation)}
                >
                  <List.Item.Meta
                    avatar={
                      <Badge count={conversation.unread_count} size="small">
                        <Avatar icon={<UserOutlined />} />
                      </Badge>
                    }
                    title={
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        <Text strong>
                          {conversation.subject || '无主题对话'}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {conversation.last_message_at
                            ? new Date(
                                conversation.last_message_at
                              ).toLocaleDateString()
                            : ''}
                        </Text>
                      </div>
                    }
                    description={
                      conversation.last_message?.content?.substring(
                        0,
                        50
                      ) || '暂无消息'
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div
            style={{
              padding: 16,
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <Title level={5} style={{ margin: 0 }}>
              {selectedConversation?.subject || '请选择一个对话'}
            </Title>
          </div>

          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 16,
              background: '#fafafa',
            }}
          >
            {!selectedConversation ? (
              <div style={{ marginTop: 200, textAlign: 'center' }}>
                <Empty description="请选择一个对话开始聊天" />
              </div>
            ) : messages.length === 0 ? (
              <div style={{ marginTop: 200, textAlign: 'center' }}>
                <Empty description="暂无消息" />
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    marginBottom: 16,
                    display: 'flex',
                    justifyContent:
                      msg.sender_name === 'current_user'
                        ? 'flex-end'
                        : 'flex-start',
                  }}
                >
                  <Card
                    size="small"
                    style={{
                      maxWidth: '70%',
                      background:
                        msg.sender_name === 'current_user'
                          ? '#1890ff'
                          : '#fff',
                      color:
                        msg.sender_name === 'current_user' ? '#fff' : '#000',
                    }}
                  >
                    <div style={{ fontSize: 12, marginBottom: 4, opacity: 0.7 }}>
                      {msg.sender_name}
                    </div>
                    <div>{msg.content}</div>
                    <div
                      style={{
                        fontSize: 11,
                        marginTop: 4,
                        opacity: 0.6,
                        textAlign: 'right',
                      }}
                    >
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </div>
                  </Card>
                </div>
              ))
            )}
          </div>

          {selectedConversation && (
            <div
              style={{
                padding: 16,
                borderTop: '1px solid #f0f0f0',
                display: 'flex',
                gap: 8,
              }}
            >
              <TextArea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                rows={2}
                placeholder="输入消息..."
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                disabled={!newMessage.trim()}
              >
                发送
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Messages;
