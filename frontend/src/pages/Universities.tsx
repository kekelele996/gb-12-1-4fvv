import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Input,
  Select,
  Row,
  Col,
  Button,
  Modal,
  Descriptions,
  Spin,
  Typography,
  Tag,
  Space,
} from 'antd';
import { SearchOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons';
import { universityAPI } from '../api';
import { University, Program } from '../types';

const { Title, Text } = Typography;
const { Option } = Select;

const Universities: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [universities, setUniversities] = useState<University[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedUniversity, setSelectedUniversity] = useState<University | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [countryFilter, setCountryFilter] = useState<string>('');
  const [minRanking, setMinRanking] = useState<number | undefined>();
  const [maxRanking, setMaxRanking] = useState<number | undefined>();

  useEffect(() => {
    fetchUniversities();
  }, []);

  const fetchUniversities = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (searchText) params.search = searchText;
      if (countryFilter) params.country = countryFilter;
      if (minRanking) params.min_ranking = minRanking;
      if (maxRanking) params.max_ranking = maxRanking;
      
      const response = await universityAPI.getUniversities(params);
      setUniversities(response.data.results || response.data);
    } catch (error) {
      console.error('获取院校列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchUniversities();
  };

  const handleViewDetail = async (university: University) => {
    setSelectedUniversity(university);
    try {
      const response = await universityAPI.getPrograms({ university: university.id });
      setPrograms(response.data.results || response.data);
    } catch (error) {
      console.error('获取专业列表失败:', error);
    }
    setDetailVisible(true);
  };

  const columns = [
    {
      title: '院校名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: University) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      ),
    },
    {
      title: '国家',
      dataIndex: 'country',
      key: 'country',
      width: 120,
    },
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      width: 120,
    },
    {
      title: 'QS排名',
      dataIndex: 'qs_ranking',
      key: 'qs_ranking',
      width: 100,
      render: (val: number | null) => val || '-',
      sorter: (a: University, b: University) => (a.qs_ranking || 9999) - (b.qs_ranking || 9999),
    },
    {
      title: '学费范围',
      key: 'tuition',
      width: 150,
      render: (_: any, record: University) => {
        if (record.tuition_min && record.tuition_max) {
          return `${record.tuition_min} - ${record.tuition_max} ${record.tuition_currency}`;
        }
        return '-';
      },
    },
    {
      title: '专业数量',
      dataIndex: 'programs_count',
      key: 'programs_count',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: University) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  const programColumns = [
    {
      title: '专业名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '学位层次',
      dataIndex: 'degree_level_display',
      key: 'degree_level_display',
      width: 100,
    },
    {
      title: '院系',
      dataIndex: 'department',
      key: 'department',
      width: 150,
    },
    {
      title: '学费',
      dataIndex: 'tuition',
      key: 'tuition',
      width: 120,
      render: (val: number | null) => val || '-',
    },
  ];

  const countries = [...new Set(universities.map((u) => u.country))];

  return (
    <div>
      <Title level={2} className="page-header">
        院校数据库
      </Title>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Input
              placeholder="搜索院校名称"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="选择国家"
              style={{ width: '100%' }}
              allowClear
              value={countryFilter || undefined}
              onChange={setCountryFilter}
            >
              {countries.map((country) => (
                <Option key={country} value={country}>
                  {country}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Input
              placeholder="最低排名"
              type="number"
              value={minRanking}
              onChange={(e) => setMinRanking(Number(e.target.value) || undefined)}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Input
              placeholder="最高排名"
              type="number"
              value={maxRanking}
              onChange={(e) => setMaxRanking(Number(e.target.value) || undefined)}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} block>
              搜索
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={universities}
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
        title={selectedUniversity?.name}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={800}
        footer={null}
      >
        {selectedUniversity && (
          <div>
            <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
              <Descriptions.Item label="国家">{selectedUniversity.country}</Descriptions.Item>
              <Descriptions.Item label="城市">{selectedUniversity.city}</Descriptions.Item>
              <Descriptions.Item label="QS排名">
                {selectedUniversity.qs_ranking || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Times排名">
                {selectedUniversity.times_ranking || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="学费范围">
                {selectedUniversity.tuition_min && selectedUniversity.tuition_max
                  ? `${selectedUniversity.tuition_min} - ${selectedUniversity.tuition_max} ${selectedUniversity.tuition_currency}`
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="专业数量">
                {selectedUniversity.programs_count}
              </Descriptions.Item>
              <Descriptions.Item label="院校简介" span={2}>
                {selectedUniversity.description || '暂无简介'}
              </Descriptions.Item>
            </Descriptions>

            <Title level={4}>开设专业</Title>
            <Table
              columns={programColumns}
              dataSource={programs}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Universities;
