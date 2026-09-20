import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Spin, Typography } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { analyticsAPI } from '../api';
import { DashboardData } from '../types';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getApplicationDashboard();
      setData(response.data);
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const statusColorMap: { [key: string]: string } = {
    planning: '#1890ff',
    preparing: '#faad14',
    submitted: '#52c41a',
    waiting: '#722ed1',
    admitted: '#52c41a',
    rejected: '#ff4d4f',
    waitlisted: '#fa8c16',
    deferred: '#13c2c2',
  };

  const statusNameMap: { [key: string]: string } = {
    planning: '规划中',
    preparing: '准备材料',
    submitted: '已提交',
    waiting: '等待结果',
    admitted: '已录取',
    rejected: '已拒',
    waitlisted: '候补',
    deferred: '延期',
  };

  const getPieChartOption = () => {
    if (!data) return {};
    
    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'horizontal',
        bottom: '0',
      },
      series: [
        {
          name: '申请状态',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold',
            },
          },
          data: data.status_distribution.map((item) => ({
            value: item.count,
            name: statusNameMap[item.status] || item.status,
            itemStyle: {
              color: statusColorMap[item.status] || '#ccc',
            },
          })),
        },
      ],
    };
  };

  const getBarChartOption = () => {
    if (!data) return {};
    
    return {
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: data.countries_distribution.map((item) => item.university__country),
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          data: data.countries_distribution.map((item) => item.count),
          type: 'bar',
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#667eea' },
                { offset: 1, color: '#764ba2' },
              ],
            },
          },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={2} className="page-header">
        数据看板
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总申请数"
              value={data?.total_applications || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已录取"
              value={data?.admitted_count || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="等待结果"
              value={data?.submitted_count || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="录取率"
              value={data?.acceptance_rate || 0}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="申请状态分布">
            <ReactECharts option={getPieChartOption()} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="申请院校国家分布">
            <ReactECharts option={getBarChartOption()} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="申请进度概览">
            <div style={{ maxWidth: 400 }}>
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>材料准备进度</span>
                  <span>75%</span>
                </div>
                <Progress percent={75} strokeColor="#1890ff" />
              </div>
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>文书完成进度</span>
                  <span>60%</span>
                </div>
                <Progress percent={60} strokeColor="#52c41a" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>申请提交进度</span>
                  <span>40%</span>
                </div>
                <Progress percent={40} strokeColor="#722ed1" />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
